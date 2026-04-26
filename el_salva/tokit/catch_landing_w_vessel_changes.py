from find_ship_history import *
from datetime import datetime
from db.model import VesselType
from db.catch_dao import get_catch_all

connection_settings.settings = json.loads(open('../settings.json').read())


def get_catch_for_country_by_period(start: datetime, end: datetime, country: 'str', ) -> pd.DataFrame:
    vessels = get_vessel_changes_for_country(start, end, country)

    # Get catch
    catch = get_catch_all()
    catch['date'] = pd.to_datetime(catch['date'])
    catch = catch[(catch['vessel_flag'] == 'Norway')]

    merged_df = pd.merge(catch, vessels, left_on='vessel_id', right_on='id', how='outer')

    # Filter rows where date falls within valid_from and valid_to
    # Apply filtering: include all rows if valid_from/valid_to are NaT, otherwise filter by date range
    filtered_df = merged_df[
        (merged_df['date'] > start) & (merged_df['date'] < end)
        & (merged_df['valid_from'].isna() & merged_df['valid_to'].isna()) |
        ((merged_df['date'] >= merged_df['valid_from']) & (merged_df['date'] <= merged_df['valid_to']))
        ]
    filtered_df = filtered_df[
        (filtered_df['specie_name'] == 'Mackerel')
        & (filtered_df['vessel_type'] == 'Pelagic')
        ]
    filtered_df.sort_values(by='date', inplace=True)

    return filtered_df


res = get_catch_for_country_by_period(datetime(2023, 1, 1), datetime(2024, 1, 1), 'NO')
print(res)
