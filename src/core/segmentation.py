import pandas as pd


def split_tracks(df, max_gap='4h'):
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.sort_values(by=['vessel_id', 'timestamp'])

    # Compute time difference per vessel
    df['dt'] = df.groupby('vessel_id')['timestamp'].diff()

    # Start a new segment if gap is larger than "max_gap" or first point
    df['new_segment'] = (df['dt'].isna()) | (df['dt'] > pd.Timedelta(max_gap))

    # Cumulative sum -> segment id
    df['segment_id'] = df.groupby('vessel_id')['new_segment'].cumsum()
    print(f'Inside split_tracks')
    print(df)
    return df


if __name__ == '__main__':
    from src.db.ais import get_vessel_locations_to_data_frame
    from datetime import datetime
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    # df = get_vessel_locations_to_data_frame(2, datetime(2025, 1, 1), datetime(2025, 2, 1))
    df = pd.read_parquet('../../data/ais/vessel_10.parquet')
    print(df)
    df = split_tracks(df)
    print(df)