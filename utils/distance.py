from nautical_calculations.basic import get_distance
from pandas import DataFrame, Series


def calculate_distance(dataframe: DataFrame) -> Series:
    """
    Calculate the distance between each row of an AIS data frame
    :param dataframe: A pandas DataFrame containing columns "latitude" and "longitude"
    :return: A pandas Series containing the distances in nautical miles between each row of the input data frame
    """
    dataframe = dataframe.copy()

    dataframe['previous_latitude'] = dataframe['latitude'].shift()
    dataframe['previous_longitude'] = dataframe['longitude'].shift()

    return dataframe.apply(
        lambda row: get_distance(row['latitude'],
                                 row['longitude'],
                                 row['previous_latitude'],
                                 row['previous_longitude']) * 0.539956803, axis=1)  # conversion from km to nm
