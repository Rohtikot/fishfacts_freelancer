from resample.resample import resample_with_interpolation
from utils.distance import calculate_distance
from zoning.zoning import assign_eez, assign_close_land
from fuel_consumption.fuel_calculation import calculate_oil, calculate_co2_emissions
import pandas as pd
import glob
from tqdm import tqdm


def main():
    # load files from AIS path
    load_path = r"C:\Users\tokit\PycharmProjects\fishfacts-data-analysis-toolbox\reports\mackerel_report\data\ais\raw"
    save_path = r"C:\Users\tokit\PycharmProjects\fishfacts-data-analysis-toolbox\reports\mackerel_report\data\ais\resampled"
    folder = glob.glob(load_path + r'\*.xlsx')

    for file_path in (pbar := tqdm(folder, total=len(folder))):
        file_name = file_path.split('\\')[-1]
        vessel_id = int(file_name.split('_')[1])
        vessel_name = file_name.split('_')[2]

        pbar.set_description(f"Processing {vessel_id}-{vessel_name}")

        df = pd.read_excel(file_path)

        # resample and interpolate
        df = resample_with_interpolation(df, interval=15)

        # calculate metrics
        df['distance_nm'] = calculate_distance(df)  # distance traveled per data point
        df['fuel_consumption_l'] = calculate_oil(df, vessel_id)  # oil consumption in liters per 15 minutes
        df['co2_kg'] = calculate_co2_emissions(df)  # co2 emission in kg per 15 minutes

        # assign zones
        df = assign_eez(df)
        df = df.drop_duplicates(subset=['timestamp', 'latitude', 'longitude'], keep='first')  # temporary solution to overlapping EEZ zones
        df = assign_close_land(df)
        print(df)
        df.to_excel(save_path + rf"\resampled_{file_name}", index=False)


main()
