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
        style = styles.get(zone_type, {"color": "gray", "fillOpacity": 0.5, "weight": 0.1})

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

