from db.vessel_dao import get_vessel_historical_name
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
from db.model import VesselType

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=".*authenticated using end user credentials.*"
)

pd.set_option('display.width', None)
pd.set_option('display.max_rows', 101)
pd.set_option('display.float_format', '{:,.0f}'.format)


if __name__ == '__main__':
    connection_settings.settings = json.loads(open("../settings.json").read())
    vessels = pd.read_parquet(r'C:\Users\tokit\PycharmProjects\fishfacts_freelancer\Projects\3M_area\ais_data\ais_data_for_all_vessels_resampled.parquet')

    # === NORWEGIAN VESSELS ONLY
    vessels = vessels[vessels['flag'] == 'Norway']
    vessel_ids = vessels['vessel_id'].unique()
    # print(vessels.head(3))
    #
    df = get_vessels_all_to_dataframe()
    df = df[df['name'].isin(['Kambur'])]
    print(df)
    hist = get_vessel_historical_name()
    hist['updated_at'] = pd.to_datetime(hist['updated_at'])
    # df = df[df['vessel_type_id'].isin([VesselType.FREEZING_TRAWLER, VesselType.TRAWLER, VesselType.LONG_LINER])]
    # print(df)
    hist = hist[
        (hist['vessel_id'].isin([581]))
        & (hist['updated_at'] >= datetime(2020, 3, 1))
    ]
    print(hist)
    # df = df[df['id'].isin(vessel_ids)]
    # print(hist)

