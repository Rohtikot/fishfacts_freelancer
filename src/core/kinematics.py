import numpy as np


def heading(lat1, lat2, lon1, lon2):
    y = np.sin(np.radians(lon2 - lon1)) * np.cos(np.radians(lat2))
    x = np.sin(np.radians(lat1)) * np.sin(np.radians(lat2)) - \
        np.sin(np.radians(lat1)) * np.cos(np.radians(lat2)) * \
        np.cos(np.radians(lon2 - lon1))
    return (np.degrees(np.arctan2(y, x)) + 360) % 360


def compute_speed(df):
    df = df.copy()
    dt = df['timestamp'].diff().dt.total_seconds()
    df['speed_calc'] = df['distance_nm'] / dt * 3600
    df.loc[dt == 0, 'speed_calc'] = None
    return df
