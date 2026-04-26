import pandas as pd
from nautical_calculations.basic import get_distance


def merge_df_on_timestamp(df1: pd.DataFrame, df2: pd.DataFrame, time_tolerance_minutes: int = 5) -> pd.DataFrame:
    """
    Merge two dataframes by aligning their timestamps to the nearest rounded timestamp.

    :param df1: pandas AIS dataframe
    :param df2: pandas AIS dataframe
    :param time_tolerance_minutes: int for minute tolerance
    :return: merged dataframe from both vessels with common column "timestamp_rounded"
    """

    # Make a rounded timestamp on each dataframe
    df1['timestamp_rounded'] = df1['timestamp'].dt.round('5min')
    df2['timestamp_rounded'] = df2['timestamp'].dt.round('5min')

    # Merge dataframes on the rounded timestamp column
    merged_df = pd.merge_asof(df1.sort_values('timestamp_rounded'),
                              df2.sort_values('timestamp_rounded'),
                              on='timestamp_rounded',
                              direction='nearest',
                              tolerance=pd.Timedelta(f'{time_tolerance_minutes}min'))

    merged_df.dropna(inplace=True)

    return merged_df


def distance_between_vessels(input_df: pd.DataFrame) -> pd.Series:
    # Calculate the distance between rows in data frame in meters
    distances = input_df.apply(
        lambda row: get_distance(
            row['latitude_x'],
            row['longitude_x'],
            row['latitude_y'],
            row['longitude_y'],
        ) * 1000, axis=1
    )

    # Calculate the rolling minimum to smooth out spikes in distance
    rolling_avg_distances = distances.rolling(window=5).min()

    return rolling_avg_distances


def find_close_encounters(df1: pd.DataFrame, df2: pd.DataFrame, time_tolerance_minutes: int = 5) -> pd.DataFrame:
    """
    Find the close encounters between two vessels

    :param df1: DataFrame of one vessel's AIS data
    :param df2: DataFrame of the other vessel's AIS data
    :param time_tolerance_minutes:  Time tolerance to align dataframes for
    :return:
    """

    # Merge both vessels' data frames on datetime column
    merged_df = merge_df_on_timestamp(df1, df2, time_tolerance_minutes)

    # Calculate the distance between each row of merged data frame
    merged_df['distance_m'] = distance_between_vessels(merged_df)

    # Create a boolean column indicating when distance_m is below 300 meters
    merged_df['below_threshold'] = merged_df['distance_m'] < 300

    # Assign a group identifier for consecutive below_threshold groups
    merged_df['group_id'] = (merged_df['below_threshold'] != merged_df['below_threshold'].shift()).cumsum()

    # Filter the dataframe to include only rows where distance_m is below 300 meters
    filtered_df = merged_df[merged_df['below_threshold']]

    # Group by group_id and find the start and stop times
    grouped = filtered_df.groupby('group_id').agg(
        start_time=('timestamp_rounded', 'min'),
        stop_time=('timestamp_rounded', 'max')
    ).reset_index(drop=True)

    return grouped
