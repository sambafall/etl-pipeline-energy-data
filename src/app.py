import os
from datetime import datetime

import dash
import pandas as pd
import plotly.express as px
import sqlalchemy
from dash import Input, Output, dcc, html

from config.constants import DB_SCHEMA, DB_TABLE
from src.dashboard_data import build_history_query, get_period_bounds

DB_URL = os.getenv(
    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN",
    "postgresql+psycopg2://airflow:airflow@postgres:5432/airflow",
)
engine = sqlalchemy.create_engine(DB_URL)

PERIOD_OPTIONS = [
    {"label": "Last 24h", "value": "24h"},
    {"label": "Last 7 days", "value": "7d"},
    {"label": "Last 30 days", "value": "30d"},
]


def fetch_regions():
    query = f"SELECT DISTINCT region FROM {DB_SCHEMA}.{DB_TABLE} ORDER BY region"
    with engine.connect() as conn:
        result = pd.read_sql(sqlalchemy.text(query), conn)
    return result["region"].tolist()


def fetch_history(selected_region=None, period_value="7d"):
    start_time, end_time = get_period_bounds(period_value, datetime.utcnow())
    aggregate = period_value == "30d"
    query = build_history_query(
        f"{DB_SCHEMA}.{DB_TABLE}",
        region=selected_region,
        start_date=start_time.isoformat(),
        end_date=end_time.isoformat(),
        aggregate_hours=aggregate,
    )
    with engine.connect() as conn:
        return pd.read_sql(sqlalchemy.text(query), conn)


external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=external_stylesheets,
)
server = app.server
colors = {"background": "#FFFFFF", "text": "#082255"}

try:
    regions = fetch_regions()
except Exception:
    regions = []
initial_region = regions[0] if regions else None

app.layout = html.Div(
    children=[
        html.H1(
            children="Renewable Energy Consumption and Production by Region",
            style={"textAlign": "center", "color": colors["text"]},
        ),
        html.Div(
            [
                dcc.Dropdown(
                    regions,
                    initial_region,
                    id="dropdown-selection",
                    clearable=False,
                ),
                dcc.Dropdown(
                    PERIOD_OPTIONS,
                    "7d",
                    id="period-selector",
                    clearable=False,
                ),
            ],
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"},
        ),
        dcc.Interval(id="refresh-interval", interval=60 * 60 * 1000, n_intervals=0),
        dcc.Graph(id="graph-content"),
    ]
)


@app.callback(
    Output("graph-content", "figure"),
    Input("dropdown-selection", "value"),
    Input("period-selector", "value"),
    Input("refresh-interval", "n_intervals"),
)
def update_graph(selected_region, selected_period, _n_intervals):
    """Refresh the area chart based on the selected region and period."""
    if not selected_region:
        return px.area(title="No region selected")

    try:
        filtered_df = fetch_history(selected_region=selected_region, period_value=selected_period)
    except Exception:
        return px.area(title="Unable to load the latest energy history")

    if filtered_df.empty:
        return px.area(title=f"No data available for {selected_region} in the selected period")

    return px.area(
        filtered_df,
        x="date_heure",
        y="consommation",
        color="filiere",
        title=f"Energy Production in {selected_region}",
        labels={
            "date_heure": "Date and Time",
            "consommation": "Production (MW)",
            "filiere": "Energy Source",
        },
    )


if __name__ == "__main__":
    debug_mode = os.getenv("DASH_DEBUG", "False").lower() == "true"
    app.run(
        debug=debug_mode,
        host=os.getenv("DASH_HOST", "0.0.0.0"),
        port=int(os.getenv("DASH_PORT", 8000)),
        dev_tools_hot_reload=debug_mode,
    )
