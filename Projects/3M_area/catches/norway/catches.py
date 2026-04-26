import pandas as pd
from catch.nor_catch_functions import *
from tqdm import tqdm
import folium
from plot import plot_area_3m

pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

dfs = []
for year in tqdm(range(2023, 2026), total=3):
    df = read_dca(year)
    dfs.append(df)
df = pd.concat(dfs)

df = df[
    (df['Startposisjon bredde'].between(39.0, 49.25)) & (df['Startposisjon lengde'].between(-46.5, -42.0)) &  # the bounds of area 3M
    (df['Aktivitet'] != 'Steaming')
]

print(df.head())

df['year'] = df['start_time'].dt.year
df['month'] = df['start_time'].dt.month
df['week'] = df['start_time'].dt.isocalendar().week

pivot = df.pivot_table(
    index=['Fartøynavn (ERS)', 'Radiokallesignal', 'start_time', 'stop_time', 'year', 'month', 'week'],
    columns='Art - FDIR',
    values='Rundvekt',
    aggfunc='sum'
).reset_index()

print(pivot)
# pivot.to_excel('norway_catches_every_operation.xlsx', index=False)
catches = (
    df
    .groupby(['year', 'month', 'week', 'Fartøynavn (ERS)', 'Art - FDIR'], as_index=False)
    .agg(Rundvekt=('Rundvekt', 'sum'))
)
print(catches)
# catches.to_excel('norway_catches_weekly_total.xlsx', index=False)
