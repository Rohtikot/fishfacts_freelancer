import pandas as pd

pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

vorn = pd.read_parquet('longliners_vorn.parquet')
vorn = vorn[vorn['radio_callsign'] == 'OW2115']
print(vorn)

# df = pd.read_parquet('longliners_ff.parquet')
#
# names = pd.read_parquet('../../ais_data/vessels_info.parquet', columns=['id', 'name'])
# names.rename(columns={'name': 'vessel_name'}, inplace=True)
# ff = pd.merge(df, names, left_on='vessel_id', right_on='id')
# ff['volume'] = ff['volume'].combine_first(ff['volume_total'])
# ff = ff[['vessel_id', 'vessel_name', 'landing_date', 'specie_name', 'fishing_area_name', 'volume']]
#
# print(ff)

