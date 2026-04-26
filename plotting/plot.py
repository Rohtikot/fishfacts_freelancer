from pandas import DataFrame
import geopandas as gpd
import folium
import os
import pandas as pd
from folium.plugins import HeatMap

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))


def plot_vessel_track(dataframe: pd.DataFrame, m: folium.Map, vessel_name: str = None) -> folium.Map:
    """
    Plots a vessel's speed track on a given Folium map.

    Parameters:
    -----------
    dataframe : pd.DataFrame
        A DataFrame containing vessel tracking data. Must include the columns:
        - 'timestamp' (str or datetime): Time of recorded location.
        - 'latitude' (float): Latitude of the vessel.
        - 'longitude' (float): Longitude of the vessel.
        - 'speed' (float): Speed of the vessel in knots.

    m : folium.Map
        The Folium map object where the vessel track will be plotted.

    vessel_name : str, optional
        The name of the vessel to display in the popup (default is None).

    Returns:
    --------
    folium.Map
        The updated Folium map with the vessel track plotted.

    Notes:
    ------
    - The function creates a **PolyLine** between consecutive vessel positions.
    - The color of each line segment is determined by the vessel's speed using `get_speed_color(speed)`.
    - A popup with vessel details appears when clicking on a segment.
    """

    vessel_feature = folium.FeatureGroup(name=vessel_name)

    # Get next latitude and longitude
    dataframe['next_latitude'] = dataframe['latitude'].shift(-1)
    dataframe['next_longitude'] = dataframe['longitude'].shift(-1)

    # Iterate over all rows except the last one (since it has no "next" point)
    for index, row in dataframe.iloc[:-1].iterrows():
        timestamp = row['timestamp']
        lat = row['latitude']
        lon = row['longitude']
        next_lat = row['next_latitude']
        next_lon = row['next_longitude']
        speed = row['speed']

        # Construct popup content with vessel details
        popup_text = f"<div style='width: 160px;'>" \
                     f"<b>Vessel name:</b> {vessel_name}<br>" \
                     f"<b>Date</b>: {timestamp}<br>" \
                     f"<b>Latitude</b>: {lat}<br>" \
                     f"<b>Longitude</b>: {lon}<br>" \
                     f"<b>Speed</b>: {speed} knots<br>"

        # Add the line segment to the map
        folium.PolyLine(
            locations=[(lat, lon), (next_lat, next_lon)],
            color=get_speed_color(speed),
            weight=2,
            opacity=1,
            popup=popup_text
        ).add_to(vessel_feature)

    vessel_feature.add_to(m)

    return m


def plot_zones(folium_map: folium.Map) -> folium.Map:
    """
    Plot EEZ zone, close land zones and other zones

    Parameters:
    -----------
    folium_map : folium.Map

    Returns:
    --------
    folium.Map
        A folium map containing added polygons split into appropriate groups
    """

    def style_function(feature):
        """Helper function to return style depending on area type."""
        # Define colors and opacities for each zone type
        styles = {
            "eez": {"color": "turquoise", "fillOpacity": 0.1, "weight": 0.2},
            "joined_zone": {"color": "green", "fillOpacity": 0.2, "weight": 0.2},
            "close_land": {"color": "red", "fillOpacity": 0.2, "weight": 0.2},
        }

        # Get the zone type
        zone_type = feature["properties"]["zone_type"]

        # Get the style for the zone type, default to gray if not found
        style = styles.get(zone_type, {"color": "gray", "fillOpacity": 0.1, "weight": 0.3})

        return {
            "fillColor": style["color"],
            "color": 'gray',
            "weight": style["weight"],
            "fillOpacity": style["fillOpacity"]  # Set the opacity here
        }

    # Read zones into GeoPandas dataframe
    zone_gdf = gpd.read_parquet(os.path.join(root_dir, 'zoning/zones', 'zones.parquet')).set_crs('EPSG:4326')

    # Feature groups for different zones type (eez, close_land, other, etc.)
    feature_groups = {
        'close_land': folium.FeatureGroup(name="Close land zones", show=False),
        'eez_zone': folium.FeatureGroup(name='EEZ zones')
    }

    # Add polygons to feature groups, grouped by zone_type
    for name, group in zone_gdf.groupby('zone_type'):
        folium.GeoJson(group, name=name, style_function=style_function).add_to(
            feature_groups['close_land' if name == 'close_land' else 'eez_zone']
        )

    # Add feature groups to folium_map
    feature_groups['eez_zone'].add_to(folium_map)
    feature_groups['close_land'].add_to(folium_map)

    return folium_map


