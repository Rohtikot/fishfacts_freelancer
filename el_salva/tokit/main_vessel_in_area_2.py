from datetime import datetime
from vessel_in_area import download_vessels_in_area
from db.location_dao import get_vessel_locations_to_data_frame
from db.vessel_dao import get_vessels_all_to_dataframe
from shapely.geometry import Polygon
from db import connection_settings
from db.model import VesselType
import json
import pandas as pd
import warnings

import pandas as pd
import geopandas as gpd
import folium

from shapely.ops import unary_union, polygonize
from shapely.prepared import prep


# =====================================================================
# 1. Load the shapefile
# =====================================================================
shp_path = r"C:\Users\tokit\Downloads\Divisions\NAFO_Divisions_SHP"

gdf = gpd.read_file(shp_path)
print("Original CRS:", gdf.crs)

# Convert to WGS84 for Folium
gdf = gdf.to_crs(epsg=4326)
print("Converted CRS:", gdf.crs)

print("Labels found:", gdf["Label"].unique())


# =====================================================================
# 2. Filter to division 3M (still LINESTRING)
# =====================================================================
gdf_3m = gdf[gdf["Label"] == "3M"]

if gdf_3m.empty:
    raise ValueError("No geometry found with Label='3M'")

print("Original 3M geometry type:", gdf_3m.geom_type.value_counts())


# =====================================================================
# 3. Polygonize: Convert 3M boundary LINESTRING → POLYGON
# =====================================================================
print("Merging lines...")
merged_lines = unary_union(gdf_3m.geometry)

print("Polygonizing...")
polygons = list(polygonize(merged_lines))

if len(polygons) == 0:
    raise ValueError("Polygonization failed — boundary not closed.")

print(f"Generated {len(polygons)} polygon(s).")

# Union them into one polygon if needed
polygon_3m = unary_union(polygons)

# Final GeoDataFrame containing a single polygon
gdf_3m_poly = gpd.GeoDataFrame(geometry=[polygon_3m], crs=gdf.crs)

print("Final 3M geometry type:", gdf_3m_poly.geom_type)


pd.set_option('display.width', None)

warnings.filterwarnings("ignore", "Your application has authenticated using end user credentials")
warnings.filterwarnings("ignore", "Properties that return a naïve datetime object have been deprecated.")

connection_settings.settings = json.loads(open("../settings.json").read())


vessels = get_vessels_all_to_dataframe()

vessels = vessels[
    (vessels['vessel_type_id'].isin([VesselType.FREEZING_TRAWLER, VesselType.TRAWLER, VesselType.LONG_LINER]))
]
vessels.sort_values(by='length_overall')
print(vessels.head(5))
print(vessels.tail(5))
print(vessels.shape)
grouped = vessels.groupby('vessel_type_id').size()
print(grouped)
grouped = vessels.groupby('vessel_type_id')
start1, end1 = datetime(2023, 3, 1), datetime(2023, 9, 1)
start2, end2 = datetime(2024, 3, 1), datetime(2024, 9, 1)
start3, end3 = datetime(2025, 3, 1), datetime(2025, 9, 1)
for name, group in grouped:
    #download_vessels_in_area(group, fr'{name}_vessels_in_area_2023', polygon_3m, start1, end1)
    download_vessels_in_area(group, fr'{name}_vessels_in_area_2024', polygon_3m, start2, end2)
    #download_vessels_in_area(group, fr'{name}_vessels_in_area_2025', polygon_3m, start3, end3)
