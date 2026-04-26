from datetime import datetime
from db.location_dao import get_vessel_locations_to_data_frame
from db.vessel_dao import get_vessels_all_to_dataframe
from db import connection_settings
import json
import warnings
from vessels_meeting import find_close_encounters


warnings.filterwarnings("ignore", "Your application has authenticated using end user credentials")
warnings.filterwarnings("ignore", "Properties that return a naïve datetime object have been deprecated.")

connection_settings.settings = json.loads(open("../settings.json").read())


if __name__ == '__main__':
    # start, end = datetime(2024, 1, 1), datetime.now()
    # df1 = get_vessel_locations_to_data_frame(1766, start, end)
    # df2 = get_vessel_locations_to_data_frame(1432, start, end)

    vessels = get_vessels_all_to_dataframe()
    vessels = vessels[
        (vessels['flag'] == 'RU')
        & (vessels['vessel_type_id'] == 4)]
    print(vessels)
    print(vessels.shape[0])
    # results = find_close_encounters(df1, df2, time_tolerance_minutes=5)
    # print(results)
    # results.to_excel('test.xlsx', index=False)
