from typing import Literal, get_args

import dash
import dash_bootstrap_components._components as dbc
import pandas as pd
from dash import Input, Output, callback, dcc, html
from plotly import graph_objects as go

from src.components import dark_mode, sidebar
from src.utils import scan_lists

CountKeys = Literal["income", "lifetime", "migs", "lapsed"]
CountFigures = dict[CountKeys, go.Figure]

dash.register_page(__name__, path="/counts", title=f"Membership Dashboard: {__name__.title()}", order=2)

# Centralized configuration mapping keys to their data logic, graph IDs, and titles
METRIC_CONFIG: dict[CountKeys, dict] = {
    "income": {"id": "income-based", "col": "membership_type", "val": "income-based", "title": "Members Paying Income-Based Dues"},
    "lifetime": {"id": "lifetime", "col": "membership_type", "val": "lifetime", "title": "Lifetime Members"},
    "migs": {"id": "migs", "col": "membership_status", "val": "member in good standing", "title": "Members in Good Standing"},
    "lapsed": {"id": "lapsed", "col": "membership_status", "val": "lapsed", "title": "Lapsed Members"},
}

# Dynamically generate 2-column rows for the layout
graphs = [
    dbc.Col(
        dcc.Graph(figure=go.Figure(), id=f"count-{cfg['id']}", style={"height": "30svh"}),
        width=6,
    )
    for cfg in METRIC_CONFIG.values()
]

membership_counts = html.Div([dbc.Row(graphs[i : i + 2]) for i in range(0, len(graphs), 2)])


def layout() -> dbc.Row:
    return dbc.Row(
        [dbc.Col(sidebar.sidebar(), width=2), dbc.Col(membership_counts, width=10)],
        className="dbc",
        style={"margin": "1em"},
    )


def create_count(df: pd.DataFrame, df_compare: pd.DataFrame, plan: dict, *, is_dark_mode: bool) -> go.Figure:
    """Construct string showing value and change (if comparison data is provided)."""
    column, value, title = plan["col"], plan["val"], plan["title"]
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
    output={k: Output(f"count-{cfg['id']}", "figure") for k, cfg in METRIC_CONFIG.items()},
    inputs={
        "date_selected": Input("list-selected", "value"),
        "date_compare_selected": Input("list-compare", "value"),
        "is_dark_mode": Input("color-mode-switch", "value"),
    },
)
def create_counts(date_selected: str, date_compare_selected: str, *, is_dark_mode: bool) -> CountFigures:
    """Update the numeric metrics shown based on the selected membership list date and compare date."""
    keys: list[CountKeys] = list(get_args(CountKeys))

    if not date_selected:
        return {k: go.Figure() for k in keys}

    df = scan_lists.MEMB_LISTS.get(date_selected, pd.DataFrame())
    df_compare = scan_lists.MEMB_LISTS.get(date_compare_selected, pd.DataFrame())

    return {k: create_count(df, df_compare, METRIC_CONFIG[k], is_dark_mode=is_dark_mode) for k in keys}
