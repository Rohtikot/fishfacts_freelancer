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
            f"SELECT * FROM {table_name} LIMIT 100",
            connection)

    return table


if __name__ == '__main__':
    pd.set_option('display.max_rows', None)
    connection_settings.settings = json.loads(open("../settings.json").read())
    print(get_all_tables_mysql())
    table = get_table('location')
    # table = get_table('country')
    # table = table[table['id'] == 4711]
    print(table)
    # table.to_csv('pretty_names.csv', index=False)
    # table = table['']

