from typing import Literal, get_args

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, callback, dcc, html
from plotly import graph_objects as go

from src.components import colors, dark_mode, sidebar
from src.utils import scan_lists

GraphKeys = Literal["status", "m_type", "union", "length", "race"]
GraphFigures = dict[GraphKeys, go.Figure]

dash.register_page(__name__, path="/graphs", title=f"Membership Dashboard: {__name__.title()}", order=3)

membership_graphs = html.Div(
    children=[
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="graph-membership-status",
                        style={"height": "48svh"},
                    ),
                    md=4,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="graph-membership-type",
                        style={"height": "48svh"},
                    ),
                    md=4,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="graph-union-member",
                        style={"height": "48svh"},
                    ),
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
                        id="graph-membership-length",
                        style={"height": "48svh"},
                    ),
                    md=6,
                ),
                dbc.Col(
                    dcc.Graph(figure=go.Figure(), id="graph-race", style={"height": "48svh"}),
                    md=6,
                ),
            ],
            align="center",
        ),
    ],
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
    output={
        "status": Output("graph-membership-status", "figure"),
        "m_type": Output("graph-membership-type", "figure"),
        "union": Output("graph-union-member", "figure"),
        "length": Output("graph-membership-length", "figure"),
        "race": Output("graph-race", "figure"),
    },
    inputs={
        "date_selected": Input("list-selected", "value"),
        "date_compare_selected": Input("list-compare", "value"),
        "is_dark_mode": Input("color-mode-switch", "value"),
    },
)
def create_graphs(date_selected: str, date_compare_selected: str, *, is_dark_mode: bool) -> GraphFigures:
    """Update the graphs shown based on the selected membership list date and compare date (if applicable)."""
    if not date_selected:
        return {"status": go.Figure(), "m_type": go.Figure(), "union": go.Figure(), "length": go.Figure(), "race": go.Figure()}

    df = scan_lists.MEMB_LISTS.get(date_selected, pd.DataFrame())
    df_compare = scan_lists.MEMB_LISTS.get(date_compare_selected, pd.DataFrame())

    def multiple_choice(df_mc: pd.DataFrame, target_column: str, separator: str) -> pd.DataFrame:
        """Split a character-separated list string into an iterable object."""
        return df_mc.assign(**{target_column: df_mc[target_column].str.split(separator)}).explode(target_column).reset_index(drop=True)

    membersdf = df.query('membership_status != "lapsed" and membership_status != "expired"')
    membersdf_compare = (
        df_compare.query('membership_status != "lapsed" and membership_status != "expired"') if "membership_status" in df_compare else pd.DataFrame()
    )

    charts = {
        "status": create_graph(
            df["membership_status"] if "membership_status" in df else pd.DataFrame(),
            df_compare["membership_status"] if "membership_status" in df_compare else pd.DataFrame(),
            "Membership Counts",
            "Members",
        ),
        "m_type": create_graph(
            df.loc[df["membership_status"] == "member in good standing"]["membership_type"] if "membership_status" in df else pd.DataFrame(),
            df_compare.loc[df_compare["membership_status"] == "member in good standing"]["membership_type"]
            if "membership_status" in df_compare
            else pd.DataFrame(),
            "Dues of Members in Good Standing",
            "Members",
        ),
        "union": create_graph(
            membersdf["union_member"] if "union_member" in df else pd.DataFrame(),
            membersdf_compare["union_member"] if "union_member" in df_compare else pd.DataFrame(),
            "Union Membership of Constitutional Members",
            "Members",
        ),
        "length": create_graph(
            membersdf["membership_length_years"].clip(upper=8) if "membership_length_years" in df else pd.DataFrame(),
            membersdf_compare["membership_length_years"].clip(upper=8) if "membership_length_years" in membersdf_compare else pd.DataFrame(),
            "Length of Membership of Constitutional Members (0 - 8+yrs)",
            "Members",
        ),
        "race": create_graph(
            multiple_choice(membersdf, "race", ",")["race"] if "race" in df else pd.DataFrame(),
            multiple_choice(membersdf_compare, "race", ",")["race"] if "race" in membersdf_compare else pd.DataFrame(),
            "Racial Demographics of Constitutional Members",
            "Members",
        ),
    }

    keys: tuple[GraphKeys, ...] = get_args(GraphKeys)
    figures: GraphFigures = {k: dark_mode.with_template_if_dark(charts[k], is_dark_mode=is_dark_mode) for k in keys}

    return figures
