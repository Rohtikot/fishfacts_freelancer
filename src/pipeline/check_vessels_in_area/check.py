import os
from datetime import datetime

import pandas as pd
import geopandas as gpd
from tqdm import tqdm

from src.db.model import VesselType
from src.db.vessels import get_vessels_all_to_dataframe
from src.db import connection_settings
from src.data.zones import load_polygons


# ============================================================
# CONFIG
# ============================================================
VESSEL_TYPE_PRIORITY = [
    VesselType.PELAGIC,
    VesselType.FREEZING_TRAWLER,
    VesselType.TRAWLER,
    VesselType.LONG_LINER,
    VesselType.CRABS_AND_SHELLFISH
]

STATUS_FILE = '../../../Projects/elsalvador26/vessel_scan_status.csv'

OPENING_AREA_PATH = '../../../data/zones/assignment/meld.st.25_opningsomrade'
EEZ_PATH = '../../../data/zones/eez/World_EEZ_v12_20231025'
NEAFC_PATH = '../../../data/zones/eez/NEAFC_VMEMEASURE_OTHER-NEAFC'

START_YEAR = 2018
END_YEAR = 2025
SAVE_EVERY = 10


# ============================================================
# LOAD POLYGONS
# ============================================================
def read_areas():
    opningsomrade = load_polygons(OPENING_AREA_PATH)
    opningsomrade['Date_updat'] = opningsomrade['Date_updat'].astype(str)

    eez = load_polygons(EEZ_PATH, layer='eez_v12')
    eez = eez[
        (eez['SOVEREIGN1'] == 'Norway') &
        (eez['MRGID'].isin([33181, 5686, 8437]))
    ]

    neafc = load_polygons(NEAFC_PATH)
    neafc = neafc.loc[0:0]

    combined = gpd.GeoDataFrame(
        pd.concat([opningsomrade, eez, neafc], ignore_index=True),
        crs=opningsomrade.crs
    )

    merged = combined.geometry.union_all()

    merged_gdf = gpd.GeoDataFrame(
        geometry=[merged],
        crs=combined.crs
    )

    bbox = merged_gdf.total_bounds.tolist()

    return merged_gdf, bbox


# ============================================================
# FAST DATABASE CHECK (BBOX ONLY)
# ============================================================
def vessel_has_bbox_hit(vessel_id: int, start: datetime, end: datetime, bbox: list[float]) -> bool:
    lon_min, lat_min, lon_max, lat_max = bbox

    sql = (
        "SELECT 1 "
        "FROM location "
        f"WHERE vessel_id = {vessel_id} "
        f"  AND timestamp > '{start:%Y-%m-%d %H:%M:%S}' "
        f"  AND timestamp < '{end:%Y-%m-%d %H:%M:%S}' "
        f"  AND latitude BETWEEN {lat_min} AND {lat_max} "
        f"  AND longitude BETWEEN {lon_min} AND {lon_max} "
        "LIMIT 1"
    )

    with connection_settings.connect_to_database().connect() as connection:
        df = pd.read_sql(sql, connection)

    return not df.empty


# ============================================================
# STATUS FILE
# ============================================================
def load_or_create_vessel_status():
    if os.path.exists(STATUS_FILE):
        vessels = pd.read_csv(STATUS_FILE)
        vessels['checked'] = vessels['checked'].astype(bool)
        vessels['in_zone'] = vessels['in_zone'].astype(bool)
        return vessels

    vessels = get_vessels_all_to_dataframe()

    vessels = vessels[
        vessels['vessel_type_id'].isin([
            VesselType.PELAGIC,
            VesselType.FREEZING_TRAWLER,
            VesselType.TRAWLER,
            VesselType.LONG_LINER,
            VesselType.CRABS_AND_SHELLFISH
        ])
    ].copy()

    vessels['checked'] = False
    vessels['in_zone'] = False

    vessels.to_csv(STATUS_FILE, index=False)

    return vessels

def save_progress(vessels: pd.DataFrame):
    vessels.to_csv(STATUS_FILE, index=False)


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    polygons, bbox = read_areas()
    vessels = load_or_create_vessel_status()

    # sort vessels by priority WITHOUT losing progress
    vessels['vessel_type_id'] = pd.Categorical(
        vessels['vessel_type_id'],
        categories=VESSEL_TYPE_PRIORITY,
        ordered=True
    )

    vessels = vessels.sort_values(
        ['vessel_type_id', 'id']
    ).reset_index(drop=True)

    # checked/in_zone may load as strings depending on CSV state
    vessels['checked'] = vessels['checked'].astype(bool)
    vessels['in_zone'] = vessels['in_zone'].astype(bool)

    unchecked = vessels.loc[~vessels['checked']].copy()

    total_count = len(vessels)
    checked_count = int(vessels['checked'].sum())

    save_counter = 0

    progress = tqdm(
        unchecked.iterrows(),
        total=len(unchecked),
        desc=f'Vessels ({checked_count}/{total_count} done)',
        unit='vessel'
    )

    for idx, vessel in progress:
        vessel_id = int(vessel['id'])
        vessel_name = str(vessel['name'])

        progress.set_postfix({
            'id': vessel_id,
            'name': vessel_name[:15]
        })

        found = False

        try:
            for year in range(START_YEAR, END_YEAR + 1):
                start = datetime(year, 1, 1)
                end = datetime(year + 1, 1, 1)

                if vessel_has_bbox_hit(
                    vessel_id=vessel_id,
                    start=start,
                    end=end,
                    bbox=bbox
                ):
                    found = True
                    break

            vessels.loc[idx, 'checked'] = True
            vessels.loc[idx, 'in_zone'] = found

            save_counter += 1

            if save_counter >= SAVE_EVERY:
                save_progress(vessels)
                save_counter = 0

        except Exception as e:
            print(f'\nFailed vessel {vessel_id}: {e}')
            save_progress(vessels)
            continue

    save_progress(vessels)

    print('Finished.')
