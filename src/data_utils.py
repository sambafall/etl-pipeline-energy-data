import pandas as pd
import sqlalchemy

PRIMARY_KEY_COLUMNS = ["date_heure", "region", "filiere"]


def normalize_timestamp_to_utc(frame):
    """Ensure all timestamps are timezone-aware and normalised to UTC."""
    if frame is None:
        raise ValueError("A dataframe is required to normalize timestamps.")

    result = frame.copy()
    if result.empty:
        return result

    if "date_heure" not in result.columns:
        raise KeyError("The dataframe must contain a 'date_heure' column.")

    result["date_heure"] = pd.to_datetime(
        result["date_heure"],
        errors="raise",
        utc=True,
        format="mixed",
    )
    return result


def prepare_for_upsert(frame):
    """Normalize timestamps, trim text fields, and remove duplicates on the unique key."""
    if frame is None:
        raise ValueError("A dataframe is required to prepare the upsert rows.")

    result = normalize_timestamp_to_utc(frame)
    if result.empty:
        return result

    for column in ["region", "filiere"]:
        if column not in result.columns:
            raise KeyError(f"The dataframe must contain a '{column}' column.")

    result["region"] = result["region"].astype(str).str.strip()
    result["filiere"] = result["filiere"].astype(str).str.strip()

    if "consommation" in result.columns:
        result["consommation"] = pd.to_numeric(result["consommation"], errors="coerce")

    result = result.drop_duplicates(subset=PRIMARY_KEY_COLUMNS, keep="last")
    result = result.sort_values(PRIMARY_KEY_COLUMNS).reset_index(drop=True)
    return result


def create_target_table(engine, schema, table_name):
    """Create the target table with a composite primary key and readable history index."""
    table_ref = f"{schema}.{table_name}"
    create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_ref} (
            date_heure TIMESTAMPTZ NOT NULL,
            region TEXT NOT NULL,
            filiere TEXT NOT NULL,
            consommation DOUBLE PRECISION,
            PRIMARY KEY (date_heure, region, filiere)
        )
    """
    index_sql = f"CREATE INDEX IF NOT EXISTS idx_{table_name}_region_date_heure ON {table_ref} (region, date_heure);"

    with engine.begin() as conn:
        conn.execute(sqlalchemy.text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.execute(sqlalchemy.text(create_table_sql))
        conn.execute(sqlalchemy.text(index_sql))
