from resample.resample_fix_time_gaps import resample_with_interpolation
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import unary_union, polygonize


"""
This script will resampled the raw AIS data (with a limit of 4 hours), interpolate the speed between points, 
and re-zone the ais data in case information was lost in the interpolation.
"""

pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)

# === READ THE POLYGON 3M ===
shp_path = r"..\area\Divisions\NAFO_Divisions_SHP"
gdf = gpd.read_file(shp_path)
print("Original CRS:", gdf.crs)
# Convert to WGS84 for Folium
gdf = gdf.to_crs(epsg=4326)
print("Converted CRS:", gdf.crs)
gdf_3m = gdf[gdf["Label"] == "3M"]
merged_lines = unary_union(gdf_3m.geometry)
polygons = list(polygonize(merged_lines))
polygon_3m = unary_union(polygons)


def resample_per_vessel(group: pd.DataFrame) -> pd.DataFrame:
    resampled = resample_with_interpolation(group)

    # Columns already produced by the resampler
    resampled_cols = set(resampled.columns)

    # Columns to reattach (everything else)
    static_cols = [c for c in group.columns if c not in resampled_cols]

    # Reattach static columns
    for col in static_cols:
        resampled[col] = group[col].iloc[0]

    return resampled


df = pd.read_parquet(r'ais_data_for_all_vessels.parquet')
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Resample and interpolate
resampled_df = (
    df.sort_values(['vessel_id', 'timestamp'])
      .groupby('vessel_id', group_keys=False)
      .apply(resample_per_vessel)
      .reset_index(drop=True)
)

# === Re-check points inside/outside polygon on resampled dataframe ===
# Create geometry from lon/lat
gdf_points = gpd.GeoDataFrame(
    resampled_df,
    geometry=gpd.points_from_xy(resampled_df["longitude"], resampled_df["latitude"]),
    crs="EPSG:4326"
)

gdf_points["is_inside"] = gdf_points.geometry.within(polygon_3m)
gdf_points.drop(columns=['geometry'], inplace=True)
print(gdf_points)
gdf_points.to_parquet(r'ais_data_for_all_vessels_resampled.parquet', index=False)
