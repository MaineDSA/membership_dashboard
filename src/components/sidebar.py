from datetime import date

import dash
import dash_bootstrap_components._components as dbc
from dash import Input, Output, callback, dcc, html

from src.utils import scan_lists

member_list_keys = list(scan_lists.MEMB_LISTS.keys())


def sidebar(*, compare: bool = True) -> html.Div:
    return html.Div(
        style={
            "display": "flex",
            "flexDirection": "column",
            "height": "100vh",
            "padding-left": "0rem",
            "padding-bottom": "1rem",
        },
        children=[
            html.Div(
                style={
                    "flex": "1 1 auto",
                    "overflow-x": "clip",
                    "overflow-y": "auto",
                },
                children=[
                    dbc.Row(
                        children=[
                            dbc.Col(
                                html.Img(
                                    src="/assets/favicon.svg",
                                    alt="Red logo of a moose holding a rose in its mouth under the text Maine DSA",
                                ),
                                align="center",
                            ),
                            dbc.Col(
                                dbc.Row(
                                    children=[
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
                                ),
                                width="auto",
                                align="center",
                            ),
                        ],
                        id="header",
                    ),
                    dbc.Row(
                        children=[
                            dbc.Col(
                                children=[
                                    html.Hr(),
                                    html.Div(
                                        html.P("Membership Dashboard", className="lead"),
                                        id="title",
                                    ),
                                    dbc.Nav(
                                        children=[
                                            dbc.NavLink(
                                                html.Div(page["name"], className="ms-2"),
                                                href=page["path"],
                                                active="exact",
                                            )
                                            for page in dash.page_registry.values()
                                        ],
                                        id="navigation",
                                        vertical=True,
                                        pills=True,
                                    ),
                                ]
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                children=[
                    html.Hr(),
                    html.Div(
                        children=[
                            html.Div(
                                children=[
                                    dcc.Dropdown(
                                        options=member_list_keys,
                                        value=member_list_keys[0],
                                        id="list-selected",
                                        persistence=True,
                                        persistence_type="session",
                                    ),
                                    html.Div(html.P("Active List")),
                                ],
                                id="list-selector",
                            ),
                            html.Div(
                                style={"display": "none" if not compare else "block"},
                                children=[
                                    dcc.Dropdown(
                                        id="list-compare",
                                        persistence=True,
                                        persistence_type="session",
                                    ),
                                    html.Div(html.P("Compare To")),
                                ],
                                id="list-selector-compare",
                            ),
                        ],
                        id="list-selectors",
                    ),
                ]
            ),
        ],
    )


@callback(Output("list-compare", "options"), Input("list-selected", "value"))
def update_compare_options(selected_list: scan_lists.ISODateStr) -> list[scan_lists.ISODateStr] | list[None]:
    if not selected_list:
        return []

    selected_date = date.fromisoformat(selected_list)
    return [key for key in member_list_keys if date.fromisoformat(key) < selected_date]
