import pandas as pd


def find_time_gaps(dataframe: pd.DataFrame, threshold_hours: int) -> pd.DataFrame:
    """
    Find instances where the time gap between two points is greater than a specified threshold in hours

    :param dataframe: A pandas DataFrame containing columns "timestamp"
    :param threshold_hours: An integer representing number of hours
    :return: A pandas DataFrame containing the gap start, gap end and delta time for instances where timedelta
    is greater than set threshold.
    """

    dataframe.sort_values(by='timestamp', inplace=True)
    dataframe['next_time'] = dataframe['timestamp'].shift(-1)
    dataframe['timedelta'] = dataframe['timestamp'].diff().shift(-1)
    too_longs = dataframe[dataframe['timedelta'] > pd.Timedelta(hours=threshold_hours)].copy()
    too_longs.rename(columns={'timestamp': 'gap_start', 'next_time': 'gap_end'}, inplace=True)
    return too_longs[['gap_start', 'gap_end', 'timedelta']]


if __name__ == '__main__':
    path = r"C:\Users\tokit\OneDrive\Desktop\Aker Biomarine rapport juni 2025\ais\vessel_989_Long Teng_20240101T0000-20250621T0000.xlsx"
    df = pd.read_excel(path)
    gaps = find_time_gaps(df, 4)
    print(gaps)


