import pandas as pd
import folium
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from shapely.geometry import MultiPoint
import geopandas as gpd
from catch.nor_catch_functions import read_dca, file_age, download_ers
from folium import features


if file_age('ers', 12):
    download_ers(2020)
    download_ers(2021)
    download_ers(2022)
    download_ers(2023)
    download_ers(2024)
    download_ers(2025)

pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)

dfs = []
for i in range(2020, 2026):
    print(i)
    df = read_dca(i)
    df = df[(df['Art - FDIR'] == 'Snøkrabbe') & (df['Fartøynasjonalitet (kode)'] == 'NOR')]
    dfs.append(df)

dfs = pd.concat(dfs)
# dfs.to_csv('data/crab_fisheries_2020-2025.csv', index=False)

# # Find which vessels are included in snow crab fisheries
# nor_vessels = df[['Radiokallesignal (ERS)', 'Fartøynavn (ERS)', 'Største lengde']].drop_duplicates()
# nor_vessels.sort_values(by='Største lengde', ascending=False, inplace=True)
#
# # Isolate positions
# positions = df[['Startposisjon bredde', 'Startposisjon lengde']]
# print(positions)
#
#
# def make_geofences(df, eps=0.01, min_samples=5, crs="EPSG:4326"):
#     coords = df[["Startposisjon bredde", "Startposisjon lengde"]].to_numpy()
#     db = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
#     df = df.copy()
#     df["cluster"] = db.labels_
#
#     geofences = []
#     for cluster_id in df["cluster"].unique():
#         if cluster_id == -1:  # -1 = noise
#             continue
#         points = df.loc[df["cluster"] == cluster_id,
#                         ["Startposisjon lengde", "Startposisjon bredde"]].to_numpy()
#         multipoint = MultiPoint(points)
#         polygon = multipoint.convex_hull
#         geofences.append({"cluster": cluster_id, "geometry": polygon})
#
#     gdf_geofences = gpd.GeoDataFrame(geofences, crs=crs)
#     return gdf_geofences, df
#
#
# def plot_geofences(df, geofences):
#     # Center map at mean coordinates
#     center_lat = df["Startposisjon bredde"].mean()
#     center_lon = df["Startposisjon lengde"].mean()
#
#     m = folium.Map(location=[center_lat, center_lon],
#                    tiles="CartoDB dark_matter", zoom_start=8)
#
#     # Add cluster points
#     for _, row in df.iterrows():
#         if row["cluster"] != -1:  # skip noise
#             folium.CircleMarker(
#                 location=[row["Startposisjon bredde"], row["Startposisjon lengde"]],
#                 radius=4,
#                 color="yellow",
#                 fill=True,
#                 fill_opacity=0.7
#             ).add_to(m)
#
#     # Add geofence polygons
#     for _, row in geofences.iterrows():
#         sim_geo = gpd.GeoSeries(row["geometry"]).simplify(0.001)
#         geo_j = sim_geo.__geo_interface__
#         folium.GeoJson(
#             geo_j,
#             name=f"Cluster {row['cluster']}",
#             style_function=lambda x: {
#                 "fillColor": "blue",
#                 "color": "red",
#                 "weight": 2,
#                 "fillOpacity": 0.2
#             }
#         ).add_to(m)
#
#     return m
#
#
# geofences, clustered_df = make_geofences(positions, eps=0.05, min_samples=2)
# m = plot_geofences(clustered_df, geofences)
# m.save('test.html')
