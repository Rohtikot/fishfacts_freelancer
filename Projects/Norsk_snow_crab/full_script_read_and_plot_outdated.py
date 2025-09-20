from plotting.plot import *
import numpy as np
import pandas as pd
from shapely.geometry import Polygon, MultiPoint, MultiPolygon
from shapely.ops import unary_union
from scipy.spatial import Delaunay
from pyproj import CRS, Transformer
import folium
from folium.plugins import FeatureGroupSubGroup

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


def polygon_area_km2(polygon, lon0, lat0):
    """Calculate area of a shapely polygon in km², given a reference lon/lat."""
    fwd, _ = get_transformers(lon0, lat0)  # use your existing function
    x, y = fwd.transform(*polygon.exterior.xy)
    poly_utm = Polygon(zip(x, y))
    return poly_utm.area / 1e6  # convert m² to km²


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
        return list(zip(lats, lons))  # (lat, lon) pairs for folium
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

    geofence_results = {}

    for name, group in df.groupby("year_group"):
        lon0, lat0 = group["longitude"].mean(), group["latitude"].mean()
        fwd, inv = get_transformers(lon0, lat0)

        # IMPORTANT: order is (lon, lat)
        x, y = fwd.transform(group["longitude"].values, group["latitude"].values)
        points_xy = np.column_stack([x, y])

        convex_geom = MultiPoint(points_xy).convex_hull
        concave_geom, used_alpha = alpha_shape(points_xy, alpha=None, auto_factor=1.3)
        concave_buffer_geom = concave_geom.buffer(5000)  # 5 km buffer

        convex_rings = polygon_to_latlon_rings(convex_geom, inv)
        concave_rings = polygon_to_latlon_rings(concave_geom, inv)
        concave_buffer_rings = polygon_to_latlon_rings(concave_buffer_geom, inv)

        geofence_results[name] = {
            "convex": convex_rings,
            "concave": concave_rings,
            "buffer": concave_buffer_rings,
            "alpha": used_alpha,
            "points": group[["latitude", "longitude"]],
        }

    # -----------------------------------
    # Folium map with nested toggleable layers
    # -----------------------------------

    # Initialize Folium map
    m = initialize_map(70, 20)

    # Plot EEZ zones as a layer
    m = plot_eez_zones2(m)

    # Distinct colors per group
    group_colors = {
        "2021-2024": "#ff7f0e",  # orange
        2025: "#1f77b4",  # blue
    }

    colors = {
        "2021-2024": {"concave": "#ffd166", "convex": "#06d6a0", "buffer": "#06d6a0"},
        2025: {"concave": "#66d1ff", "convex": "#d606a0", "buffer": "#d606a0"},
    }

    # Add geofence layers per group & type
    for group, results in geofence_results.items():
        # Parent (top-level) group
        parent_layer = folium.FeatureGroup(name=f"{group}", show=True)
        m.add_child(parent_layer)

        # Points subgroup
        points_layer = FeatureGroupSubGroup(parent_layer, name=f"{group} points", show=True)
        for _, row in results["points"].iterrows():
            folium.CircleMarker(
                location=(row["latitude"], row["longitude"]),
                radius=1,
                color="#5bc0ff",
                fill=True,
                fill_color=group_colors[group],
                fill_opacity=0.60,
                weight=0,
            ).add_to(points_layer)
        points_layer.add_to(m)

        # Convex subgroup
        convex_layer = FeatureGroupSubGroup(parent_layer, name=f"{group} convex", show=False)
        for ring in results["convex"]:
            folium.Polygon(
                locations=ring,
                color=colors[group]["convex"],
                weight=2,
                fill=False,
                dash_array="5,6",
                tooltip=f"{group} convex"
            ).add_to(convex_layer)
        convex_layer.add_to(m)

        # Concave subgroup
        concave_layer = FeatureGroupSubGroup(parent_layer, name=f"{group} concave (alpha={results['alpha']:.5f})", show=True)
        for ring in results["concave"]:
            folium.Polygon(
                locations=ring,
                color=colors[group]["concave"],
                weight=2,
                fill=True,
                fill_color=colors[group]["concave"],
                fill_opacity=0.1
            ).add_to(concave_layer)
        concave_layer.add_to(m)

        # Buffer subgroup
        buffer_layer = FeatureGroupSubGroup(parent_layer, name=f"{group} buffer (+5 km)", show=False)
        for ring in results["buffer"]:
            folium.Polygon(
                locations=ring,
                color=colors[group]["buffer"],
                weight=2,
                fill=True,
                fill_opacity=0.1,
                tooltip=f"{group} buffer"
            ).add_to(buffer_layer)
        buffer_layer.add_to(m)

    # Fit to data
    bounds = [[df["latitude"].min(), df["longitude"].min()],
              [df["latitude"].max(), df["longitude"].max()]]
    m.fit_bounds(bounds)

    folium.LayerControl(collapsed=True).add_to(m)
    m.save("geofence_map_test.html")
    print("Generated map: geofence_map.html")


if __name__ == "__main__":
    main()