def plot_eez_zones2(m: folium.Map = None) -> folium.Map:
    # If m argument is not passed, create new map object based on mean coordinates of input dataframe
    if m is None:
        m = initialize_map()

    # Get path of EEZ zones
    cur_file_path = os.path.abspath(__file__)
    par_file_dir = os.path.dirname(cur_file_path)
    eez_zones_path = r"C:\Users\tokit\PycharmProjects\fishfacts_toolbox\zones\eez_zones"# os.path.join(par_file_dir, '../zones/eez_zones')
    eez_zones_folder = os.listdir(eez_zones_path)

    # Plot EEZ zones
    polygon_group_line = folium.FeatureGroup(name='EEZ zones (lines)')
    polygon_group_fill = folium.FeatureGroup(name='EEZ zones (fill)', show=False)

    for zone in eez_zones_folder:
        polygon_df = pd.read_csv(os.path.join(eez_zones_path, zone))
        if zone.split('_')[0] == 'neafc':
            polygon_line = plot_polygon(polygon_df)
            polygon_fill = plot_polygon(polygon_df, weight=0.05, fill=True, fill_opacity=0.1, fill_color='white')
        elif zone.split('_')[0] == 'joined':
            polygon_line = plot_polygon(polygon_df)
            polygon_fill = plot_polygon(polygon_df, weight=0.05, fill=True, fill_opacity=0.15, fill_color='green')
        else:
            polygon_line = plot_polygon(polygon_df)
            polygon_fill = plot_polygon(polygon_df, weight=0.05, fill=True, fill_opacity=0.12, fill_color='turquoise')

        polygon_line.add_to(polygon_group_line)
        polygon_fill.add_to(polygon_group_fill)

        polygon_group_line.add_to(m)
        polygon_group_fill.add_to(m)

    return m


def plot_heatmap(dataframe: pd.DataFrame, m: folium.Map, name: str = None) -> folium.Map:
    """Function to plot heatmap based on density of points from vessel track"""

    data = dataframe[['latitude', 'longitude']].values.tolist()

    # Create layer for the heatmap instance
    heatmap_layer = folium.FeatureGroup(name=name)

    # Add heatmap to the layer
    HeatMap(
        data=data,
        radius=6,
        blur=6,
    ).add_to(heatmap_layer)

    # Add layer to map m
    heatmap_layer.add_to(m)

    return m


def get_speed_color(speed: float) -> str:
    """ Get track color depending on speed. Color-gradient is from Fishfacts live map"""
    if 0 <= speed <= 0.3:
        return '#0118c8'  # dark blue
    elif 0.3 < speed <= 1:
        return '#4e74fb'  # medium light blue
    elif 1 < speed <= 3:
        return '#4db2ff'  # light blue
    elif 3 < speed <= 4:
        return '#01e6b7'  # turquoise
    elif 4 < speed <= 5.5:
        return '#b3f95b'  # lime
    elif 5.5 < speed <= 7:
        return '#ffff00'  # yellow
    elif 7 < speed <= 10:
        return '#ffd325'  # orange
    elif 10 < speed <= 13:
        return '#ff8717'  # dark orange
    elif speed > 13:
        return '#ff0000'  # red


def add_bathymetry(fol_map: folium.Map):
    # Add GEBCO bathymetry WMS layer
    folium.WmsTileLayer(
        url='https://wms.gebco.net/mapserv?',
        layers='GEBCO_LATEST',
        fmt='image/png',
        transparent=True,
        attribute='GEBCO'
    ).add_to(fol_map)

    return fol_map


