"""Components for a membership dashboard showing various graphs and metrics to illustrate changes over time."""

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import (
    dash_table,
    dcc,
    html,
)


def layout(memb_list_keys: list[str]) -> dbc.Container:
    def sidebar_header() -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(
                    html.Img(
                        src="https://www.mainedsa.org/wp-content/uploads/2023/07/Maine-DSA-Moose-with-Rose-Logo.svg",
                        alt="Red Maine DSA logo of a moose holding a rose in its mouth under the text Maine DSA",
                    ),
                    align="center",
                ),
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(dbc.Label(className="fa fa-sun", html_for="color-mode-switch")),
                                dbc.Col(
                                    dbc.Switch(
                                        id="color-mode-switch",
                                        value=True,
                                        className="d-inline-block ms-1",
                                        persistence=True,
                                    )
                                ),
                                dbc.Col(dbc.Label(className="fa fa-moon", html_for="color-mode-switch")),
                            ],
                            className="g-0",
                        )
                    ],
                    width="auto",
                    align="center",
                ),
            ]
        )

    def sidebar() -> html.Div:
        return html.Div(
            id="sidebar",
            children=[
                sidebar_header(),
                # we wrap the horizontal rule and short blurb in a div that can be hidden on a small screen
                html.Div(
                    [
                        html.Hr(),
                        html.P("Membership Dasboard", className="lead"),
                    ],
                    id="blurb",
                ),
                dcc.Dropdown(
                    options=memb_list_keys,
                    value=memb_list_keys[0],
                    id="list_dropdown",
                ),
                html.Div(
                    [
                        html.P("Active List"),
                    ],
                    id="list_dropdown_label",
                ),
                dcc.Dropdown(
                    options=memb_list_keys,
                    id="list_compare_dropdown",
                ),
                html.Div(
                    [
                        html.P("Compare To"),
                    ],
                    id="list_compare_dropdown_label",
                ),
                dbc.Nav(
                    [
                        dbc.NavLink("Timeline", href="/", active="exact"),
                        dbc.NavLink("List", href="/list", active="exact"),
                        dbc.NavLink("Metrics", href="/metrics", active="exact"),
                        dbc.NavLink("Graphs", href="/graphs", active="exact"),
                        dbc.NavLink("Map", href="/map", active="exact"),
                    ],
                    id="navigation",
                    vertical=True,
                    pills=True,
                ),
            ],
        )

    return dbc.Container([dcc.Location(id="url"), sidebar(), html.Div(id="page-content")], className="dbc dbc-ag-grid", fluid=True)


def timeline(memb_lists_metrics_keys: list[str]) -> html.Div:
    return html.Div(
        id="timeline-container",
        children=[
            dcc.Dropdown(
                options=memb_lists_metrics_keys,
                value=["membership_status"],
                multi=True,
                id="timeline_columns",
            ),
            dcc.Graph(
                figure={},
                id="membership_timeline",
                style={
                    "display": "inline-block",
                    "height": "85vh",
                    "width": "100%",
                    "padding-left": "-1em",
                    "padding-right": "-1em",
                    "padding-bottom": "-1em",
                },
            ),
        ],
    )


def member_list(memb_lists: dict) -> html.Div:
    memb_list_keys = list(memb_lists.keys())
    return html.Div(
        id="list-container",
        children=[
            dash_table.DataTable(
                data=memb_lists[memb_list_keys[0]].to_dict("records"),
                columns=[{"name": i, "id": i, "selectable": True} for i in memb_lists[list(memb_lists.keys())[0]].columns],
                sort_action="native",
                sort_by=[
                    {"column_id": "last_name", "direction": "asc"},
                    {"column_id": "first_name", "direction": "asc"},
                ],
                filter_action="native",
                filter_options={"case": "insensitive"},
                export_format="csv",
                page_size=20,
                style_table={
                    "display": "inline-block",
                    "height": "80vh",
                    "overflowY": "auto",
                    "overflowX": "auto",
                },
                id="membership_list",
            ),
        ],
    )


def metrics() -> html.Div:
    return html.Div(
        id="metrics-container",
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(
                            figure=go.Figure(),
                            id="members_lifetime",
                            style={"height": "30vh"},
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        dcc.Graph(figure=go.Figure(), id="members_migs", style={"height": "30vh"}),
                        width=6,
                    ),
                ],
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(
                            figure=go.Figure(),
                            id="members_expiring",
                            style={"height": "30vh"},
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        dcc.Graph(
                            figure=go.Figure(),
                            id="members_lapsed",
                            style={"height": "30vh"},
                        ),
                        width=6,
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(
                            figure=go.Figure(),
                            id="metric_retention",
                            style={"height": "30vh"},
                        ),
                        width=6,
                    ),
                ]
            ),
        ],
    )


def graphs() -> html.Div:
    return html.Div(
        id="graphs-container",
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(
                            figure=go.Figure(),
                            id="membership_status",
                            style={"height": "46vh"},
                        ),
                        md=4,
                    ),
                    dbc.Col(
                        dcc.Graph(
                            figure=go.Figure(),
                            id="membership_type",
                            style={"height": "46vh"},
                        ),
                        md=4,
                    ),
                    dbc.Col(
                        dcc.Graph(figure=go.Figure(), id="union_member", style={"height": "46vh"}),
                        md=4,
                    ),
                ],
                align="center",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(
                            figure=go.Figure(),
                            id="membership_length",
                            style={"height": "46vh"},
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dcc.Graph(figure=go.Figure(), id="race", style={"height": "46vh"}),
                        md=6,
                    ),
                ],
                align="center",
            ),
        ],
    )


def member_map(memb_lists_metrics_keys: list[str]) -> html.Div:
    return html.Div(
        id="map-container",
        children=[
            dcc.Dropdown(
                options=memb_lists_metrics_keys,
                value="membership_status",
                multi=False,
                id="map_column",
            ),
            dcc.Graph(
                figure=go.Figure(),
                id="membership_map",
                style={
                    "display": "inline-block",
                    "height": "85vh",
                    "width": "100%",
                    "padding-left": "-1em",
                    "padding-right": "-1em",
                    "padding-bottom": "-1em",
                },
            ),
        ],
    )
