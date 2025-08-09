import pandas as pd
from scipy.interpolate import interp1d


def resample_with_interpolation(dataframe: pd.DataFrame, interval: int = 15, max_gap_hours: float = 4) -> pd.DataFrame:
    """
    Resamples and interpolates a DataFrame to a consistent time interval, avoiding interpolation across large time gaps.

    Parameters:
    -----------
    dataframe : pd.DataFrame
        Input data with 'timestamp', 'speed', 'latitude', 'longitude', 'heading'

    interval : int
        Desired resampling interval in minutes

    max_gap_hours : float
        Maximum allowed gap for interpolation (in hours). Gaps larger than this will break the interpolation.

    Returns:
    --------
    pd.DataFrame
        Interpolated DataFrame with uniform timestamps and no cross-gap interpolation
    """
    dataframe = dataframe.sort_values('timestamp').reset_index(drop=True)
    dataframe['time_diff'] = dataframe['timestamp'].diff()
    max_gap = pd.Timedelta(hours=max_gap_hours)

    # Create a group for each continuous chunk
    dataframe['segment'] = (dataframe['time_diff'] > max_gap).cumsum()
    dataframe = dataframe.drop(columns='time_diff')

    # Prepare list of resampled segments
    all_segments = []

    for _, segment_df in dataframe.groupby('segment'):
        if len(segment_df) < 2:
            continue  # skip segments too small to interpolate

        # Create timestamp range for this segment
        start_time = segment_df['timestamp'].iloc[0].replace(minute=0, second=0, microsecond=0)
        end_time = segment_df['timestamp'].iloc[-1]
        timestamp_range = pd.date_range(start=start_time, end=end_time, freq=f'{interval}min')

        # Interpolate speed
        interp_func = interp1d(segment_df['timestamp'].astype('int64'), segment_df['speed'], kind='linear',
                               fill_value='extrapolate')
        interpolated_data = pd.DataFrame({
            'timestamp': timestamp_range,
            'speed': interp_func(timestamp_range.astype('int64'))
        })

        # Merge with nearest lat/lon/heading from the segment
        merged = pd.merge_asof(
            interpolated_data,
            segment_df.drop(columns=['speed', 'segment']),
            on='timestamp',
            direction='nearest'
        )

        all_segments.append(merged)

    # Combine all segments
    result = pd.concat(all_segments, ignore_index=True)
    result = result.sort_values('timestamp').reset_index(drop=True)

    return result[['timestamp', 'latitude', 'longitude', 'speed', 'heading']]
