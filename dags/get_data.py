import datetime
import pendulum
import os
import pandas as pd
import sqlalchemy
import time
import csv
import urllib.request
import asyncio

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
from sqlalchemy.exc import SQLAlchemyError

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
        @asyncio.coroutine
        def get_csv():
            url_csv = fr'https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-regional-tr/exports/csv?lang=fr&refine=date_heure%3A%222024%22&facet=facet(name%3D%22libelle_region%22%2C%20disjunctive%3Dtrue)&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B'
            start = time.time()

            #response = urllib.request.urlopen(url_csv)
            #df = csv.reader(response, delimiter=';')
            df = pd.read_csv(url_csv, sep=';')
            end = time.time()
            print("difference: ", f"{(end - start) / 60}")
            return df
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(get_csv())
        return result

    @task()
    def transform(df):
        df.columns = df.columns.map(lambda x: x.lower().strip().replace("(", "").replace(")", "").replace(" %", "") \
                                    .replace(" - ", "_").replace(" ", "_"))
        df = df[['région', 'date_heure', 'thermique_mw', 'nucléaire_mw', 'eolien_mw', 'solaire_mw',
                'hydraulique_mw', 'pompage_mw', 'bioénergies_mw']]
        df.loc[:, "date_heure"] = pd.to_datetime(df["date_heure"])
        df.rename({'région': 'region'}, axis=1, inplace=True)
        df_normalized = pd.melt(df, id_vars=['date_heure', 'region'],
                                value_vars=['thermique_mw', 'nucléaire_mw', 'eolien_mw', 'solaire_mw',
                                            'hydraulique_mw', 'pompage_mw', 'bioénergies_mw'],
                                value_name='consommation',
                                var_name='filiere')
        return df_normalized
    @task()
    def load(data):
        engine = sqlalchemy.create_engine('postgresql+psycopg2://airflow:airflow@postgres:5432/airflow')
        create_schema_sql = """ CREATE SCHEMA IF NOT EXISTS energy"""
        engine.execute(create_schema_sql)

        try:
            engine.connect()
            data.to_sql(
                name='eco_to_mix',
                con=engine,
                schema='energy',
                if_exists='replace',
                index=False,
                method='multi',
                chunksize=5000,
            )
            engine.dispose()
            print(f"Storage of energy data completed !!!")

        except SQLAlchemyError as e:
            raise e
    df = extract_data()
    data = transform(df)
    load(data)

process_energy_data()

