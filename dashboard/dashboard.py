# -*- coding: utf-8 -*-

import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
# from dash.dependencies import Input, Output, State
# from dash.exceptions import PreventUpdate
import plotly.express as px
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
import pandas as pd
import geopandas as gpd

external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

print("Loading data")
ardeche = pd.read_parquet(
    "https://object.files.data.gouv.fr/hydra-parquet/hydra-parquet/5b3c2cee-44b7-48bd-b4e8-439a03ff6cd2.parquet",
    columns=["Nom_du_POI", "Latitude", "Longitude", "Code_postal_et_commune"],
    filters=[("Code_postal_et_commune", ">", "07"), ("Code_postal_et_commune", "<", "08")],
)
fig = px.scatter_map(
    ardeche, lat="Latitude", lon="Longitude",
    hover_name="Nom_du_POI",
#     color="peak_hour", size="car_hours",
#     color_continuous_scale=px.colors.cyclical.IceFire, size_max=15, zoom=10
)

# %% APP LAYOUT:
app.layout = dbc.Container(
    [
        dbc.Row([
            html.H3(
                "Carto Ardèche",
                style={
                    "padding": "5px 0px 10px 0px",  # "padding": "top right down left"
                }),
        ]),
        dbc.Row([
            dcc.Graph(id="map", figure=fig),
        ]),
    ])

# %% Callbacks


# %%
if __name__ == '__main__':
    app.run(debug=False, use_reloader=False, port=8051)
