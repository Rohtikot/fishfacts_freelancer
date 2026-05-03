import pandas as pd

from src.db import connection_settings


def get_vessels_all_to_dataframe() -> pd.DataFrame:
    with connection_settings.connect_to_database().connect() as connection:
        df = pd.read_sql(
            "SELECT id, name, flag, vessel_type_id, imo, call_sign, bruttotons, length_overall, vessel_status_id "
            "FROM vessel",
            connection
        )
    return df


def get_vessel_historical_name() -> pd.DataFrame:
    with connection_settings.connect_to_database().connect() as connection:
        df = pd.read_sql(
            "SELECT * FROM vessel_action_history ORDER BY updated_at",
            connection
        )
    return df
