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


# =====================================================================
# 4. Create Folium map with 3M polygon
# =====================================================================
bounds = gdf_3m_poly.total_bounds  # minx, miny, maxx, maxy
center_lat = (bounds[1] + bounds[3]) / 2
center_lon = (bounds[0] + bounds[2]) / 2

m = folium.Map(location=[center_lat, center_lon], zoom_start=6)

folium.GeoJson(
    gdf_3m_poly,
    name="3M Polygon"
).add_to(m)

m.save("3M_polygon.html")
print("Saved map as 3M_polygon.html")


# =====================================================================
# 5. OPTIONAL — AIS point-in-polygon check
# =====================================================================
"""
# Example AIS dataframe
df_ais = pd.DataFrame({
    "latitude": [55.0, 48.2],
    "longitude": [-50.0, -52.3]
})

# Convert AIS points to GeoDataFrame
gdf_ais = gpd.GeoDataFrame(
    df_ais,
    geometry=gpd.points_from_xy(df_ais.longitude, df_ais.latitude),
    crs="EPSG:4326"
)

# Prepare polygon for fast repeated checks
prepared_poly = prep(polygon_3m)

# Check if each AIS point is inside 3M
gdf_ais["inside_3M"] = gdf_ais.geometry.apply(lambda p: prepared_poly.contains(p))

print(gdf_ais)
"""

print("Done.")
