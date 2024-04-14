import dash
from dash import dcc, html
import plotly.express as px
import sqlalchemy
import pandas as pd


engine = sqlalchemy.create_engine('postgresql+psycopg2://airflow:airflow@postgres:5432/airflow')

query = f"""
        select
            *
        from
            energy.eco_to_mix
         """

df = pd.read_sql(query, con=engine)

df.rename({'région': 'region'}, axis=1, inplace=True)

# Application
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
                external_stylesheets=external_stylesheets)

server = app.server

colors = {
    'background': '#FFFFF',
    'text': '#082255'
}

app.layout = html.Div(
    #style={'backgroundColor': colors['background']},
    children=[
    html.H1(children='Real-time consumption and production by region and sector', style={'textAlign':'center'}),
    dcc.Dropdown(df.region.unique(), 'Auvergne-Rhône-Alpes', id='dropdown-selection'),
    dcc.Graph(id='graph-content')
])


@app.callback(
    dash.dependencies.Output('graph-content', 'figure'),
    dash.dependencies.Input('dropdown-selection', 'value')
)
def update_graph(value):
    dff = df[df.region == value]
    return px.area(dff, x="date_heure", y="consommation", color="filiere")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0',port=8000, dev_tools_hot_reload=True)
