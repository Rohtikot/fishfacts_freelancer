from plotting.plot import *
import numpy as np
import pandas as pd
import folium
from shapely.geometry import Polygon, MultiPoint, MultiPolygon
from shapely.ops import unary_union
from scipy.spatial import Delaunay
from pyproj import CRS, Transformer
from folium.plugins import FeatureGroupSubGroup
from sklearn.cluster import KMeans


# -----------------------------
# Projection utilities (WGS84 <-> local UTM)
# -----------------------------
def utm_crs_for_ll(lon, lat):
    zone = int((lon + 180) // 6) + 1
    epsg = 32600 + zone if lat >= 0 else 32700 + zone
    return CRS.from_epsg(epsg)


def get_transformers(lon0, lat0):
    wgs84 = CRS.from_epsg(4326)
    utm = utm_crs_for_ll(lon0, lat0)
    fwd = Transformer.from_crs(wgs84, utm, always_xy=True)
    inv = Transformer.from_crs(utm, wgs84, always_xy=True)
    return fwd, inv


# --------------------------------
# Alpha shape (concave hull)
# --------------------------------
def _triangle_circumradius(pts3):
    a = np.linalg.norm(pts3[1] - pts3[0])
    b = np.linalg.norm(pts3[2] - pts3[1])
    c = np.linalg.norm(pts3[0] - pts3[2])
    s = (a + b + c) / 2.0
    area_sq = s * (s - a) * (s - b) * (s - c)
    if area_sq <= 0:
        return np.inf
    area = np.sqrt(area_sq)
    return (a * b * c) / (4.0 * area)


def _delaunay_edge_lengths(points_xy):
    tri = Delaunay(points_xy)
    edges = set()
    for simplex in tri.simplices:
        for i in range(3):
            a = simplex[i]
            b = simplex[(i + 1) % 3]
            edges.add(tuple(sorted((a, b))))
    return np.array([np.linalg.norm(points_xy[j] - points_xy[i]) for (i, j) in edges])


def alpha_shape(points_xy, alpha=None, auto_factor=1.6):
    points_xy = np.asarray(points_xy)
    if len(points_xy) < 4:
        return MultiPoint(points_xy).convex_hull, None
    if alpha is None:
        lengths = _delaunay_edge_lengths(points_xy)
        if len(lengths) == 0:
            return MultiPoint(points_xy).convex_hull, None
        p60 = np.percentile(lengths, 60)
        r_thresh = auto_factor * p60
        alpha = 1.0 / r_thresh
    tri = Delaunay(points_xy)
    inv_alpha = 1.0 / alpha
    triangles = []
    for simplex in tri.simplices:
        tri_pts = points_xy[simplex]
        r = _triangle_circumradius(tri_pts)
        if r < inv_alpha:
            triangles.append(Polygon(tri_pts))
    if not triangles:
        return MultiPoint(points_xy).convex_hull, alpha
    concave = unary_union(triangles)
    if concave.is_empty:
        return MultiPoint(points_xy).convex_hull, alpha
    return concave, alpha


# -----------------------------------------
# Convert polygon(s) back to lat/lon rings
# -----------------------------------------
def polygon_to_latlon_rings(geom, inv_transformer):
    def _exterior_to_latlon(poly):
        x, y = poly.exterior.xy
        lons, lats = inv_transformer.transform(list(x), list(y))
        return list(zip(lats, lons))  # folium expects (lat, lon)
    if isinstance(geom, MultiPolygon):
        return [_exterior_to_latlon(p) for p in geom.geoms]
    elif hasattr(geom, "exterior"):
        return [_exterior_to_latlon(geom)]
    return []


# ============================================================
# Main script
# ============================================================
def main():
    path = r'data/crab_fisheries_2020-2025.csv'
    df = pd.read_csv(path, parse_dates=['stop_time'])
    df = df[df['stop_time'].dt.year >= 2021]
    df.rename(columns={'Stopposisjon bredde': 'latitude',
                       'Stopposisjon lengde': 'longitude'}, inplace=True)

    # Year grouping: 2021–2024 vs 2025
    df['year'] = df['stop_time'].dt.year
    df['year_group'] = df['year'].where(df['year'] == 2025, "2021-2024")

    # Number of clusters per group
    n_clusters_map = {
        "2021-2024": 3,
        2025: 2
    }

    # Distinct colors per group
    group_colors = {
        "2021-2024": "#ff7f0e",  # orange
        2025: "#1f77b4",         # blue
    }

    geofence_results = {}
    area_records = []

    for name, group in df.groupby("year_group"):
        lon0, lat0 = group["longitude"].mean(), group["latitude"].mean()
        fwd, inv = get_transformers(lon0, lat0)

        x, y = fwd.transform(group["longitude"].values, group["latitude"].values)
        points_xy = np.column_stack([x, y])

        # KMeans clustering
        n_clusters = n_clusters_map[name]
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels = kmeans.fit_predict(points_xy)
        group = group.copy()
        group["cluster"] = labels

        geofence_results[name] = {}

        for cluster_id, cdf in group.groupby("cluster"):
            x, y = fwd.transform(cdf["longitude"].values, cdf["latitude"].values)
            points_xy = np.column_stack([x, y])

            convex_geom = MultiPoint(points_xy).convex_hull
            concave_geom, used_alpha = alpha_shape(points_xy, alpha=None, auto_factor=1.3)
            concave_buffer_geom = concave_geom.buffer(5000)  # 5 km buffer

            # Compute areas in km² (shapely areas are in m² in projected coords)
            convex_area = convex_geom.area / 1e6
            concave_area = concave_geom.area / 1e6
            buffer_area = concave_buffer_geom.area / 1e6

            # Save results
            convex_rings = polygon_to_latlon_rings(convex_geom, inv)
            concave_rings = polygon_to_latlon_rings(concave_geom, inv)
            concave_buffer_rings = polygon_to_latlon_rings(concave_buffer_geom, inv)

            geofence_results[name][cluster_id] = {
                "points": cdf[["latitude", "longitude"]],
                "convex": convex_rings,
                "concave": concave_rings,
                "buffer": concave_buffer_rings,
                "alpha": used_alpha,
            }

            area_records.append({
                "group": name,
                "cluster": cluster_id,
                "convex_km2": convex_area,
                "concave_km2": concave_area,
                "buffer_km2": buffer_area
            })

    # -----------------------------------
    # Folium map with main group + subgroups
    # -----------------------------------
    # Initialize Folium map
    m = initialize_map(70, 20, zoom_start=10)

    # Plot EEZ zones as a layer
    m = plot_eez_zones2(m)
    for group, clusters in geofence_results.items():
        # Main toggle for group
        parent_layer = folium.FeatureGroup(name=f"{group}", show=True)
        m.add_child(parent_layer)

        # Subgroups under the group
        points_layer = FeatureGroupSubGroup(parent_layer, name=f"{group} – Points", show=True)
        convex_layer = FeatureGroupSubGroup(parent_layer, name=f"{group} – Convex hulls", show=False)
        concave_layer = FeatureGroupSubGroup(parent_layer, name=f"{group} – Concave hulls", show=True)
        buffer_layer = FeatureGroupSubGroup(parent_layer, name=f"{group} – Buffers (+5 km)", show=False)

        m.add_child(points_layer)
        m.add_child(convex_layer)
        m.add_child(concave_layer)
        m.add_child(buffer_layer)

        # Add all clusters' geometries into these subgroups
        for cluster_id, results in clusters.items():
            # Points
            for _, row in results["points"].iterrows():
                folium.CircleMarker(
                    location=(row["latitude"], row["longitude"]),
                    radius=1,
                    color=group_colors[group],
                    fill=True,
                    fill_color=group_colors[group],
                    fill_opacity=0.85,
                    weight=0,
                ).add_to(points_layer)

            # Convex hulls
            for ring in results["convex"]:
                folium.Polygon(
                    locations=ring,
                    color=group_colors[group],
                    weight=0.3,
                    fill=False,
                    dash_array="5,6",
                    tooltip=f"{group} cluster {cluster_id} convex"
                ).add_to(convex_layer)

            # Concave hulls
            for ring in results["concave"]:
                folium.Polygon(
                    locations=ring,
                    color=group_colors[group],
                    weight=0.3,
                    fill=True,
                    fill_opacity=0.5,
                    tooltip=f"{group} cluster {cluster_id} concave (alpha={results['alpha']:.5f})"
                ).add_to(concave_layer)

            # Buffers
            for ring in results["buffer"]:
                folium.Polygon(
                    locations=ring,
                    color=group_colors[group],
                    weight=0.3,
                    fill=True,
                    fill_opacity=0.5,
                    tooltip=f"{group} cluster {cluster_id} buffer"
                ).add_to(buffer_layer)

    # Fit map to data
    bounds = [[df["latitude"].min(), df["longitude"].min()],
              [df["latitude"].max(), df["longitude"].max()]]
    m.fit_bounds(bounds)

    folium.LayerControl(collapsed=True).add_to(m)
    m.save("geofence_map_how_it_currently_is_being_produced.html")
    print("Generated map: geofence_map_how_it_currently_is_being_produced.html")

    # -----------------------------------
    # Print area summary
    # -----------------------------------
    area_df = pd.DataFrame(area_records)
    print("\n=== Geofence Areas (km²) ===")
    print(area_df)
    area_df.to_excel("geofence_areas.xlsx", index=False)
    print("Saved geofence areas to 'geofence_areas.xlsx'")


if __name__ == "__main__":
    main()
