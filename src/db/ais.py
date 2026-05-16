from datetime import datetime
import pandas as pd
from sqlalchemy import text

from src.db import connection_settings


def get_vessel_locations_to_data_frame(vessel_id: int, start: datetime, end: datetime) -> pd.DataFrame:
    sql = ("SELECT "
           "    vessel_id,"
           "    timestamp,"
           "    latitude,"
           "    longitude,"
           "    IF(speed > 19.99, NULL, speed) as `speed`,"
           "    heading "
           "FROM location "
           f"WHERE vessel_id = {vessel_id} "
           f"   AND timestamp > '{start:%Y-%m-%d %H:%M:%S}'"
           f"   AND timestamp < '{end:%Y-%m-%d %H:%M:%S}'"
           "ORDER BY timestamp")

    with connection_settings.connect_to_database().connect() as connection:
        df = pd.read_sql(
            sql,
            connection,
            parse_dates=["timestamp"])

        return df


def get_ais_candidates(
    start: datetime,
    end: datetime,
    bbox: list[float]
) -> pd.DataFrame:
    lon_min, lat_min, lon_max, lat_max = bbox

    sql = (
        "SELECT "
        "    vessel_id,"
        "    timestamp,"
        "    latitude,"
        "    longitude,"
        "    IF(speed > 19.99, NULL, speed) as speed "
        "FROM location "
        f"WHERE timestamp > '{start:%Y-%m-%d %H:%M:%S}' "
        f"  AND timestamp < '{end:%Y-%m-%d %H:%M:%S}' "
        f"  AND latitude BETWEEN {lat_min} AND {lat_max} "
        f"  AND longitude BETWEEN {lon_min} AND {lon_max} "
        "ORDER BY vessel_id, timestamp"
    )

    with connection_settings.connect_to_database().connect() as connection:
        df = pd.read_sql(sql, connection, parse_dates=["timestamp"])

    return df


def get_first_vessel_location(vessel_id: int) -> datetime | None:
    with connection_settings.connect_to_historical().connect() as connection:
        for row in connection.execute(text(f"SELECT MIN(timestamp FROM location WHERE vessel_id = {vessel_id})")):
            return row[0]
    return None



import pandas as pd
from datetime import datetime

def explain_vessel_query(
    vessel_id: int,
    start: datetime,
    end: datetime,
    bbox: list[float]
) -> pd.DataFrame:
    lon_min, lat_min, lon_max, lat_max = bbox

    sql = (
        "EXPLAIN "
        "SELECT "
        "    vessel_id,"
        "    timestamp,"
        "    latitude,"
        "    longitude,"
        "    speed "
        "FROM location "
        f"WHERE vessel_id = {vessel_id} "
        f"  AND timestamp > '{start:%Y-%m-%d %H:%M:%S}' "
        f"  AND timestamp < '{end:%Y-%m-%d %H:%M:%S}' "
        f"  AND latitude BETWEEN {lat_min} AND {lat_max} "
        f"  AND longitude BETWEEN {lon_min} AND {lon_max} "
        "ORDER BY timestamp"
    )

    with connection_settings.connect_to_database().connect() as connection:
        df = pd.read_sql(sql, connection)

    return df