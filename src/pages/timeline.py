import logging

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from components.colors import COLORS
from components.dark_mode import with_template_if_dark
from components.sidebar import sidebar
from components.status_filter import status_filter_col
from dash import Input, Output, callback, dcc, html
from plotly import graph_objects as go
from utils.scan_lists import MEMB_LISTS
from utils.schema import schema

dash.register_page(__name__, path="/", title=f"Membership Dashboard: {__name__.title()}", order=0)

membership_timeline = html.Div(
    children=[
        dbc.Row(
            [
                status_filter_col(),
                dbc.Col(
                    dcc.Dropdown(
                        options=list(column for column in schema.columns), value=["membership_status"], multi=True, id="selected-columns", className="dbc"
                    ),
                ),
            ],
            align="center",
        ),
        dbc.Row(
            dbc.Col(
                dcc.Graph(
                    figure={},
                    id="timeline",
                    style={
                        "display": "inline-block",
                        "height": "85svh",
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


def layout():
    return dbc.Row([dbc.Col(sidebar(), width=2), dbc.Col(membership_timeline, width=10)])


def value_counts_by_date(date_counts: dict) -> dict[str, int]:
    """Returns data from date_counts in format column>date>value (instead of date>column>value) for use in creating timeline traces"""
    metrics = {}
    for date, values in date_counts.items():
        for value, count in values.value_counts().items():
            metrics.setdefault(value, {}).setdefault(date, count)
    return metrics


def get_membership_list_metrics(members: dict[str, pd.DataFrame]) -> dict[str, dict[str, pd.Series]]:
    """Restructure a dictionary of dataframs keyed to dates into a dictionary of pandas column names containing the columns keyed to each date."""
    logging.info("Calculating metrics for %s membership lists", len(members))
    columns = set(column for memb_list in members.values() for column in memb_list.columns)
    return {
        column: {list_date: members[list_date].get(column) for list_date, memb_list in members.items() if column in memb_list.columns} for column in columns
    }


@callback(
    Output(component_id="timeline", component_property="figure"),
    Input(component_id="selected-columns", component_property="value"),
    Input(component_id="status-filter", component_property="value"),
    Input(component_id="color-mode-switch", component_property="value"),
)
def create_timeline(selected_columns: list[str], selected_statuses: list[str], dark_mode: bool) -> go.Figure:
    """Update the timeline plotting selected columns."""
    membership_lists = {date: membership_list.loc[membership_list["membership_status"].isin(selected_statuses)] for date, membership_list in MEMB_LISTS.items()}
    membership_value_counts = get_membership_list_metrics(membership_lists)
    selected_metrics = {column: value_counts_by_date(membership_value_counts[column]) for column in selected_columns}

    fig = go.Figure(layout={"title": "Membership Trends Timeline", "yaxis_title": "Members"})
    fig.add_traces(
        [
            go.Scatter(
                name=value,
                x=list(timeline_metric[value].keys()),
                y=list(timeline_metric[value].values()),
                mode="lines",
                marker_color=COLORS[count % len(COLORS)],
            )
            for _, timeline_metric in selected_metrics.items()
            for count, value in enumerate(timeline_metric)
        ]
    )
    return with_template_if_dark(fig, dark_mode)
