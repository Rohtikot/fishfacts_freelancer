from plotting.plot import plot_vessel_track
import pandas as pd
import matplotlib.pyplot as plt
import folium
from resample.resample_fix_time_gaps import resample_with_interpolation

pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)


df = pd.read_parquet('ais_data/ais_data_for_all_vessels_resampled.parquet')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df[
    (df['is_inside'])
    & (df['speed'] <= 6)
]
print(df.head())

df['year'] = df['timestamp'].dt.year
df['month'] = df['timestamp'].dt.month
df['week'] = df['timestamp'].dt.isocalendar().week

# Count of vessels per year
result = (
    df.groupby(['year', 'flag', 'vessel_type'])
    .agg(
        num_vessels=('vessel_id', 'nunique'),
        vessels=('vessel_id', lambda x: list(
            zip(
                x.unique(),
                df.loc[x.index, 'vessel_name'].drop_duplicates().values
            )
        ))
    )
    .reset_index()
    .sort_values(by=['year', 'vessel_type', 'flag'])
)

fishing_points_summary = (
    df.groupby(['year', 'month', 'week', 'flag', 'vessel_id', 'vessel_name', 'vessel_type'])
    .agg(
        fishing_points=('timestamp', 'count'),
        fishing_hours=('timestamp', lambda x: len(x) * 0.25),
        fishing_days=('timestamp', lambda x: len(x) * 0.25 * 1 / 24),
    )
    .reset_index()
)

fishing_points_summary.sort_values(by='fishing_points', inplace=True)
print(result)
print(fishing_points_summary)
print(fishing_points_summary)
fishing_points_summary.to_excel('ais-based_statistics.xlsx', index=False)
