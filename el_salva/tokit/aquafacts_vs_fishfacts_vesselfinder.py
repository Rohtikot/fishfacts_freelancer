import json

import pandas as pd

from db import connection_settings
from db.vessel_dao import get_vessels_all_to_dataframe

status_codes = {
    1: "In service",
    2: "Sold_to_abroad",
    3: "Deleted",
    4: "Hidden (no ais signal long duration)",
    5: 'Test'
}


if __name__ == '__main__':
    pd.set_option('display.width', None)
    # connection_settings.settings = json.loads(open("../settings.json").read())
    # vessels = get_vessels_all_to_dataframe()
    # vessels.to_excel('all_vessels.xlsx', index=False)

    af_type_ids = [15, 16, 17, 18, 19, 20, 26, 27]
    # ff_type_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 21, 22, 23, 24, 25]
    type_ids = pd.read_excel('../vessel_types.xlsx')
    type_ids = type_ids.rename(columns={'id': 'vessel_type_id'})
    vessels = pd.read_excel('all_vessels.xlsx')
    vessels = vessels[vessels['vessel_type_id'].isin(af_type_ids)]
    dfs = pd.merge(vessels, type_ids, on='vessel_type_id')
    dfs = dfs.drop(columns=['name_fo_fo', 'name_no_no', 'name_is_is', 'parent_id', 'supported_fields', 'crm_only'])
    # print(dfs.head(5))
    # print(dfs.shape[0])

    vf_df = pd.read_csv(r"C:\Users\tokit\Downloads\vessel_finder_unique_vessels (1).csv")
    li = vf_df['id'].tolist()

    dfs = dfs[~dfs['id'].isin(li)]
    dfs['vessel_status'] = dfs['vessel_status_id'].map(status_codes)
    dfs.to_excel('aquafacts_not_on_vesselfinder.xlsx', index=False)
    print(dfs)
    print(dfs.shape[0])
