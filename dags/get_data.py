import datetime
import os
import time

import pandas as pd
import pendulum
import sqlalchemy
from airflow.decorators import dag, task
from sqlalchemy.exc import SQLAlchemyError

from config.constants import (
    DB_SCHEMA,
    DB_TABLE,
    ECO2MIX_API_BASE_URL,
    ECO2MIX_API_PARAMS,
    ENERGY_SOURCES,
    MIN_ROWS_THRESHOLD,
    RAW_COLUMNS,
    RENEWABLE_SOURCES,
)
from src.data_utils import create_target_table, prepare_for_upsert


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
    schedule_interval="0 * * * *",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=datetime.timedelta(minutes=60),
    default_args={
        "retries": 3,
        "retry_delay": datetime.timedelta(minutes=5),
    },
)
def process_energy_data():
    @task()
    def extract_data():
        """Extract energy data from the ECO2MIX API."""
        url_csv = build_api_url()
        start = time.time()

        df = pd.read_csv(url_csv, sep=";")
        elapsed_minutes = (time.time() - start) / 60
        print(f"Data extraction completed in {elapsed_minutes:.2f} minutes")

        if len(df) < MIN_ROWS_THRESHOLD:
            raise ValueError(
                f"Insufficient data: received {len(df)} rows, "
                f"expected at least {MIN_ROWS_THRESHOLD}"
            )

        return df

    @task()
    def transform(df):
        """Transform raw energy data into normalized format."""
        df = df.copy()
        df.columns = df.columns.map(normalize_column_names)
        df = df[RAW_COLUMNS].copy()
        df.rename(columns={"région": "region"}, inplace=True)
        df["date_heure"] = pd.to_datetime(df["date_heure"], errors="raise", utc=True)
        df_normalized = pd.melt(
            df,
            id_vars=["date_heure", "region"],
            value_vars=ENERGY_SOURCES,
            value_name="consommation",
            var_name="filiere",
        )
        df_normalized = df_normalized.loc[
            df_normalized["filiere"].isin(RENEWABLE_SOURCES), :
        ]
        return df_normalized

    @task()
    def load(data):
        """Load transformed data into PostgreSQL with an upsert against the primary key."""
        db_url = os.getenv(
            "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN",
            "postgresql+psycopg2://airflow:airflow@postgres:5432/airflow",
        )
        engine = sqlalchemy.create_engine(db_url)

        try:
            create_target_table(engine, DB_SCHEMA, DB_TABLE)
            prepared_data = prepare_for_upsert(data)

            if prepared_data.empty:
                raise ValueError("No rows available after normalization and duplicate removal.")

            staging_table = f"{DB_TABLE}_staging"
            target_table = f"{DB_SCHEMA}.{DB_TABLE}"
            staging_ref = f"{DB_SCHEMA}.{staging_table}"

            with engine.begin() as conn:
                conn.execute(sqlalchemy.text(f"DROP TABLE IF EXISTS {staging_ref}"))
                prepared_data.to_sql(
                    name=staging_table,
                    con=conn,
                    schema=DB_SCHEMA,
                    if_exists="replace",
                    index=False,
                    method="multi",
                    chunksize=1000,
                )

                existing_matches = conn.execute(
                    sqlalchemy.text(
                        f"""
                        SELECT COUNT(*)
                        FROM {target_table}
                        WHERE (date_heure, region, filiere)
                            IN (SELECT date_heure, region, filiere FROM {staging_ref})
                        """
                    )
                ).scalar()

                rows_affected = conn.execute(
                    sqlalchemy.text(
                        f"""
                        INSERT INTO {target_table} (date_heure, region, filiere, consommation)
                        SELECT date_heure, region, filiere, consommation
                        FROM {staging_ref}
                        ON CONFLICT (date_heure, region, filiere)
                        DO UPDATE SET consommation = EXCLUDED.consommation
                        """
                    )
                ).rowcount

                conn.execute(sqlalchemy.text(f"DROP TABLE IF EXISTS {staging_ref}"))

            inserted_rows = len(prepared_data) - int(existing_matches or 0)
            updated_rows = int(existing_matches or 0)
            print(
                f"Upserted {len(prepared_data)} rows into {target_table}: "
                f"{inserted_rows} inserted, {updated_rows} updated."
            )

        except SQLAlchemyError as exc:
            raise exc
        finally:
            engine.dispose()

    df = extract_data()
    data = transform(df)
    load(data)


process_energy_data()
