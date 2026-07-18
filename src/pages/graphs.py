from collections.abc import Callable
from typing import Literal, get_args

import dash
import dash_bootstrap_components._components as dbc
import pandas as pd
from dash import Input, Output, callback, dcc, html
from plotly import graph_objects as go

from src.components import colors, dark_mode, sidebar
from src.utils import scan_lists

GraphKeys = Literal["status", "m_type", "union", "length", "race"]
GraphFigures = dict[GraphKeys, go.Figure]

GRAPH_KEYS: tuple[GraphKeys, ...] = get_args(GraphKeys)

dash.register_page(__name__, path="/graphs", title=f"Membership Dashboard: {__name__.title()}", order=3)

# list of rows containing (key, element_id, width)
GRID_CONFIG = [
    [
        ("status", "graph-membership-status", 4),
        ("m_type", "graph-membership-type", 4),
        ("union", "graph-union-member", 4),
    ],
    [
        ("length", "graph-membership-length", 6),
        ("race", "graph-race", 6),
    ],
]

membership_graphs = html.Div(
    [
        dbc.Row([dbc.Col(dcc.Graph(figure=go.Figure(), id=graph_id, style={"height": "48svh"}), md=width) for _, graph_id, width in row], align="center")
        for row in GRID_CONFIG
    ]
)


def layout() -> dbc.Row:
    return dbc.Row([dbc.Col(sidebar.sidebar(), width=2), dbc.Col(membership_graphs, width=10)], className="dbc", style={"margin": "1em"})


def get_positive_sign(num: float) -> str:
    """Return a string indicating if a number is positive."""
    return "+" if num > 0 else ""


def create_graph(
    df_field: pd.Series | pd.DataFrame,
    df_compare_field: pd.Series | pd.DataFrame,
    title: str,
    ylabel: str,
    *,
    log: bool = False,
) -> go.Figure:
    """Set up html data to show a chart of 1-2 dataframes."""
    chartdf_vc = df_field.value_counts()
    chartdf_compare_vc = df_compare_field.value_counts()

    color: list[str] | str = colors.COLORS
    color_compare: list[str] | str = colors.COLORS
    active_labels = [str(val) for val in chartdf_vc.values]

    if not df_compare_field.empty:
        color, color_compare = colors.COMPARE_COLORS[1], colors.COMPARE_COLORS[0]
        diff_counts = [count - chartdf_compare_vc.get(val, 0) for val, count in zip(chartdf_vc.index, chartdf_vc.values, strict=True)]
        active_labels = [f"{count} ({get_positive_sign(diff)}{diff})" for count, diff in zip(chartdf_vc.values, diff_counts, strict=True)]

    chart = go.Figure(
        data=[
            go.Bar(
                name="Compare List",
                x=chartdf_compare_vc.index.tolist(),
                y=chartdf_compare_vc.values.tolist(),
                text=chartdf_compare_vc.values.tolist(),
                marker_color=color_compare,
            ),
            go.Bar(
                name="Active List",
                x=chartdf_vc.index.tolist(),
                y=chartdf_vc.values.tolist(),
                text=active_labels,
                marker_color=color,
            ),
        ],
        layout={"title": title, "yaxis_title": ylabel},
    )

    if log:
        chart.update_layout(yaxis_title=ylabel + " (Logarithmic)")
        chart.update_yaxes(type="log")

    return chart


@callback(
    output={key: Output(graph_id, "figure") for row in GRID_CONFIG for key, graph_id, _ in row},
    inputs={
        "date_selected": Input("list-selected", "value"),
        "date_compare_selected": Input("list-compare", "value"),
        "is_dark_mode": Input("color-mode-switch", "value"),
    },
)
def create_graphs(date_selected: scan_lists.ISODateStr, date_compare_selected: scan_lists.ISODateStr, *, is_dark_mode: bool) -> GraphFigures:
    """Update the graphs shown based on the selected membership list date and compare date (if applicable)."""
    if not date_selected:
        return {k: go.Figure() for k in GRAPH_KEYS}

    df = scan_lists.MEMB_LISTS.get(date_selected, pd.DataFrame())
    df_compare = scan_lists.MEMB_LISTS.get(date_compare_selected, pd.DataFrame())

    def multiple_choice(df_mc: pd.DataFrame, target_column: str, separator: str) -> pd.DataFrame:
        """Split a character-separated list string into an iterable object."""
        return df_mc.assign(**{target_column: df_mc[target_column].str.split(separator)}).explode(target_column).reset_index(drop=True)

    def _get_field(source_df: pd.DataFrame, col: str, transform: Callable | None = None) -> pd.Series | pd.DataFrame:
        """Safely extract and optional transform a dataframe column if it exists."""
        if col not in source_df:
            return pd.DataFrame()
        return transform(source_df) if transform else source_df[col]

    # Filters
    status_query = 'membership_status != "lapsed" and membership_status != "expired"'
    membersdf = df.query(status_query) if "membership_status" in df else pd.DataFrame()
    membersdf_compare = df_compare.query(status_query) if "membership_status" in df_compare else pd.DataFrame()

    charts = {
        "status": create_graph(
            _get_field(df, "membership_status"),
            _get_field(df_compare, "membership_status"),
            "Membership Counts",
            "Members",
        ),
        "m_type": create_graph(
            _get_field(df, "membership_status", lambda d: d.loc[d["membership_status"] == "member in good standing"]["membership_type"]),
            _get_field(df_compare, "membership_status", lambda d: d.loc[d["membership_status"] == "member in good standing"]["membership_type"]),
            "Dues of Members in Good Standing",
            "Members",
        ),
        "union": create_graph(
            _get_field(membersdf, "union_member"),
            _get_field(membersdf_compare, "union_member"),
            "Union Membership of Constitutional Members",
            "Members",
        ),
        "length": create_graph(
            _get_field(membersdf, "membership_length_years", lambda d: d["membership_length_years"].clip(upper=8)),
            _get_field(membersdf_compare, "membership_length_years", lambda d: d["membership_length_years"].clip(upper=8)),
            "Length of Membership of Constitutional Members (0 - 8+yrs)",
            "Members",
        ),
        "race": create_graph(
            _get_field(membersdf, "race", lambda d: multiple_choice(d, "race", ",")["race"]),
            _get_field(membersdf_compare, "race", lambda d: multiple_choice(d, "race", ",")["race"]),
            "Racial Demographics of Constitutional Members",
            "Members",
        ),
    }

    return {k: dark_mode.with_template_if_dark(charts[k], is_dark_mode=is_dark_mode) for k in GRAPH_KEYS}
