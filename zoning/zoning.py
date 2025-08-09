import pandas as pd
import os
import geopandas as gpd

zone_dir = os.path.join(os.path.dirname(__file__), 'zones', 'zones.parquet')


def assign_eez(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Assigns an EEZ zone to each point"""

    # Load polygon data
    zone_gdf = gpd.read_parquet(os.path.join(zone_dir)).set_crs('EPSG:4326')
    # EEZ zones and joined zones
    zone_groups = {
        'eez': zone_gdf[zone_gdf['zone_type'] == 'eez'].rename(columns={'zone': 'eez_zone'}),
        'joined_zone': zone_gdf[zone_gdf['zone_type'] == 'joined_zone'].rename(columns={'zone': 'joined_zone'})
    }

    # Create Geopandas dataframe from AIS containing "geometry" column
    ais_df = gpd.GeoDataFrame(
        dataframe,
        geometry=gpd.points_from_xy(dataframe.longitude, dataframe.latitude),
        crs='EPSG:4326'
    )

    # Spatial joins
    for zone_type, gdf in zone_groups.items():
        ais_df = ais_df.sjoin(gdf, how="left", predicate="within").drop(columns=['index_right'])

    # Drop unnecessary columns
    return ais_df.drop(columns=['zone_type_left', 'zone_type_right', 'geometry'])


def assign_close_land(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Assigns whether each point is close to land"""

    # Read close land geo-fences
    close_land_gdf = gpd.read_parquet(os.path.join(zone_dir)).set_crs('EPSG:4326')
    close_land_gdf = close_land_gdf[close_land_gdf['zone_type'] == 'close_land']

    # Convert to GeoDataFrame for vectorized processing
    ais_gdf = gpd.GeoDataFrame(dataframe, geometry=gpd.points_from_xy(dataframe.longitude, dataframe.latitude),
                               crs="EPSG:4326")
    # Do spatial join on ais dataframe and polygons dataframe
    joined = ais_gdf.sjoin(close_land_gdf, how="left", predicate="within")
    dataframe['close_land'] = joined['index_right'].notna()

    return dataframe


def adjust_joined_zone_eez(dataframe: pd.DataFrame, vessel_flag: str) -> pd.DataFrame:
    """Adjusts EEZ assignment for vessels in applicable joined zones. Dataframe must contain zone columns."""

    # Define reassignment rules for each joined zone based on vessel flags.
    # If a vessel is in a specific joined zone, its EEZ assignment is overridden
    # based on the vessel's flag.
    joined_zone_rules = {
        'joined_fro_ice': {'IS': 'iceland_eez', 'FO': 'faroe_islands_eez'},  # Iceland-Faroe rule
        'joined_jm_ice': {'IS': 'iceland_eez', 'NO': 'jan_mayen_eez'},  # Jan Mayen-Iceland rule
        'joined_fro_uk': {'FO': 'faroe_islands_eez', 'GB': 'united_kingdom_eez'}  # UK-Faroe rule
    }

    def assign_correct_eez(row):
        """
        Checks if the vessel is in a joined zone and reassigns EEZ based on its flag.
        If the vessel's flag is not in the rules for that zone, it retains its original EEZ.
        """
        if row['joined_zone'] in joined_zone_rules:
            return joined_zone_rules[row['joined_zone']].get(vessel_flag, row['eez_zone'])
        return row['eez_zone']

    # Apply the EEZ reassignment logic to each row in the DataFrame
    dataframe['eez_zone'] = dataframe.apply(assign_correct_eez, axis=1)
    return dataframe


def correct_overlaps(dataframe: pd.DataFrame, vessel_flag: str) -> pd.DataFrame:
    # TODO: Some areas of some EEZ Zones overlap. This overlap causes the AIS point to be in two zones at the same time,
    #  meaning there will be duplicate rows.
    #  Quick fix is to drop duplicates and choose either one, since this incident is rare.
    #  Other fix is to look at vessel's flag, and assign the point as the vessel's home country, if one of the polygons
    #  is the vessel's flag country.
    raise NotImplemented
