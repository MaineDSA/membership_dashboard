import os

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from src.utils import scan_lists


def sidebar() -> html.Div:
    member_list_keys = list(scan_lists.MEMB_LISTS.keys())

    periscope_url = os.getenv("PERISCOPE_URL")
    periscope_pass = os.getenv("PERISCOPE_PASS")
    is_disabled = not (periscope_url and periscope_pass)

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
                                className="g-0 justify-content-center",
                            ),
                            dbc.Row(
                                dbc.Col(
                                    [
                                        html.Span(
                                            [
                                                dbc.Button(
                                                    "Fetch New List",
                                                    id="fetch-list-button",
                                                    size="sm",
                                                    className="mt-1 w-100",
                                                    disabled=is_disabled,
                                                ),
                                                html.Small(id="fetch-list-status", className="text-muted"),
                                                dcc.Interval(id="fetch-list-poll", interval=1000, disabled=True),
                                                dbc.Tooltip(
                                                    "Missing PERISCOPE_URL or PERISCOPE_PASS in environment settings.",
                                                    target="fetch-list-wrapper",
                                                    placement="bottom",
                                                )
                                                if is_disabled
                                                else None,
                                            ],
                                            id="fetch-list-wrapper",
                                            className="d-block w-100",
                                        ),
                                    ],
                                    width=12,
                                ),
                            ),
                        ],
                        width="auto",
                        align="center",
                        className="d-flex flex-column align-items-center",
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
