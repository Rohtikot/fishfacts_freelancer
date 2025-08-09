import pandas as pd
import glob
import geopandas as gpd
import pyarrow
from shapely.geometry import Polygon


pd.set_option('display.width', None)

files = glob.glob(r"C:\Users\tokit\PycharmProjects\fishfacts_toolbox\zones\close_land_geofencing\*.csv")

dataframes = []

for file in files:
    df = pd.read_csv(file)
    name = file.split('\\')[-1].replace('.csv', '')
    df['close_land'] = name
    points = [(lat, lon) for lat, lon in zip(df['longitude'], df['latitude'])]
    polygon = Polygon(points)

    dataframes.append({'zone': name, 'geometry': polygon})

    # dfs.append(df)
gdf = gpd.GeoDataFrame(dataframes, geometry='geometry')
gdf['zone_type'] = 'close_land'
gdf.set_crs(epsg=4326, inplace=True)
print(gdf)
print(gdf.dtypes)

gdf.to_parquet("close_land.parquet", index=False)
# print(combined_df)
