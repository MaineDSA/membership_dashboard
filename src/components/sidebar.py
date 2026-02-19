import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from src.utils.scan_lists import MEMB_LISTS

member_list_keys = list(MEMB_LISTS.keys())


def sidebar() -> html.Div:
    return html.Div(
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        html.Img(
                            src="/assets/favicon.svg",
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
            ),
            dbc.Row(
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Hr(),
                                html.P("Membership Dashboard", className="lead"),
                            ],
                        ),
                        dcc.Dropdown(
                            options=member_list_keys,
                            value=member_list_keys[0],
                            id="list-selected",
                            persistence=True,
                            persistence_type="session",
                        ),
                        html.Div(
                            [
                                html.P("Active List"),
                            ],
                        ),
                        dcc.Dropdown(
                            options=member_list_keys,
                            id="list-compare",
                            persistence=True,
                            persistence_type="session",
                        ),
                        html.Div(
                            [
                                html.P("Compare To"),
                            ],
                        ),
                        dbc.Nav(
                            [
                                dbc.NavLink(
                                    html.Div(page["name"], className="ms-2"),
                                    href=page["path"],
                                    active="exact",
                                )
                                for page in dash.page_registry.values()
                            ],
                            vertical=True,
                            pills=True,
                        ),
                    ]
                ),
            ),
        ],
    )
