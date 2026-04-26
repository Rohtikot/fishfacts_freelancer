import pandas as pd
import json
from db import connection_settings

pd.set_option('display.width', None)


"""
#################### TABLES IN THE DATABASE ####################
table_schema             table_name
   fishfacts                  catch
   fishfacts      catch_destination
   fishfacts                company
   fishfacts                country
   fishfacts           engine_model
   fishfacts           fishing_area
   fishfacts               location
   fishfacts              ownership
   fishfacts                species
   fishfacts                 vessel
   fishfacts  vessel_action_history
   fishfacts            vessel_type
   fishfacts            vessel_yard
"""


def get_all_tables_mysql() -> pd.DataFrame:
    with connection_settings.connect_to_database().connect() as connection:
        df = pd.read_sql(
            "SELECT table_schema, table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema = DATABASE()",
            connection)

    return df


def get_table(table_name: str) -> pd.DataFrame:
    with connection_settings.connect_to_database().connect() as connection:
        table = pd.read_sql(
            f"SELECT * FROM {table_name} ",
            connection)

    return table


if __name__ == '__main__':
    pd.set_option('display.max_rows', None)
    connection_settings.settings = json.loads(open("../settings.json").read())

    table1 = get_table('vessel')
    vessel_imo = table1[(table1['name'] == 'Komandor') | (table1['imo'] == '8505977')]
    print(vessel_imo)
    # print(table1.head())
    # table2 = get_table('ownership')
    # table3 = get_table('company')
    # table4 = get_table('country')
    #
    # # table2 = table2[table2['end'].isna()]
    # print(table2.head())
    # company_df = pd.merge(table2, table3, left_on='company_id', right_on='id', how='outer')
    #
    # vessel_df = pd.merge(table1, company_df, left_on='id', right_on='vessel_id', how='outer')
    # print(vessel_df.head(10))
    #
    # columns = [
    #     'id',
    #     'name_x',
    #     'vessel_type_id',
    #     'flag',
    #     'imo',
    #     'mmsi',
    #     'call_sign',
    #     'harbour_number',
    #     'registration_number_x',
    #     'build_year',
    #     'vessel_status_id',
    #     'name_y',
    #     'previous_name'
    # ]
    # vessel_df = vessel_df[columns]
    # table4 = table4[['id', 'name_gb_en']]
    # vessel_df = pd.merge(vessel_df, table4, left_on='flag', right_on='id', how='inner', suffixes=('_v', '_z'))
    #
    # status_names = {
    #     1: 'In service',
    #     2: 'Sold to abroad',
    #     3: 'Deleted',
    #     4: 'Hidden',
    #     5: 'Undefined'
    # }
    #
    # columns_renames = {
    #     'id_v': 'Vessel_ID',
    #     'name_x': 'Vessel_name',
    #     'name_gb_en_y': 'Vessel_type',
    #     'name_gb_en_x': 'Flag',
    #     'imo': 'IMO',
    #     'mmsi': 'MMSI',
    #     'call_sign': 'Callsign',
    #     'harbour_number': 'Harbor_No.',
    #     'registration_number_x': 'Registration_No.',
    #     'build_year': 'Build_year',
    #     'status': 'Status',
    #     'name_y': 'Owner',
    #     'previous_name': 'Previous_name(s)'
    # }
    # vessel_type_df = get_table('vessel_type')
    # vessel_df = pd.merge(vessel_df, vessel_type_df, left_on='vessel_type_id', right_on='id', how='inner')
    #
    # vessel_df['status'] = vessel_df['vessel_status_id'].map(status_names)
    # vessel_df.rename(columns=columns_renames, inplace=True)
    # print(vessel_df.head(3))
    # columns_order = ['Vessel_ID', 'Vessel_name', 'Vessel_type', 'Flag', 'IMO', 'MMSI', 'Callsign', 'Harbor_No.', 'Registration_No.', 'Build_year', 'Owner', 'Status']
    # ordered_df = vessel_df[columns_order]
    # ordered_df['Build_year'] = pd.to_numeric(ordered_df['Build_year'], errors='coerce').fillna(0).astype(int)
    # ordered_df['Vessel_ID'] = pd.to_numeric(ordered_df['Vessel_ID'], errors='coerce').fillna(0).astype(int)
    # ordered_df['IMO'] = pd.to_numeric(ordered_df['IMO'], errors='coerce').fillna(0).astype(int)
    # ordered_df['MMSI'] = pd.to_numeric(ordered_df['MMSI'], errors='coerce').fillna(0).astype(int)
    # print(ordered_df.head(10))
    # ordered_df.to_excel('Vessels_ff_db.xlsx', index=False)
