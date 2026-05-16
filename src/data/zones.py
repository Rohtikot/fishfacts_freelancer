import geopandas as gpd
import folium
import pandas as pd
from src.db.ais import get_ais_candidates, get_vessel_locations_to_data_frame, explain_vessel_query


def load_polygons(path, layer: str = None):
    gdf = gpd.read_file(path, layer=layer)
    return gdf.to_crs('EPSG:4326')


import geopandas as gpd

def detect_vessels_in_polygon(df: pd.DataFrame, polygons: gpd.GeoDataFrame) -> set:
    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326"
    )

    hits = gpd.sjoin(points, polygons, predicate="within", how="inner")

    return set(hits["vessel_id"].unique())


if __name__ == '__main__':
    import pandas as pd
    from datetime import datetime
    from time import time

    pd.set_option('display.width', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', None)
    # pd.set_option('display.max_rows', None)

    path = r'../../data/zones/assignment/meld.st.25_opningsomrade'
    eez_path = r'../../data/zones/eez/World_EEZ_v12_20231025'
    neafc_path = r'../../data/zones/eez/NEAFC_VMEMEASURE_OTHER-NEAFC'

    opningsomrade = load_polygons(path)
    # Fix timestamp column
    opningsomrade['Date_updat'] = opningsomrade['Date_updat'].astype(str)

    eez = load_polygons(eez_path, layer='eez_v12')
    neafc = load_polygons(neafc_path)

    eez = eez[
        (eez['SOVEREIGN1'] == 'Norway')
        & (eez['MRGID'].isin([33181, 5686, 8437,]))
    ]

    neafc = neafc.loc[0:0]

    combined = gpd.GeoDataFrame(
        pd.concat([opningsomrade, eez, neafc], ignore_index=True),
        crs=opningsomrade.crs,
    )

    merged = combined.geometry.union_all()
    merged_df = gpd.GeoDataFrame(
        geometry=[merged],
        crs=combined.crs
    )
    print(combined)
    bbox = merged_df.total_bounds.tolist()
    print('Now querying database')
