from pandas import DataFrame, Series, to_datetime
from astral.sun import elevation
from astral import LocationInfo


def calculate_daylight(dataframe: DataFrame) -> Series:
    """
    Calculate the solar elevation for each row in the DataFrame and return a Series.

    :param dataframe: A DataFrame containing timestamp, latitude and longitude columns.
    :return: A Series with the solar elevation in degrees for each row in the DataFrame.
    """
    dataframe = dataframe.copy()

    def get_solar_elevation(row):
        location = LocationInfo(latitude=row['latitude'], longitude=row['longitude'])
        start_time = to_datetime(row['timestamp'])
        solar_elevation = elevation(location.observer, start_time)
        return solar_elevation

    # Apply the get_solar_elevation function to each row and return the resulting Series
    return dataframe.apply(get_solar_elevation, axis=1)
