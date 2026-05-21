import os
import dash
from dash import dcc, html
import plotly.express as px
import sqlalchemy
import pandas as pd

from config.constants import DB_SCHEMA, DB_TABLE

# Database configuration
DB_URL = os.getenv(
    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN",
    "postgresql+psycopg2://airflow:airflow@postgres:5432/airflow",
)
engine = sqlalchemy.create_engine(DB_URL)

# Query data from database
query = f"""
    SELECT *
    FROM {DB_SCHEMA}.{DB_TABLE}
    ORDER BY date_heure DESC
"""

df = pd.read_sql(query, con=engine)

# Rename column for consistency
df.rename({"région": "region"}, axis=1, inplace=True)

# Application initialization
external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=external_stylesheets,
)

server = app.server

# Color theme
colors = {"background": "#FFFFFF", "text": "#082255"}

# Application layout
app.layout = html.Div(
    children=[
        html.H1(
            children="Real-time Renewable Energy Consumption and Production by Region",
            style={"textAlign": "center", "color": colors["text"]},
        ),
        dcc.Dropdown(
            df.region.unique(),
            df.region.unique()[0],  # Default to first region
            id="dropdown-selection",
        ),
        dcc.Graph(id="graph-content"),
    ]
)


@app.callback(
    dash.dependencies.Output("graph-content", "figure"),
    dash.dependencies.Input("dropdown-selection", "value"),
)
def update_graph(selected_region):
    """Update graph based on selected region."""
    filtered_df = df[df.region == selected_region]
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
