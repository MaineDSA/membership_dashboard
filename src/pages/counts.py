import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from components.dark_mode import with_template_if_dark
from components.sidebar import sidebar
from dash import Input, Output, callback, dcc, html
from utils.scan_lists import MEMB_LISTS

dash.register_page(__name__, path="/counts", title=f"Membership Dashboard: {__name__.title()}", order=2)

membership_counts = html.Div(
    children=[
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="count-lifetime",
                        style={"height": "30svh"},
                    ),
                    width=6,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="count-migs",
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
                        id="count-expiring",
                        style={"height": "30svh"},
                    ),
                    width=6,
                ),
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
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="count-retention",
                        style={"height": "30svh"},
                    ),
                    width=6,
                ),
            ]
        ),
    ],
)


def layout():
    return dbc.Row([dbc.Col(sidebar(), width=2), dbc.Col(membership_counts, width=10)])


def calculate_metric(df: pd.DataFrame, df_compare: pd.DataFrame, plan: list, dark_mode: bool) -> go.Figure:
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

    return with_template_if_dark(fig, dark_mode)


def retention_math(df_status: pd.Series) -> float:
    """Return the retention rate as a percentage."""
    migs = df_status.eq("member in good standing").sum()
    constitutional = df_status.eq("member").sum()
    return (migs / (constitutional + migs)) * 100


def calculate_retention_rate(df: pd.DataFrame, df_compare: pd.DataFrame, dark_mode: bool) -> go.Figure:
    """Construct string showing retention rate and change vs another date (if comparison data is provided)."""
    rate = retention_math(df["membership_status"])
    indicator_mode = "number"
    indicator_delta = None

    if not df_compare.empty:
        rate_compare = retention_math(df_compare["membership_status"])
        indicator_mode = "number+delta"
        indicator_delta = {
            "position": "top",
            "reference": rate_compare,
            "valueformat": ".2",
        }

    indicator = go.Indicator(
        mode=indicator_mode,
        value=rate,
        delta=indicator_delta,
        number={"suffix": "%"},
    )

    fig = go.Figure(data=indicator, layout={"title": "Retention Rate (MIGS / Constitutional)"})
    return with_template_if_dark(fig, dark_mode)


@callback(
    Output(component_id="count-lifetime", component_property="figure"),
    Output(component_id="count-migs", component_property="figure"),
    Output(component_id="count-expiring", component_property="figure"),
    Output(component_id="count-lapsed", component_property="figure"),
    Output(component_id="count-retention", component_property="figure"),
    Input(component_id="list-selected", component_property="value"),
    Input(component_id="list-compare", component_property="value"),
    Input(component_id="color-mode-switch", component_property="value"),
)
def create_metrics(date_selected: str, date_compare_selected: str, dark_mode: bool) -> list[go.Figure]:
    """Update the numeric metrics shown based on the selected membership list date and compare date (if applicable)."""
    metrics_plan = [
        ["membership_type", "lifetime", "Lifetime Members"],
        ["membership_status", "member in good standing", "Members in Good Standing"],
        ["membership_status", "member", "Expiring Members"],
        ["membership_status", "lapsed", "Lapsed Members"],
    ]

    if not date_selected:
        return [go.Figure()] * (len(metrics_plan) + 1)

    df = MEMB_LISTS.get(date_selected, pd.DataFrame())
    df_compare = MEMB_LISTS.get(date_compare_selected, pd.DataFrame())

    metric_count_frames = [calculate_metric(df, df_compare, metric_plan, dark_mode) for metric_plan in metrics_plan]
    metric_count_frames.append(calculate_retention_rate(df, df_compare, dark_mode))

    return metric_count_frames