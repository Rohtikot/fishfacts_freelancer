import geopandas as gpd
from shapely.geometry import Point
from shapely import contains_xy


def assign_zone_labels(df, polygons=None, zone_col: str = 'TERRITORY1'):
    if polygons is None:
        raise ValueError('Polygons must be provided via pipeline context')

    gdf = gpd.GeoDataFrame(
        df.copy(),
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs='EPSG:4326',
    )
    # Spatial join
    joined = gdf.sjoin(polygons, how='left', predicate='within')

    # Assign zone label
    joined['zone'] = joined[zone_col] if zone_col in joined else None

    # Boolean flag
    joined['in_zone'] = joined['zone'].notna()

    return joined.drop(columns='geometry')


def add_in_zone_flag(df, polygons=None):
    if polygons is None:
        raise ValueError('Polygons required')

    union = polygons.unary_union

    mask = contains_xy(union, df.longitude.values, df.latitude.values)

    df = df.copy()
    df['in_zone'] = mask

    return df


def detect_in_zone(df, polygons):
    """
    Fast check: does any AIS point fall inside polygon?
    Returns:
        bool
    """
    if df.empty:
        return False

    # build spatial index once
    sindex = polygons.sindex

    # iterate points (fast due to spatial index filtering)
    for lon, lat in zip(df.longitude.values, df.latitude.values):
        point = Point(lon, lat)

        # candidate polygons via bounding boxes
        possible_matches_idx = list(sindex.intersection(point.bounds))

        if not possible_matches_idx:
            continue

        # precise check
        for idx in possible_matches_idx:
            if polygons.geometry.iloc[idx].contains(point):
                return True
    return False