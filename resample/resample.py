import pandas as pd
from scipy.interpolate import interp1d


def resample_with_interpolation(dataframe: pd.DataFrame, interval: int = 15) -> pd.DataFrame:
    """
        Resamples and interpolates a DataFrame to a consistent time interval without altering positional data.

        This function resamples the input DataFrame to a fixed time interval (default: 15 minutes)
        and interpolates the 'speed' column using linear interpolation. The 'latitude', 'longitude',
        and 'heading' columns remain unchanged and are assigned based on the nearest available timestamp.

        Parameters:
        -----------
        input_df : pd.DataFrame
            A DataFrame containing at least the following columns:
            - 'timestamp' (datetime): Time of each observation.
            - 'speed' (float): Speed values to interpolate.
            - 'latitude' (float): Latitude values
            - 'longitude' (float): Longitude values
            - 'heading' (float): Heading values

        interval : int, optional (default=15)
            The time interval (in minutes) to which the data should be resampled.

        Returns:
        --------
        pd.DataFrame
            A DataFrame with resampled timestamps and interpolated speed values,
            preserving latitude, longitude, and heading from the original data.

        Notes:
        ------
        - The function assumes the 'timestamp' column is in datetime format.
        - Linear interpolation is applied only to 'speed'.
        - 'latitude', 'longitude', and 'heading' remain unchanged and are assigned
          from the nearest available timestamp using `merge_asof()`.
        """

    # Create data range based on input data frame
    start_time = dataframe['timestamp'].iloc[0].replace(minute=0, second=0, microsecond=0)
    end_time = dataframe['timestamp'].iloc[-1]
    timestamp_range = pd.date_range(start=start_time, end=end_time, freq=f'{interval}min')

    # Create a function for interpolation
    interp_func = interp1d(dataframe['timestamp'].astype('int64'), dataframe['speed'], kind='linear',
                           fill_value='extrapolate')

    # Create new data frame to merge with input data frame
    interpolated_data = {
        'timestamp': timestamp_range,
        'speed': interp_func(timestamp_range.astype('int64'))
    }

    # Merge the two data frames and remove the old speed column
    interpolated_df = pd.DataFrame(interpolated_data)
    interpolated_df = pd.merge_asof(
        interpolated_df,
        dataframe.drop(columns=['speed']),
        on='timestamp',
        direction='nearest'
    )

    return interpolated_df[['timestamp', 'latitude', 'longitude', 'speed', 'heading']]

