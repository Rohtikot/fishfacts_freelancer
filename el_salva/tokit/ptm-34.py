import pandas as pd
from db import connection_settings
from db.vessel_dao import get_vessels_all_to_dataframe
import json

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

if __name__ == '__main__':
    connection_settings.settings = json.loads(open("../settings.json").read())

    # load vessel list from csv-file
    path = r"C:\Users\tokit\Downloads\vessel_finder_unique_vessels.csv"
    df = pd.read_csv(path)
    df.sort_values(by='id', ascending=True, inplace=True)

    status_codes = {
        1: "In service",
        2: "Sold_to_abroad",
        3: "Deleted",
        4: "Hidden (no ais signal long duration)",
        5: 'Test'
    }

    db_df = get_vessels_all_to_dataframe()
    db_df['vessel_status_id'] = db_df['vessel_status_id'].astype(int)
    db_df = db_df[db_df['id'].isin(df['id'])]
    db_df['vessel_status'] = db_df['vessel_status_id'].map(status_codes)
    order = ['id', 'name', 'flag', 'vessel_type_id', 'length_overall', 'vessel_status_id', 'vessel_status', 'imo', 'mmsi']
    db_df = db_df[order]

    print(db_df.head(5))
    db_df.to_excel('MMSI_ships_on_vessel_finder.xlsx', index=False)
