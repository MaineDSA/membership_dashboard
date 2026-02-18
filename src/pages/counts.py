from typing import Literal, get_args

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, callback, dcc, html
from plotly import graph_objects as go

from src.components import dark_mode, sidebar
from src.utils import scan_lists

CountKeys = Literal["income", "lifetime", "migs", "expiring", "lapsed"]
CountFigures = dict[CountKeys, go.Figure]

dash.register_page(__name__, path="/counts", title=f"Membership Dashboard: {__name__.title()}", order=2)

METRIC_PLANS = [
    ["membership_type", "income-based", "Members Paying Income-Based Dues"],
    ["membership_type", "lifetime", "Lifetime Members"],
    ["membership_status", "member in good standing", "Members in Good Standing"],
    ["membership_status", "member", "Expiring Members"],
    ["membership_status", "lapsed", "Lapsed Members"],
]

membership_counts = html.Div(
    children=[
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="count-income-based",
                        style={"height": "30svh"},
                    ),
                    width=6,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="count-lifetime",
                        style={"height": "30svh"},
                    ),
                    width=6,
                ),
            ],
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="count-migs",
                        style={"height": "30svh"},
                    ),
                    width=6,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="count-expiring",
                        style={"height": "30svh"},
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
                        id="count-lapsed",
                        style={"height": "30svh"},
                    ),
                    width=6,
                ),
            ]
        ),
    ],
)


def layout() -> dbc.Row:
    return dbc.Row([dbc.Col(sidebar.sidebar(), width=2), dbc.Col(membership_counts, width=10)], className="dbc", style={"margin": "1em"})


def create_count(df: pd.DataFrame, df_compare: pd.DataFrame, plan: list[str], *, is_dark_mode: bool) -> go.Figure:
    """Construct string showing value and change (if comparison data is provided)."""
    column, value, title = plan
    count = df[column].eq(value).sum()
    indicator_mode = "number"
    indicator_delta = None

    if not df_compare.empty:
        count_compare = df_compare[column].eq(value).sum()
        indicator_mode = "number+delta"
        indicator_delta = {
            "position": "top",
            "reference": count_compare,
            "valueformat": ".0f",
        }

    indicator = go.Indicator(
        mode=indicator_mode,
        value=count,
        delta=indicator_delta,
    )

    fig = go.Figure(data=indicator, layout={"title": title})

    return dark_mode.with_template_if_dark(fig, is_dark_mode=is_dark_mode)


@callback(
    output={
        "income": Output("count-income-based", "figure"),
        "lifetime": Output("count-lifetime", "figure"),
        "migs": Output("count-migs", "figure"),
        "expiring": Output("count-expiring", "figure"),
        "lapsed": Output("count-lapsed", "figure"),
    },
    inputs={
        "date_selected": Input("list-selected", "value"),
        "date_compare_selected": Input("list-compare", "value"),
        "is_dark_mode": Input("color-mode-switch", "value"),
    },
)
def create_counts(date_selected: str, date_compare_selected: str, *, is_dark_mode: bool) -> CountFigures:
    """Update the numeric metrics shown based on the selected membership list date and compare date (if applicable)."""
    if not date_selected:
        return {count: go.Figure() for _, count in enumerate(get_args(CountKeys))}

    df = scan_lists.MEMB_LISTS.get(date_selected, pd.DataFrame())
    df_compare = scan_lists.MEMB_LISTS.get(date_compare_selected, pd.DataFrame())

    keys: tuple[CountKeys, ...] = get_args(CountKeys)
    figures: CountFigures = {k: create_count(df, df_compare, METRIC_PLANS[i], is_dark_mode=is_dark_mode) for i, k in enumerate(keys)}

    return figures
