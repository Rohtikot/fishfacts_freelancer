import pandas as pd
pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)

df = pd.read_parquet('ais_data_for_all_vessels_resampled.parquet')
df['year'] = df['timestamp'].dt.year
df = df[
    (df['is_inside']) &
    (df['flag'] == 'Faroe Islands') &
    (df['speed'] <= 6)
]
fo_vessels = df[['vessel_id', 'vessel_name', 'vessel_type']].drop_duplicates()

fishing_points_summary = (
    df.groupby(['year', 'flag', 'vessel_id', 'vessel_name', 'vessel_type'])
    .agg(
        fishing_points=('timestamp', 'count'),
        fishing_hours=('timestamp', lambda x: len(x) * 0.25),
        fishing_days=('timestamp', lambda x: len(x) * 0.25 * 1 / 24),
    )
    .reset_index()
)
print(fishing_points_summary)
print(fo_vessels)

