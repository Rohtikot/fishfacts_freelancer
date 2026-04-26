from find_ship_history import *
from datetime import datetime
from db.model import VesselType
from db.vessel_dao import get_vessels_all_to_dataframe

pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.float_format', '{:,.1f}'.format)

warnings.filterwarnings("ignore", "Your application has authenticated using end user credentials")
connection_settings.settings = json.loads(open('../settings.json').read())

start, end = datetime(2023, 1, 1), datetime(2024, 1, 1)
country = 'NO'
vessel_type = [VesselType.PELAGIC, VesselType.FREEZING_TRAWLER, VesselType.COAST, VesselType.TRAWLER]

df = get_vessel_changes_for_country(start, end, country, vessel_type)
# df = df[df['vessel_status_id'] == 1]
df.sort_values(by='updated_at', inplace=True)

df['name'] = df['name'].str.title()
df['before_name'] = df['before_name'].str.title()
df['after_name'] = df['after_name'].str.title()
df = df[['id', 'name', 'imo', 'mmsi', 'flag', 'call_sign', 'updated_at', 'before_name', 'after_name']]

grouped = df.groupby(['name', 'id']).agg(
    name1=('before_name', 'unique'),
    name2=('after_name', 'unique'),
    date=('updated_at', 'first')
).reset_index()


# Define a function to combine lists, handling NaNs
def combine_lists(row):
    curr_name = row['name']

    list1 = list(row['name1'])
    list2 = list(row['name2'])

    listm = list(set(list1+list2))
    listm = [i for i in listm if i != curr_name]

    return listm


# Apply the function to create the 'previous_names' column
grouped['previous_names'] = grouped.apply(combine_lists, axis=1)
grouped = grouped[['name', 'id', 'previous_names']]
print(grouped)
