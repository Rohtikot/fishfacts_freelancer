from datetime import datetime
import numpy as np
import pandas as pd


def perform_interval_join(ais_dataframe: pd.DataFrame, trips_dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Perform an interval join between AIS data and corresponding trip data.

    This function merges AIS data with trip information based on timestamps,
    ensuring that each AIS record is associated with the correct trip.
    It matches AIS records to trips that started before or at the same time
    as the AIS record's timestamp, and ensures that the AIS record's timestamp
    falls within the trip's duration.

    Parameters:
    ais_dataframe (pd.DataFrame): A DataFrame containing AIS data with a 'timestamp' column.
    trips_dataframe (pd.DataFrame): A DataFrame containing trip data with 'start' and 'end' columns.

    Returns:
    pd.DataFrame: A merged DataFrame containing AIS records with associated trip information,
                  ensuring that each AIS record is linked to the correct trip based on timestamps.
    """

    # Sort both dataframes by their respective datatime columns to prepare for the merge
    ais_dataframe = ais_dataframe.sort_values('timestamp')
    trips_dataframe = trips_dataframe.sort_values('start')

    # Join dataframes such that AIS rows are associated with their corresponding trip
    joined = pd.merge_asof(ais_dataframe, trips_dataframe, left_on='timestamp', right_on='start', direction='backward')

    # Filter the joined DataFrame to ensure only AIS records within trip durations are retained
    joined = joined[joined['timestamp'] <= joined['end']]

    return joined


def calculate_trip_metrics(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate aggregated trip-level metrics from AIS data.

    This function groups the AIS data by trip start and end times to compute key metrics:
    - Total duration of the trip
    - Total distance traveled in nautical miles (nm)
    - Total fuel consumption in liters (l)
    - Count of AIS records

    Parameters:
    dataframe (pd.DataFrame): A DataFrame containing AIS data, which must include
                              'start', 'end', 'duration', 'distance_nm', 'fuel_consumption_l',
                              and 'timestamp' columns.

    Returns:
    pd.DataFrame: A DataFrame with aggregated metrics for each trip, indexed by 'start' and 'end'.
                  The resulting columns will include:
                  - total_duration: Duration of the trip
                  - total_distance: Total distance traveled (in nautical miles)
                  - total_consumption: Total fuel consumed (in liters)
                  - count_ais_records: Number of AIS records associated with the trip
    """

    # Group the data by trip start and end times
    aggregated_metrics = dataframe.groupby(['start', 'end']).agg(
        total_duration=('duration', 'first'),
        total_distance=('distance_nm', 'sum'),
        total_consumption_l=('fuel_consumption_l', 'sum'),
        count_ais_records=('timestamp', 'count')
    )

    return aggregated_metrics


def calculate_trip_speeds(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Categorize AIS data into speed groups and compute the time spent in each category per trip.

    Parameters:
    dataframe (pd.DataFrame): A DataFrame containing AIS data, including columns for speed, trip start and end times.

    Returns:
    pd.DataFrame: A DataFrame with the total hours spent in each speed category for each trips
                  defined by 'start' and 'end' columns.
                  The speed categories are:
                  - 'fishing': 0.3 to 7.5 knots
                  - 'transit': 7.5 to 10 knots
                  - 'speedy_transit': 10 knots and above
    """

    def categorize_speed(speed):
        """Helper function to classify speed into predefined categories."""
        if 0.3 <= speed < 7.5:
            return 'fishing'
        elif 7.5 <= speed < 10:
            return 'transit'
        elif speed >= 10:
            return 'speedy_transit'

    # Calculate speed categories for each AIS record
    dataframe['speed_category'] = dataframe['speed'].apply(categorize_speed)

    # Count the number of AIS records per speed category per trip
    speed_counts = dataframe.groupby(['start', 'end', 'speed_category']).size().unstack(fill_value=0)

    # Convert counts to hours (each point = 0.25 hours)
    speed_counts = speed_counts * 0.25
    speed_counts = speed_counts.rename(
        columns={
            'fishing': 'fishing_hours',
            'transit': 'transit_hours',
            'speedy_transit': 'speedy_transit_hours'
        }
    )

    return speed_counts


def calculate_trip_eez_fishing(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate fishing hours per EEZ zone.

    This function filters the input DataFrame to retain only the records
    where the vessel's speed indicates fishing activity (between 0.3 and 7.5).
    It then counts the number of AIS records per EEZ zone for each trip,
    converts the counts to hours, and renames the columns to indicate
    that they represent fishing hours.

    Parameters:
    ----------
    dataframe : pd.DataFrame
        A DataFrame containing AIS records, with columns including 'speed',
        'start', 'end', and 'eez_zone'.

    Returns:
    -------
    pd.DataFrame
        A new DataFrame where the index is composed of the unique combinations
        of 'start', 'end', and 'eez_zone', and the columns represent the
        number of fishing hours per zone.
    """

    # Filter speeds to only include fishing speeds
    dataframe = dataframe[(dataframe['speed'] >= 0.3) & (dataframe['speed'] < 7.5)]

    # Count the number of AIS records per EEZ zone
    zone_counts = dataframe.groupby(['start', 'end', 'eez_zone']).size().unstack(fill_value=0)

    # Convert counts to hours (each point = 0.25 hours)
    zone_counts = zone_counts * 0.25

    # Add "_fishing_hours" to column names to indicate which metric is being calculated
    zone_counts = zone_counts.rename(lambda x: f"{x}_fishing_hours", axis=1).fillna(0)

    return zone_counts


def master_function(ais_dataframe: pd.DataFrame, trips_dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Master function to process AIS and trip data and return a long-format DataFrame.

    This function combines the functions:
        - perform_interval_join()
        - calculate_trip_metrics()
        - calculate_trip_speeds()
        - calculate_trip_eez_fishing()

    This function integrates multiple processing steps to:
    1. Join the AIS data with trip records using `perform_interval_join()`.
    2. Compute various trip-related metrics, including:
       - General trip metrics (`calculate_trip_metrics`)
       - Speed-based activity categorization (`calculate_trip_speeds`)
       - Fishing activity by EEZ zone (`calculate_trip_eez_fishing`)
    3. Merge the calculated metrics into a single DataFrame.
    4. Transform the DataFrame into a long-format structure using `pd.melt()`,
       excluding zero-value rows for cleaner output.

    Parameters:
    ----------
    ais_dataframe : pd.DataFrame
        The vessel's AIS data, containing timestamped location and movement information.

    trips_dataframe : pd.DataFrame
        The corresponding trips data, defining the start and end times of each trip.

    Returns:
    -------
    pd.DataFrame
        A long-format DataFrame with trip-related metrics, categorized by activity type.
        Each row represents a unique (start, end, category, value) combination.
    """

    # Check if AIS data is uniformly resampled on 15 minute intervals
    ais_dataframe = ais_dataframe.copy()
    ais_dataframe['timestamp'] = pd.to_datetime(ais_dataframe['timestamp'])

    # Compute time differences
    time_diffs = ais_dataframe['timestamp'].diff().dt.total_seconds().dropna()
    ais_dataframe['diffs'] = ais_dataframe['timestamp'].diff().dt.total_seconds().dropna()
    ais_dataframe = ais_dataframe[ais_dataframe['timestamp'] >= datetime(2023, 1, 27, 11, 30)]
    # print(ais_dataframe)
    diffs = ais_dataframe[ais_dataframe['diffs'] != 900.0].iloc[1:-1]
    # print(diffs)
    expected_interval = 15 * 60  # 15 minutes = 900 seconds

    if not np.all(np.isclose(time_diffs, expected_interval, atol=5)):  # 5 second tolerance
        raise ValueError('AIS data is not uniformly resampled to 15-minute intervals.')
    # if not (time_diffs == pd.Timedelta(minutes=15)).all():
    #     raise ValueError('AIS data is not uniformly resampled to 15-minute intervals.')

    # Join the trips and AIS dataframes
    joined_df = perform_interval_join(ais_dataframe=ais_dataframe, trips_dataframe=trips_dataframe)

    # Calculate metrics in grouped (pivot) format
    trip_metrics = calculate_trip_metrics(joined_df)
    speed_groups = calculate_trip_speeds(joined_df)
    eez = calculate_trip_eez_fishing(joined_df)

    final_metrics = pd.merge(trip_metrics, speed_groups, on=['start', 'end'], how='left')
    final_metrics = pd.merge(final_metrics, eez, on=['start', 'end'], how='left')
    final_metrics = final_metrics.reset_index()

    # Melt dataframe into long format
    value_vars = final_metrics.drop(columns=['start', 'end']).columns.tolist()

    long_df = pd.melt(
        final_metrics,
        id_vars=['start', 'end'],
        value_vars=value_vars,
        var_name='category',
        value_name='value'
    )
    long_df = long_df[long_df['value'] > 0]  # exclude rows with 0 value, as these don't give any information
    long_df.sort_values(by='start', inplace=True)

    return long_df

