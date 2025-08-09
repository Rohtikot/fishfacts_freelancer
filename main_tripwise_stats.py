from tripwise_functions.tripwise_metrics import master_function
from tqdm import tqdm
import pandas as pd
import glob

pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)


def main():
    # Read trips DataFrame
    trips = pd.read_excel(r"reports/mackerel_report/data/trips/trips.xlsx")

    # Get file paths for AIS
    path = r"C:\Users\tokit\PycharmProjects\fishfacts-data-analysis-toolbox\reports\mackerel_report\data\ais\resampled"
    folder = glob.glob(path + '/*.xlsx')

    # List to store each vessel's trips
    all_vessels_trips = []

    for file in tqdm(folder, total=len(folder)):
        # Get vessel id, to be used in the trips query
        file_text = file.split('\\')[-1]
        vessel_id = int(file_text.split('_')[2])
        vessel_name = file_text.split('_')[3]

        # Read current vessel's AIS DataFrame
        ais_df = pd.read_excel(file)

        # Find current vessel's trips
        vessel_trips = trips[trips['vessel_id'] == vessel_id]
        calculated_trips = master_function(ais_df, vessel_trips)

        # Add vessel ID and name to calculated_trips dataframe before appending to all_vessels_trips list
        calculated_trips['vessel_id'] = vessel_id
        calculated_trips['vessel_name'] = vessel_name

        # Set column order
        calculated_trips = calculated_trips[['vessel_id', 'vessel_name', 'start', 'end', 'category', 'value']]

        # Add to all_vessels_trips list
        all_vessels_trips.append(calculated_trips)

    # Concatenate all vessel trips
    dfs = pd.concat(all_vessels_trips)
    print(dfs)
    for i in dfs['category'].unique():
        print(i)
    # dfs.to_excel('mackerel_example_report_trips.xlsx', index=False)


if __name__ == '__main__':
    main()
