import pandas as pd
pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)

# VORN TABLE
df = pd.read_parquet('longliners_vorn.parquet')
df = df[df['radio_callsign'] == 'OW2115']
print(df)

df['vessel_id'] = 581
df['fishing_area_name'] = 'NAFO'
renames = {
    'Toskur': 'Cod',
    'Steinbítur': 'Wolf-fish, Catfish, Steen biter',
    'Steinbítur (Wolffishes/Catfish': 'Wolf-fish, Catfish, Steen biter',
    'Kalvi': 'Halibut',
    'Brosma': 'Tusk',
}
df.rename(columns={'date': 'landing_date', 'value (kg)': 'volume', 'species': 'specie_name'}, inplace=True)
df['specie_name'] = df['specie_name'].replace(renames)
df = df[['vessel_id', 'vessel_name', 'landing_date', 'specie_name', 'fishing_area_name', 'volume']]
ff = pd.read_parquet('longliners_ff.parquet')
# join names onto catches df
names = pd.read_parquet('../../ais_data/vessels_info.parquet', columns=['id', 'name'])
names.rename(columns={'name': 'vessel_name'}, inplace=True)
ff = pd.merge(ff, names, left_on='vessel_id', right_on='id')
ff['volume'] = ff['volume'].combine_first(ff['volume_total'])
ff = ff[['vessel_id', 'vessel_name', 'landing_date', 'specie_name', 'fishing_area_name', 'volume']]

df = pd.concat([df, ff])
df['landing_date'] = pd.to_datetime(df['landing_date'], format='%Y-%m-%d')
df['year'] = df['landing_date'].dt.year
df['month'] = df['landing_date'].dt.month
df['week'] = df['landing_date'].dt.isocalendar().week
df = df[['vessel_id', 'vessel_name', 'landing_date', 'year', 'month', 'week', 'specie_name', 'fishing_area_name', 'volume']]
print(df)
df.to_excel('faroe_catches.xlsx', index=False)
