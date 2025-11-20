# -*- coding: utf-8 -*-
from os import truncate
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

data_folder = "/".join(__file__.split("/")[:-2]) + "/data/"

external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Ardashboard"

print("Loading data")
biodiv = gpd.read_file(data_folder + "biodiv_agg.geojson")
biodiv["annee_mois"] = biodiv.apply(
    lambda df: f"{df['year_date']}-{'0' + str(month) if (month := df['year_month']) < 10 else month}",
    axis=1,
)
available_months = sorted(biodiv["annee_mois"].unique())
intersect_file = data_folder + "biodiv_intersects.parquet"

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


def flatten_with_none(list_of_lists_of_coords: list[list[float]]) -> list[float | None]:
    result = []
    for sublist in list_of_lists_of_coords:
        result.extend(sublist)
        result.append(None)
    return result[:-1]  # pop last None


def get_coords(geom):
    if geom.geom_type == 'Polygon':
        return list(geom.exterior.coords.xy)
    elif geom.geom_type == 'MultiPolygon':
        # For MultiPolygon, return the exterior of the first Polygon (or handle as needed)
        return list(geom.geoms[0].exterior.coords.xy)
    else:
        return [[], []]


def build_figure(gdf: gpd.GeoDataFrame, intersect: gpd.GeoDataFrame):
    def _build_scattermap(gdf, **kwargs):
        gdf_exploded = gdf.explode(index_parts=False)
        gdf_exploded['lon'], gdf_exploded['lat'] = zip(*gdf_exploded['geometry'].apply(get_coords))
        lon = flatten_with_none([[l for l in gdf_exploded["lon"]][k].tolist() for k in range(len(gdf_exploded))])
        labels = []
        idx = 0
        for k in range(len(lon)):
            if lon[k] is None:
                idx += 1
            labels.append(gdf_exploded["nom_valide"].iloc[gdf_exploded.index[idx]])
        return go.Scattermap(
            mode = "lines",
            lon = lon,
            lat = flatten_with_none([[l for l in gdf_exploded["lat"]][k].tolist() for k in range(len(gdf_exploded))]),
            text= labels,
            **kwargs,
        )

    print("Creating figure")
    fig = go.Figure(_build_scattermap(gdf, **{"fill": "toself"}))
    print("Adding trace")
    # only a subset here because it's so slow
    fig.add_trace(_build_scattermap(intersect[:min(3000, len(intersect))], **{"marker": {"size": 5, "color": 'red'}}))
    fig.update_layout(
        map = {'style': "open-street-map", 'center': {'lon': 4.594, 'lat': 44.364}, 'zoom': 10},
        showlegend = False,
        margin = {'l':0, 'r':0, 'b':0, 't':0})
    return fig


# %% APP LAYOUT:
app.layout = dbc.Container(
    [
        dbc.Row([
            html.H3(
                "Espèces sensibles en Ardèche",
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
                    for k in range(0, len(available_months), 9)
                } | {len(available_months) - 1: month_label(available_months[-1])},
            ),
        ]),
        dbc.Row([
            html.H6("Espèce d'intérêt"),
            dcc.Dropdown(
                id="species",
                options=[
                    {
                        "label": espece,
                        "value": espece,
                    }
                    for espece in biodiv["nom_valide"].unique()
                ]
            ),
        ]),
        dbc.Row([
            html.H6("Comportement"),
            dcc.Dropdown(
                id="behaviour",
                options=[
                    {
                        "label": behaviour,
                        "value": behaviour,
                    }
                    for behaviour in biodiv["behaviour"].unique()
                ]
            ),
        ]),
        dbc.Row([
            html.H6("Niveau de sensibilité"),
            dcc.Dropdown(
                id="sensibility",
                options=[
                    {
                        "label": sensibility,
                        "value": sensibility,
                    }
                    for sensibility in biodiv["niveau_sensibilite"].unique()
                ]
            ),
        ]),
        dbc.Row([
            html.H6("Âge des individus"),
            dcc.Dropdown(
                id="species_age",
                options=[
                    {
                        "label": species_age,
                        "value": species_age,
                    }
                    for species_age in biodiv["species_age"].unique()
                ]
            ),
        ]),
        dbc.Row([
            dcc.Graph(id="map"),
        ],
            style={"padding": "15px 0px 5px 0px"},
        ),
    ])


# %% Callbacks
@dash.callback(
    Output("map", "figure"),
    [
        Input("months_slider", "value"),
        Input("species", "value"),
        Input("behaviour", "value"),
        Input("sensibility", "value"),
        Input("species_age", "value"),
    ],
)
def update_map(
    months_idx: tuple[int, int], species: str, behaviour: str, sensibility: str, species_age: str,
):
    filters = []
    mmin, mmax = months_idx
    restr = biodiv.loc[
        (biodiv["annee_mois"].between(available_months[mmin], available_months[mmax]))
    ]
    if species is not None:
        restr = restr.loc[restr["nom_valide"] == species]
        filters.append(("nom_valide", "=", species))
    if behaviour is not None:
        restr = restr.loc[restr["behaviour"] == behaviour]
        filters.append(("behaviour", "=", behaviour))
    if sensibility is not None:
        restr = restr.loc[restr["niveau_sensibilite"] == sensibility]
        filters.append(("niveau_sensibilite", "=", sensibility))
    if species_age is not None:
        restr = restr.loc[restr["species_age"] == species_age]
        filters.append(("species_age", "=", species_age))
    intersect = gpd.read_parquet(
        intersect_file,
        filters=filters or None,
    )
    return build_figure(restr.reset_index(drop=True), intersect)


# %%
if __name__ == '__main__':
    app.run(debug=False, use_reloader=False, port=8051)
