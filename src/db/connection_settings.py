import os
import json
from pathlib import Path

import pymysql
import sqlalchemy
from google.cloud.sql.connector import Connector, IPTypes

import warnings

warnings.filterwarnings(
    "ignore",
    message="Your application has authenticated using end user credentials"
)

# --- Lazy-loaded settings ---
_settings = None

def get_settings():
    global _settings
    if _settings is None:
        json_file = Path(__file__).parents[2] / "settings.json"
        with open(json_file) as f:
            _settings = json.load(f)
    return _settings


# --- Connection singletons ---
connection_to_database = None
connection_to_historical = None
connection_to_analytics = None
connection_to_states = None


# --- Database connections ---
def connect_to_database() -> sqlalchemy.engine.base.Engine:
    global connection_to_database
    if connection_to_database is None:
        settings = get_settings()

        connector = Connector(enable_iam_auth=True)
        ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

        def get_connection() -> pymysql.connections.Connection:
            conn: pymysql.connections.Connection = connector.connect(
                settings["fishfacts_url"],
                "pymysql",
                user=settings["fishfacts_user"],
                db=settings["fishfacts_db"],
                ip_type=ip_type,
                timeout=10
            )
            return conn

        connection_to_database = sqlalchemy.create_engine(
            "mysql+pymysql://",
            creator=get_connection,
            pool_size=10,
            pool_reset_on_return=True,
            pool_pre_ping=True,
            pool_recycle=180
        )

    return connection_to_database


def connect_to_analytics() -> sqlalchemy.engine.base.Engine:
    global connection_to_analytics
    if connection_to_analytics is None:
        settings = get_settings()

        connection_string = (
            f"mssql+pymssql://{settings['seafacts_analytics_user']}:{settings['seafacts_analytics_password']}"
            f"@{settings['seafacts_analytics_url']}/{settings['seafacts_analytics_db']}?charset=utf8"
        )

        connection_to_analytics = sqlalchemy.create_engine(
            connection_string,
            pool_size=10,
            pool_reset_on_return=True,
            pool_pre_ping=True,
            pool_recycle=180
        )

    return connection_to_analytics


# TODO: should be replaced with BigQuery for all locations older than 100 days
def connect_to_historical() -> sqlalchemy.engine.base.Engine:
    global connection_to_historical
    if connection_to_historical is None:
        settings = get_settings()

        connector = Connector(enable_iam_auth=True)
        ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

        def get_connection() -> pymysql.connections.Connection:
            conn: pymysql.connections.Connection = connector.connect(
                settings["fishfacts_url"],
                "pymysql",
                user=settings["fishfacts_user"],
                db=settings["fishfacts_db"],
                ip_type=ip_type
            )
            return conn

        connection_to_historical = sqlalchemy.create_engine(
            "mysql+pymysql://",
            creator=get_connection,
            pool_size=10
        )

    return connection_to_historical
