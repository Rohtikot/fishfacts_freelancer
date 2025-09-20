import matplotlib.pyplot as plt

from sklearn.cluster import DBSCAN
from shapely.geometry import MultiPoint
import geopandas as gpd
from catch.nor_catch_functions import read_dca, file_age, download_ers
from folium import features
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from shapely.geometry import MultiPoint
import geopandas as gpd
import folium

pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)


def main():
    path = r'data/crab_fisheries_2020-2025.csv'
    df = pd.read_csv(path, parse_dates=['stop_time'])
    df = df[df['stop_time'].dt.year >= 2021]
    # # Find which vessels are included in snow crab fisheries

    df['year'] = df['stop_time'].dt.year
    df['year_group'] = df['year'].where(df['year'] == 2025, "2021-2024")
    print(df.head())
    nor_vessels = df[['Radiokallesignal (ERS)', 'Fartøynavn (ERS)', 'Største lengde']].drop_duplicates()
    nor_vessels.sort_values(by='Største lengde', ascending=False, inplace=True)

    plt.hist(df['Varighet'], bins=np.arange(0, 10000, 60))
    plt.show()
    # Select only the relevant columns
    vessels_df = df[['year', 'Radiokallesignal (ERS)', 'Fartøynavn (ERS)', 'Største lengde']].drop_duplicates()

    # Sort by year and vessel name
    vessels_df.sort_values(by=['year', 'Fartøynavn (ERS)'], inplace=True)

    # Optional: reset index
    vessels_df.reset_index(drop=True, inplace=True)
    vessels_df.to_excel('crab_fishing_vessels_nor.xlsx', index=False)
    print(vessels_df)

    # result = df.groupby('year_group')
    # for name, group in result:
    #     print(group)

    # print(nor_vessels)
    # geofences, clustered_df = make_kmeans_geofences(positions, n_clusters=2)
    # m = plot_geofences(clustered_df, geofences)
    # m.save("kmeans_geofence_map.html")


def make_kmeans_geofences(df, n_clusters=3, crs="EPSG:4326"):
    """
    Cluster points into n_clusters using KMeans and build convex-hull geofences.

    Parameters
    ----------
    df : DataFrame with columns "Startposisjon bredde" (lat), "Startposisjon lengde" (lon)
    n_clusters : int, number of clusters
    crs : str, CRS for output GeoDataFrame (default: WGS84)

    Returns
    -------
    geofences : GeoDataFrame with cluster polygons
    df_with_clusters : DataFrame with cluster labels
    """
    coords = df[["Startposisjon bredde", "Startposisjon lengde"]].to_numpy()

    kmeans = KMeans(n_clusters=n_clusters, random_state=42).fit(coords)
    df = df.copy()
    df["cluster"] = kmeans.labels_

    geofences = []
    for cluster_id in sorted(df["cluster"].unique()):
        points = df.loc[df["cluster"] == cluster_id,
                        ["Startposisjon lengde", "Startposisjon bredde"]].to_numpy()
        polygon = MultiPoint(points).convex_hull
        geofences.append({"cluster": cluster_id, "geometry": polygon})

    gdf_geofences = gpd.GeoDataFrame(geofences, crs=crs)
    return gdf_geofences, df


def plot_geofences(df, geofences):
    # Center map
    center_lat = df["Startposisjon bredde"].mean()
    center_lon = df["Startposisjon lengde"].mean()
    m = folium.Map(location=[center_lat, center_lon],
                   tiles="CartoDB dark_matter", zoom_start=6)

    # Add per-cluster FeatureGroups
    for cluster_id in sorted(df["cluster"].unique()):
        group = folium.FeatureGroup(name=f"Cluster {cluster_id}", show=True).add_to(m)

        # Add points
        for _, row in df[df["cluster"] == cluster_id].iterrows():
            folium.CircleMarker(
                location=[row["Startposisjon bredde"], row["Startposisjon lengde"]],
                radius=4,
                color="yellow",
                fill=True,
                fill_opacity=0.7
            ).add_to(group)

        # Add polygon
        poly = geofences.loc[geofences["cluster"] == cluster_id, "geometry"].iloc[0]
        folium.GeoJson(
            poly.__geo_interface__,
            name=f"Cluster {cluster_id} geofence",
            style_function=lambda x: {
                "fillColor": "blue",
                "color": "red",
                "weight": 2,
                "fillOpacity": 0.2
            }
        ).add_to(group)

    folium.LayerControl(collapsed=False).add_to(m)
    return m

if __name__ == '__main__':
    main()
