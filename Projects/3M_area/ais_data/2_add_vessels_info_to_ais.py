import pandas as pd

"""This adds vessel information onto AIS-data in the RAW ais data parquet."""

pd.set_option('display.width', None)

df = pd.read_parquet('vessels_info.parquet')
df = df[['id', 'flag']]
pretty = pd.read_csv('pretty_names.csv')
pretty = pretty[['id', 'name_gb_en']]
print(pretty)
df = pd.merge(df, pretty, left_on='flag', right_on='id', how='left')
df.drop(columns=['id_y'], inplace=True)
df.rename(columns={'id_x': 'id'}, inplace=True)
print(df)

raw_ais = pd.read_parquet('ais_data_for_all_vessels.parquet')
merged = pd.merge(raw_ais, df, left_on='vessel_id', right_on='id', how='left')
merged.drop(columns=['id_y', 'flag_x', 'flag_y', 'id_x'], inplace=True)
merged.rename(columns={'name_gb_en': 'flag'}, inplace=True)
print(merged)

merged.to_parquet('ais_data/ais_data_for_all_vessels.parquet', index=False)
