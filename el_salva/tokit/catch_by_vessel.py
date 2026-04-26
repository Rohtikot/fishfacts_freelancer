from datetime import datetime
import pandas as pd
import json
from time import sleep
from tqdm import tqdm
import warnings
from db.vessel_dao import get_vessels_all_to_dataframe
from db.catch_dao import get_catch_all, get_catch_by_vessel
from db import connection_settings
from trip_finder.db.trip_dao import find_trips_all
from trip_finder.trip_catch import calculate_catch_per_trip

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=".*authenticated using end user credentials.*"
)

pd.set_option('display.width', None)
pd.set_option('display.max_rows', None)

if __name__ == '__main__':
    connection_settings.settings = json.loads(open("../settings.json").read())
    from datetime import datetime

    dfs = []

    vessel_ids = [153, 581, 731, 784, 795, 932, 935, 940, 941, 956, 1931]

    for vessel_id in vessel_ids:
        # Catches
        df = get_catch_by_vessel(vessel_id)
        df['landing_date'] = pd.to_datetime(df['landing_date'])
        df = df[
            (df['landing_date'] > datetime(2023, 3, 1))
            & (df['landing_date'] < datetime(2025, 9, 30))
            & (df['fishing_area_name'] == 'NAFO')
            ]
        dfs.append(df)

    dfs = pd.concat(dfs)
    dfs.sort_values(by=['vessel_id', 'landing_date'], inplace=True)
    dfs = dfs[dfs['id'] == 581]
    print(dfs)
    # dfs.to_parquet(r'C:\Users\tokit\PycharmProjects\fishfacts_freelancer\Projects\3M_area\catches\faroe\longliners_ff.parquet', index=False)
