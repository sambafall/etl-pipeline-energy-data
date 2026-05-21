import datetime
import pendulum
import os
import pandas as pd
import sqlalchemy
import time

from airflow.decorators import dag, task
from sqlalchemy.exc import SQLAlchemyError
from config.constants import (
    ENERGY_SOURCES,
    RENEWABLE_SOURCES,
    RAW_COLUMNS,
    DB_SCHEMA,
    DB_TABLE,
    ECO2MIX_API_BASE_URL,
    ECO2MIX_API_PARAMS,
    MIN_ROWS_THRESHOLD,
)


def build_api_url():
    """Construct the API URL with query parameters."""
    params = "&".join([f"{k}={v}" for k, v in ECO2MIX_API_PARAMS.items()])
    return f"{ECO2MIX_API_BASE_URL}?{params}"


def normalize_column_names(col_name):
    """Normalize column names to lowercase with underscores."""
    return (
        col_name.lower()
        .strip()
        .replace("(", "")
        .replace(")", "")
        .replace(" %", "")
        .replace(" - ", "_")
        .replace(" ", "_")
    )


@dag(
    dag_id="process-energy",
    schedule_interval="0 0 * * *",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
)
def process_energy_data():
    @task()
    def extract_data():
        """Extract energy data from the ECO2MIX API."""
        url_csv = build_api_url()
        start = time.time()

        df = pd.read_csv(url_csv, sep=";")
        end = time.time()
        
        elapsed_minutes = (end - start) / 60
        print(f"Data extraction completed in {elapsed_minutes:.2f} minutes")
        
        # Validate minimum data threshold
        if len(df) < MIN_ROWS_THRESHOLD:
            raise ValueError(
                f"Insufficient data: received {len(df)} rows, "
                f"expected at least {MIN_ROWS_THRESHOLD}"
            )
        
        return df

    @task()
    def transform(df):
        """Transform raw energy data into normalized format."""
        # Normalize column names
        df.columns = df.columns.map(normalize_column_names)
        
        # Select required columns
        df = df[RAW_COLUMNS]
        
        # Convert date column to datetime
        df.loc[:, "date_heure"] = pd.to_datetime(df["date_heure"])
        
        # Rename région to region for consistency
        df.rename({"région": "region"}, axis=1, inplace=True)
        
        # Normalize data: unpivot energy sources into a single column
        df_normalized = pd.melt(
            df,
            id_vars=["date_heure", "region"],
            value_vars=ENERGY_SOURCES,
            value_name="consommation",
            var_name="filiere",
        )
        
        # Filter to renewable sources only
        df_normalized = df_normalized.loc[
            df_normalized["filiere"].isin(RENEWABLE_SOURCES), :
        ]
        
        return df_normalized

    @task()
    def load(data):
        """Load transformed data into PostgreSQL database."""
        db_url = os.getenv(
            "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN",
            "postgresql+psycopg2://airflow:airflow@postgres:5432/airflow",
        )
        engine = sqlalchemy.create_engine(db_url)

        try:
            # Create schema if it doesn't exist
            with engine.connect() as conn:
                conn.execute(
                    sqlalchemy.text(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}")
                )
                conn.commit()

            # Load data into database
            data.to_sql(
                name=DB_TABLE,
                con=engine,
                schema=DB_SCHEMA,
                if_exists="replace",
                index=False,
                method="multi",
                chunksize=100000,
            )
            
            print(f"Storage of energy data completed to {DB_SCHEMA}.{DB_TABLE}!")

        except SQLAlchemyError as e:
            raise e
        finally:
            engine.dispose()

    # DAG workflow
    df = extract_data()
    data = transform(df)
    load(data)


process_energy_data()
