from find_ship_history import *
from datetime import datetime
from db.model import VesselType
from db.catch_dao import get_catch_all


pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.float_format', '{:,.1f}'.format)

warnings.filterwarnings("ignore", "Your application has authenticated using end user credentials")
connection_settings.settings = json.loads(open('../settings.json').read())

start, end = datetime(2023, 1, 1), datetime(2023, 12, 31)
country = 'NO'
vessel_type = [VesselType.PELAGIC, VesselType.FREEZING_TRAWLER, VesselType.COAST, VesselType.TRAWLER]
df = get_vessel_changes_for_country(start, end, country, vessel_type)
df = df[df['vessel_status_id'] == 1]
df.sort_values(by='updated_at', inplace=True)

df['name'] = df['name'].str.title()
df['before_name'] = df['before_name'].str.title()
df['after_name'] = df['after_name'].str.title()

df = df[~df['valid_from'].isna() | ~df['valid_to'].isna()]
df.sort_values(by='valid_to', inplace=True)

# Get catch
catch = get_catch_all()
catch['date'] = pd.to_datetime(catch['date'])
catch = catch[(catch['vessel_flag'] == 'Norway')]

merged_df = pd.merge(catch, df, left_on='vessel_id', right_on='id', how='outer')

# Filter rows where date falls within valid_from and valid_to
# Apply filtering: include all rows if valid_from/valid_to are NaT, otherwise filter by date range
filtered_df = merged_df[
    (merged_df['date'].dt.year == 2023)
    & (merged_df['valid_from'].isna() & merged_df['valid_to'].isna()) |
    ((merged_df['date'] >= merged_df['valid_from']) & (merged_df['date'] <= merged_df['valid_to']))
]
filtered_df = filtered_df[
    (filtered_df['specie_name'] == 'Mackerel')
    & (filtered_df['vessel_type'] == 'Pelagic')
]
filtered_df.sort_values(by='date', inplace=True)
print(filtered_df.tail(10))
print(f"{filtered_df['volume'].sum():,.0f} kg")
