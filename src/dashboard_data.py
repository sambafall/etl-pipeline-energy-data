from datetime import datetime, timedelta


def build_history_query(table_name, region=None, start_date=None, end_date=None, aggregate_hours=False):
    """Build a PostgreSQL query with optional region/date filters and optional hourly aggregation."""
    conditions = []
    if region:
        conditions.append(f"region = '{region}'")
    if start_date:
        conditions.append(f"date_heure >= '{start_date}'")
    if end_date:
        conditions.append(f"date_heure < '{end_date}'")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    if aggregate_hours:
        return f"""
            SELECT
                date_trunc('hour', date_heure) AS date_heure,
                region,
                filiere,
                AVG(consommation) AS consommation
            FROM {table_name}
            {where_clause}
            GROUP BY date_trunc('hour', date_heure), region, filiere
            ORDER BY date_heure ASC, region ASC, filiere ASC
        """

    return f"""
        SELECT
            region,
            date_heure,
            filiere,
            consommation
        FROM {table_name}
        {where_clause}
        ORDER BY date_heure ASC, region ASC, filiere ASC
    """


def get_period_bounds(period_value="7d", end_time=None):
    """Return a start/end window for a dashboard period selector."""
    if end_time is None:
        end_time = datetime.utcnow()

    mapping = {"24h": 1, "7d": 7, "30d": 30}
    days = mapping.get(period_value, 7)
    start_time = end_time - timedelta(days=days)
    return start_time, end_time
