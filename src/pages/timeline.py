import logging
from typing import Literal, get_args

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, html
from plotly import graph_objects as go

from src.components import colors, dark_mode, sidebar, value_filter
from src.utils import scan_lists

TimelineKeys = Literal["timeline"]
TimelineFigures = dict[TimelineKeys, go.Figure]

dash.register_page(__name__, path="/", title=f"Membership Dashboard: {__name__.title()}", order=0)

logger = logging.getLogger(__name__)

membership_timeline = html.Div(
    children=[
        dbc.Row(
            [
                dbc.Col(
                    dcc.Dropdown(options=[], multi=True, id="filtered-values"),
                ),
                dbc.Col(
                    dcc.Dropdown(options=["membership_status"], value="membership_status", multi=False, id="selected-column"),
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
    return dbc.Row([dbc.Col(sidebar.sidebar(), width=2), dbc.Col(membership_timeline, width=10)], className="dbc", style={"margin": "1em"})


@callback(
    output={"timeline": Output(component_id="timeline", component_property="figure")},
    inputs={
        "selected_column": Input(component_id="selected-column", component_property="value"),
        "selected_values": Input(component_id="filtered-values", component_property="value"),
        "is_dark_mode": Input(component_id="color-mode-switch", component_property="value"),
    },
)
def create_timeline(selected_column: str, selected_values: list[str], *, is_dark_mode: bool) -> TimelineFigures:
    """Update the timeline plotting selected columns."""
    if not selected_column or not selected_values:
        return {"timeline": go.Figure()}

    membership_lists = {
        date: membership_list.loc[membership_list[selected_column].isin(selected_values)] for date, membership_list in scan_lists.MEMB_LISTS.items()
    }
    membership_value_counts = value_filter.get_membership_list_metrics(membership_lists)
    pivot_data = value_filter.pivot_with_summary(membership_value_counts[selected_column])

    fig = go.Figure(layout={"title": "Membership Trends Timeline", "yaxis_title": "Members"})
    fig.add_traces(
        [
            go.Scatter(
                name=value,
                x=list(data_points.keys()),
                y=list(data_points.values()),
                mode="lines",
                marker_color=colors.COLORS[count % len(colors.COLORS)],
            )
            for count, (value, data_points) in enumerate(pivot_data["timeline"].items())
        ]
    )

    keys: tuple[TimelineKeys, ...] = get_args(TimelineKeys)
    figures: TimelineFigures = {k: dark_mode.with_template_if_dark(fig, is_dark_mode=is_dark_mode) for k in keys}

    return figures
