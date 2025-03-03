from pathlib import Path, PurePath

import dash
import dash_bootstrap_components as dbc
import dotenv
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from dash import Input, Output, callback, dcc, html

from src.components import colors, sidebar, status_filter
from src.utils import scan_lists, schema

dash.register_page(__name__, path="/map", title=f"Membership Dashboard: {__name__.title()}", order=5)

config = dotenv.dotenv_values(Path(PurePath(__file__).parents[2], ".env"))

if "MAPBOX" in config:
    px.set_mapbox_access_token(config.get("MAPBOX"))

membership_map = html.Div(
    children=[
        dbc.Row(
            [
                status_filter.status_filter_col(),
                dbc.Col(
                    dcc.Dropdown(options=list(column for column in schema.schema.columns), value="membership_status", multi=False, id="selected-column"),
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
                        "height": "91svh",
                        "width": "100%",
                        "padding-left": "-1em",
                        "padding-right": "-1em",
                        "padding-bottom": "-1em",
                    },
                ),
            ),
        ),
    ],
)


def layout() -> dbc.Row:
    return dbc.Row([dbc.Col(sidebar.sidebar(), width=2), dbc.Col(membership_map, width=10)], className="dbc", style={"margin": "1em"})


@callback(
    Output(component_id="map", component_property="figure"),
    Input(component_id="list-selected", component_property="value"),
    Input(component_id="selected-column", component_property="value"),
    Input(component_id="status-filter", component_property="value"),
    Input(component_id="color-mode-switch", component_property="value"),
)
def create_map(date_selected: str, selected_column: str, selected_statuses: list[str], dark_mode: bool) -> px.scatter_mapbox:
    """Set up html data to show a map of Maine DSA members."""
    df_map = scan_lists.MEMB_LISTS.get(date_selected, pd.DataFrame())
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
        color_discrete_sequence=colors.COLORS,
        zoom=6,
        height=1100,
        mapbox_style="dark",
        template=pio.templates["darkly"],
    )

    if not dark_mode:
        map_figure.update_layout(mapbox_style="light", template=pio.templates["journal"])

    map_figure.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return map_figure
