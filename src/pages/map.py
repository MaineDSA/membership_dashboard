import os
from pathlib import Path, PurePath

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from components.colors import COLORS
from components.sidebar import sidebar
from components.status_filter import status_filter_col
from dash import Input, Output, callback, dcc, html
from utils.scan_lists import MEMB_LISTS
from utils.schema import schema

dash.register_page(__name__, path="/map", title=f"Membership Dashboard: {__name__.title()}", order=5)

MAPBOX_TOKEN_PATH = Path(PurePath(os.getcwd()).parent, ".mapbox_token")
if MAPBOX_TOKEN_PATH.is_file():
    px.set_mapbox_access_token(MAPBOX_TOKEN_PATH.read_text(encoding="UTF-8"))

membership_map = html.Div(
    children=[
        dbc.Row(
            [
                status_filter_col(),
                dbc.Col(
                    dcc.Dropdown(
                        options=list(column for column in schema.columns), value="membership_status", multi=False, id="selected-column", className="dbc"
                    ),
                ),
            ],
            align="center",
        ),
        dbc.Row(
            dbc.Col(
                dcc.Graph(
                    figure=go.Figure(),
                    id="map",
                    style={
                        "display": "inline-block",
                        "height": "85svh",
                        "width": "100%",
                        "padding-left": "-1em",
                        "padding-right": "-1em",
                        "padding-bottom": "-1em",
                    },
                    className="dbc",
                ),
            ),
        ),
    ],
)


def layout():
    return dbc.Row([dbc.Col(sidebar(), width=2), dbc.Col(membership_map, width=10)])


@callback(
    Output(component_id="map", component_property="figure"),
    Input(component_id="list-selected", component_property="value"),
    Input(component_id="selected-column", component_property="value"),
    Input(component_id="status-filter", component_property="value"),
    Input(component_id="color-mode-switch", component_property="value"),
)
def create_map(date_selected: str, selected_column: str, selected_statuses: list[str], dark_mode: bool) -> px.scatter_mapbox:
    """Set up html data to show a map of Maine DSA members."""
    df_map = MEMB_LISTS.get(date_selected, pd.DataFrame())
    df_map = df_map.loc[df_map["membership_status"].isin(selected_statuses)]

    map_figure = px.scatter_mapbox(
        df_map.reset_index(drop=False),
        lat="lat",
        lon="lon",
        hover_name="actionkit_id",
        hover_data={
            "first_name": True,
            "last_name": True,
            "best_phone": True,
            "email": True,
            "membership_type": True,
            "membership_status": True,
            "membership_length_years": True,
            "join_date": True,
            "xdate": True,
            "lat": False,
            "lon": False,
        },
        color=selected_column,
        color_discrete_sequence=COLORS,
        zoom=6,
        height=1100,
        mapbox_style="dark",
        template=pio.templates["darkly"],
    )

    if not dark_mode:
        map_figure.update_layout(mapbox_style="light", template=pio.templates["journal"])

    map_figure.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return map_figure