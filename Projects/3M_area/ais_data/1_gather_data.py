import os
import pandas as pd

"""This takes all the sheets from all the excel files and adds them into one dataframe to be saved as .parquet"""

pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)

vessel_types = {
    3: 'trawler',
    4: 'freezing_trawler',
    5: 'longliner',
}
folder = [i for i in os.listdir('') if i.endswith('.xlsx')]

dfs = []

for path in folder:
    # Get vessel type ID and vessel_type_name from file names
    vessel_type_id = int(path[0])
    vessel_type = vessel_types[vessel_type_id]

    file = pd.ExcelFile('ais_data/' + path)
    for sheet in file.sheet_names:
        vessel_id, vessel_name = sheet.split('-', 1)
        vessel_id = int(vessel_id)

        df = pd.read_excel('ais_data/' + path, sheet_name=sheet)
        df['vessel_id'] = vessel_id
        df['vessel_name'] = vessel_name
        df['vessel_type_id'] = vessel_type_id
        df['vessel_type'] = vessel_type
        print(df)
        dfs.append(df)

final_df = pd.concat(dfs)

print(final_df.shape[0])

final_df.to_csv('ais_data_for_all_vessels.csv', index=False)
final_df.to_parquet('ais_data_for_all_vessels.parquet', index=False)
