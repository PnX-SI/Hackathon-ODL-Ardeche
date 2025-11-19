# -*- coding: utf-8 -*-
import json

import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
# from dash.exceptions import PreventUpdate
import plotly
import plotly.express as px
import plotly.graph_objects as go
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
compteur = pd.read_csv("data/ecocompteur.csv")
available_months = sorted(compteur["time"].str.slice(0,7).unique())
with open("data/coords.json") as f:
    sites = json.load(f)

def month_label(month: str):
    mapping: dict[str, str] = {
        "01": "janvier",
        "02": "février",
        "03": "mars",
        "04": "avril",
        "05": "mai",
        "06": "juin",
        "07": "juillet",
        "08": "août",
        "09": "septembre",
        "10": "octobre",
        "11": "novembre",
        "12": "décembre",
    }
    year, m = month.split("-")
    return f"{mapping[m]} {year}"


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
            html.H6("Mois de début et de fin"),
            dcc.RangeSlider(
                min=0,
                max=len(available_months) - 1,
                step=1,
                value=[0, len(available_months) - 1],
                id="months_slider",
                marks={
                    k: month_label(available_months[k])
                    for k in range(0, len(available_months), 18)
                } | {len(available_months) - 1: month_label(available_months[-1])},
            ),
        ]),
        dbc.Row([
            dcc.Graph(id="map"),
        ]),
    ])

# %% Callbacks
@dash.callback(
    Output("map", "figure"),
    [Input("months_slider", "value")],
)
def update_map(months_idx: tuple[int, int]):
    mmin, mmax = months_idx
    restr = compteur.loc[
        compteur["month"].between(available_months[mmin], available_months[mmax])
    ]
    stats = restr.groupby("site")["count"].sum().reset_index()
    for coord in ["lat", "lon"]:
        stats[coord] = stats["site"].apply(lambda lab: sites[lab][coord])
    stats["label"] = stats["site"].apply(lambda lab: sites[lab]["label"])
    fig = px.scatter_map(
        stats,
        lat="lat",
        lon="lon",
        hover_name="label",
        size="count",
    )
    fig.add_trace(
        go.Scattermap(
            lon = ardeche["Longitude"],
            lat = ardeche["Latitude"],
            text = ardeche['Nom_du_POI'],
            mode="markers",
            marker=go.scattermap.Marker(size=6, color="red"),
        )
    )
    fig.update_layout(showlegend=False)
    return fig


# %%
if __name__ == '__main__':
    app.run(debug=False, use_reloader=False, port=8051)
