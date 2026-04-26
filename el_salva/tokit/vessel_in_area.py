from db import connection_settings
from db.location_dao import get_vessel_locations_to_data_frame

from time import sleep
from datetime import datetime

from pandas import DataFrame, ExcelWriter
from tqdm import tqdm
from shapely.geometry import Point, Polygon

import json


def download_vessels_in_area(
        vessels_df: DataFrame,
        output_file_name: str,
        polygon: Polygon,
        start: datetime,
        end: datetime) -> None:
    """
    Create Excel file with a sheet for each vessel's AIS data within given period if vessel is inside area.

    Args:
        vessels_df: (DataFrame) dataframe containing vessel name and vessel id
        output_file_name: (str) name (and location) of file
        polygon: (Polygon) shapely Polygon
        start: (datetime) start time (not inclusive)
        end: (datetime) end time (not inclusive)
    """

    # helper function to determine if vessel is inside given area (polygon)
    def is_point_in_area(row, p):
        point = Point(row['longitude'], row['latitude'])
        return p.contains(point)

    try:
        writer = ExcelWriter(f'{output_file_name}.xlsx', engine='xlsxwriter')

        # establish connection to database
        connection_settings.settings = json.loads(open("../settings.json").read())

        # iterate through vessels in vessels_df and check if they're inside given area
        for index, vessel in (pbar := tqdm(vessels_df.iterrows(), total=vessels_df.shape[0], desc='Processing')):
            vessel_id = vessel['id']
            vessel_name = vessel['name']
            pbar.set_description(f"Processing {vessel_name}")  # update progress bar text

            # load current vessel's AIS data into pandas data frame
            _df = get_vessel_locations_to_data_frame(vessel_id, start=start, end=end)

            _df['is_inside'] = _df.apply(is_point_in_area, axis=1, p=polygon)

            # check if any point in _df is in area
            if _df['is_inside'].any():
                _df.to_excel(writer, sheet_name=f"{vessel_id}-{vessel_name}", index=False)
            sleep(1)
        writer.close()

    # if KeyboardInterrupt, save the progress so far.
    except KeyboardInterrupt:
        print('\nKeyboard interrupt detected. Performing cleanup...')
        writer.close()
        print('\nCleanup completed.')
