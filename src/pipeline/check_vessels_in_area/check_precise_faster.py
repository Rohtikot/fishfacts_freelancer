import os.path
from time import time
from tqdm import tqdm
from datetime import datetime
import pandas as pd
import numpy as np
import geopandas as gpd
import folium

from src.db.model import VesselType
from src.data.zones import load_polygons
from src.db.ais import get_vessel_locations_to_data_frame
from src.db import connection_settings

from shapely.prepared import prep
from pathlib import Path

pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)

# ==========================================================================
# CONFIG
# ==========================================================================
ROOT = Path(__file__).parents[3]
PROJECT_PATH = ROOT / 'Projects' / 'elsalvador26'
STATUS_FILE = PROJECT_PATH / 'vessel_scan_status.csv'
REGISTER_FILE = PROJECT_PATH / 'vessel_polygon_status.csv'
OUTPUT_DIR = PROJECT_PATH / 'vessel_tracks'

START_YEAR = 2018
END_YEAR = 2025
SAVE_EVERY = 10

VESSEL_TYPE_PRIORITY = [
    VesselType.PELAGIC,
    VesselType.FREEZING_TRAWLER,
    VesselType.TRAWLER,
    VesselType.LONG_LINER,
    VesselType.CRABS_AND_SHELLFISH
]


# ==========================================================================
# HELPER: FAST YEAR CHECK (NEW)
# ==========================================================================
def year_has_any_bbox_points(vessel_id, start, end, bbox):
    """
    Very fast check:
    only checks if ANY point exists in bbox for that year.
    Does NOT fetch full dataset.
    """
    lon_min, lat_min, lon_max, lat_max = bbox

    sql = f"""
        SELECT 1
        FROM location
        WHERE vessel_id = {vessel_id}
          AND timestamp > '{start:%Y-%m-%d %H:%M:%S}'
          AND timestamp < '{end:%Y-%m-%d %H:%M:%S}'
          AND latitude BETWEEN {lat_min} AND {lat_max}
          AND longitude BETWEEN {lon_min} AND {lon_max}
        LIMIT 1
    """

    with connection_settings.connect_to_database().connect() as conn:
        df = pd.read_sql(sql, conn)

    return not df.empty


# ==========================================================================
# POLYGONS
# ==========================================================================
def read_polygons():
    opnings = load_polygons(
        ROOT / 'data' / 'zones' / 'assignment' / 'meld.st.25_opningsomrade'
    )
    opnings['Date_updat'] = opnings['Date_updat'].astype(str)

    eez = load_polygons(
        path=ROOT / 'data' / 'zones' / 'eez' / 'World_EEZ_v12_20231025',
        layer='eez_v12'
    )
    eez = eez[
        (eez['SOVEREIGN1'] == 'Norway')
        & (eez['MRGID'].isin([33181, 5686, 8437]))
    ]

    neafc = load_polygons(
        path=ROOT / 'data' / 'zones' / 'eez' / 'NEAFC_VMEMEASURE_OTHER-NEAFC'
    )
    neafc = neafc.loc[0:0]

    combined = gpd.GeoDataFrame(
        pd.concat([eez, neafc, opnings], ignore_index=True),
        crs=eez.crs,
    )

    merged = combined.geometry.unary_union

    merged_gdf = gpd.GeoDataFrame(
        geometry=[merged],
        crs=combined.crs
    )

    bbox = merged_gdf.total_bounds.tolist()

    return merged_gdf, bbox


# ==========================================================================
# INIT
# ==========================================================================
polygons, bbox = read_polygons()
polygon = polygons.geometry.iloc[0]
prepared_polygon = prep(polygon)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================================================
# LOAD VESSELS
# ==========================================================================
bbox_hits = pd.read_csv(STATUS_FILE)
bbox_hits['in_zone'] = bbox_hits['in_zone'].astype(bool)

vessels = bbox_hits[bbox_hits['in_zone']].copy()
vessels = vessels[['id', 'name', 'vessel_type_id']].copy()

vessels['vessel_type_id'] = pd.Categorical(
    vessels['vessel_type_id'],
    categories=VESSEL_TYPE_PRIORITY,
    ordered=True
)

vessels = vessels.sort_values(
    ['vessel_type_id', 'id']
).reset_index(drop=True)


# ==========================================================================
# REGISTER FILE (RESUME SUPPORT)
# ==========================================================================
if os.path.exists(REGISTER_FILE):
    register = pd.read_csv(REGISTER_FILE)
    register['processed'] = register['processed'].astype(bool)
else:
    register = vessels.copy()
    register['processed'] = False
    register.to_csv(REGISTER_FILE, index=False)


todo = register[~register['processed']].copy()
print(f'Remaining vessels: {len(todo)}')

if __name__ == '__main__':
    # ==========================================================================
    # MAIN LOOP
    # ==========================================================================
    save_counter = 0

    progress = tqdm(
        todo.iterrows(),
        total=len(todo),
        desc='Checking polygons',
        unit='vessel'
    )

    for idx, vessel in progress:
        vessel_id = int(vessel['id'])

        progress.set_postfix({'id': vessel_id})

        yearly_data = []

        try:
            for year in range(START_YEAR, END_YEAR + 1):

                start = datetime(year, 1, 1)
                end = datetime(year + 1, 1, 1)

                # ==========================================================
                # NEW: FAST PRE-CHECK (THIS IS THE BIG SPEEDUP)
                # ==========================================================
                precheck_start = time()
                precheck = year_has_any_bbox_points(vessel_id, start, end, bbox)
                if not precheck:
                    continue
                precheck_end = time()
                print(f'Precheck for vessel {vessel['name']}, year {year} took {precheck_end-precheck_start:.02f}.')

                # ==========================================================
                # FULL DOWNLOAD ONLY IF NECESSARY
                # ==========================================================
                timer_start = time()
                df = get_vessel_locations_to_data_frame(
                    vessel_id=vessel_id,
                    start=start,
                    end=end,
                )
                timer_end = time()
                print(f'Query for vessel {vessel['name']}, year {year} took {timer_end-timer_start:.02f}. Rows: {df.shape[0]}')
                print('\n')
                if df.empty:
                    continue

                geometry = gpd.points_from_xy(
                    df['longitude'],
                    df['latitude'],
                )

                has_hit = prepared_polygon.contains(geometry).any()

                if has_hit:
                    df['year'] = year
                    yearly_data.append(df)

            # Save vessel parquet
            if yearly_data:
                result = pd.concat(yearly_data, ignore_index=True)
                output_file = OUTPUT_DIR / f'{vessel_id}.parquet'
                result.to_parquet(output_file, index=False)

            register.loc[idx, 'processed'] = True

            save_counter += 1

            if save_counter >= SAVE_EVERY:
                register.to_csv(REGISTER_FILE, index=False)
                save_counter = 0

        except Exception as e:
            print(f"\nFailed vessel {vessel_id}: {e}")
            register.to_csv(REGISTER_FILE, index=False)
            continue


    # ==========================================================================
    # FINAL SAVE
    # ==========================================================================
    register.to_csv(REGISTER_FILE, index=False)

    print('Finished')