def plot_eez_zones_w_shorelines(m: folium.Map) -> folium.Map:
    # Define a style function for customizing polygons
    def style_function(feature):
        return {
            "fillColor": "turquoise",  # Fill color
            "color": "grey",          # Border color
            "weight": 0.05,           # Border thickness
            "fillOpacity": 0.1        # Transparency
        }

    # Areas' ids from Marine Regions
    ids = [
        5690,
        5684,
        5683,
        5675,
        5676,
        5687,
        5694,
        5674,
        5686,
        5669,
        5668,
        3293,
        5696,
        8435,
        5681,
        5680,
        8437,
        33181,
        8438,
        5677
    ]

    path = r"C:\Users\tokit\Downloads\World_EEZ_v12_20231025\World_EEZ_v12_20231025\eez_v12.shp"
    df = gpd.read_file(path)

    # Select multipolygons from each country
    selected_df = df[(df['MRGID'].isin(ids))]

    feature_group = folium.FeatureGroup(name="Selected EEZ Zones")

    # Add each multipolygon to the map
    for _, row in selected_df.iterrows():
        folium.GeoJson(
            row.geometry,
            style_function=style_function,
            name=f"Feature {row.name}"
        ).add_to(feature_group)

    feature_group.add_to(m)

    return m


def plot_other_zones(m: folium.Map = None) -> folium.Map:
    # If m argument is not passed, create new map object based on mean coordinates of input dataframe
    if m is None:
        m = initialize_map()

    # Get path of other zones
    cur_file_path = os.path.abspath(__file__)
    par_file_dir = os.path.dirname(cur_file_path)
    other_zones_path = os.path.join(par_file_dir, '../zones/other_zones')
    other_zones_folder = os.listdir(other_zones_path)

    # Plot other zones in a layer each
    for zone in other_zones_folder:
        if zone.endswith('.csv'):  # in case there are non-csv files in directory
            group_name = get_zone_name(zone)
            polygon_group = folium.FeatureGroup(name=group_name, show=False)
            polygon_df = pd.read_csv(os.path.join(other_zones_path, zone))
            polygon = plot_polygon(polygon_df, color='yellow', fill=True, fill_opacity=0.2, fill_color='yellow')
            polygon.add_to(polygon_group)
            polygon_group.add_to(m)

    return m


# Plot single polygon
def plot_polygon(input_df: DataFrame, color: str = 'grey', **kwargs) -> folium.Polygon:
    # Default parameters for polygon
    default_kwargs = {
        'color': color,
        'weight': 0.5,
        'opacity': 0.5,
        'fill': False,
        'fill_opacity': 0,
        'fill_color': color
    }

    # Merge custom kwargs with default kwargs
    merged_kwargs = {**default_kwargs, **kwargs}

    # Plot polygon
    polygon = folium.Polygon(
        locations=input_df[['latitude', 'longitude']].values.tolist(),
        **merged_kwargs
    )

    return polygon


# Function to initialize folium map object
def initialize_map(lat: float = 62.0, lon: float = -7.0, zoom_start=5) -> folium.Map:
    m = folium.Map(
        location=(lat, lon),
        zoom_start=zoom_start,
        attr=None
    )

    m = add_bathymetry(m)

    m.options['attributionControl'] = False

    tiles = {
        'OpenStreetMap': 'Open Street Map',
        'CartoDB.Positron': 'Positron',
        'CartoDB.PositronNoLabels': 'Positron (no labels)',
        'Stadia.StamenToner': 'Stamen Toner',
        'Stadia.StamenTonerBackground': 'Stamen Toner (no labels)',
        'Stadia.AlidadeSmoothDark': 'Alidade Smooth Dark',
        'CartoDB.Voyager': 'Voyager',
        'CartoDB.VoyagerNoLabels': 'Voyager (no labels)',
        'OpenStreetMap.HOT': 'OpenStreetMap HOT',
        'CartoDB.DarkMatter': 'Dark Matter',
        'CartoDB.DarkMatterNoLabels': 'Dark Matter (no labels)',
    }

    for key, value in tiles.items():
        folium.TileLayer(key, name=value).add_to(m)

    return m


def get_zone_name(file_name):
    # Function to return proper name according to passed file
    names = {
        'norway250_nm.csv': 'Norway 250 nm zone',
        'norway250_nm_w_fjords.csv': 'Norway 250 m zone incl. fjords',
        'norway_eez_north_62.csv': 'Norway EEZ north 62N',
        'norway_eez_south_62.csv': 'Norway EEZ south 62N'
    }

    if file_name in names:
        return names[file_name]
    else:
        return file_name

