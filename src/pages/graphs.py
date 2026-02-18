import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from src.components import colors, dark_mode, sidebar
from src.utils import scan_lists

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


def create_chart(
    df_field: pd.DataFrame,
    df_compare_field: pd.DataFrame,
    title: str,
    ylabel: str,
    *,
    log: bool,
) -> go.Figure:
    """Set up html data to show a chart of 1-2 dataframes."""
    chartdf_vc = df_field.value_counts()
    chartdf_compare_vc = df_compare_field.value_counts()

    color, color_compare = colors.COLORS, colors.COLORS
    active_labels = [str(val) for val in chartdf_vc.values]

    if not df_compare_field.empty:
        color, color_compare = colors.COMPARE_COLORS[1], colors.COMPARE_COLORS[0]
        diff_counts = [count - chartdf_compare_vc.get(val, 0) for val, count in zip(chartdf_vc.index, chartdf_vc.values, strict=True)]
        active_labels = [f"{count} ({get_positive_sign(diff)}{diff})" for count, diff in zip(chartdf_vc.values, diff_counts, strict=True)]

    chart = go.Figure(
        data=[
            go.Bar(
                name="Compare List",
                x=chartdf_compare_vc.index,
                y=chartdf_compare_vc.values,
                text=chartdf_compare_vc.values,
                marker_color=color_compare,
            ),
            go.Bar(
                name="Active List",
                x=chartdf_vc.index,
                y=chartdf_vc.values,
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
    Output(component_id="graph-membership-status", component_property="figure"),
    Output(component_id="graph-membership-type", component_property="figure"),
    Output(component_id="graph-union-member", component_property="figure"),
    Output(component_id="graph-membership-length", component_property="figure"),
    Output(component_id="graph-race", component_property="figure"),
    Input(component_id="list-selected", component_property="value"),
    Input(component_id="list-compare", component_property="value"),
    Input(component_id="color-mode-switch", component_property="value"),
)
def create_graphs(date_selected: str, date_compare_selected: str, *, is_dark_mode: bool) -> [go.Figure] * 5:
    """Update the graphs shown based on the selected membership list date and compare date (if applicable)."""
    if not date_selected:
        return [go.Figure()] * 5

    df = scan_lists.MEMB_LISTS.get(date_selected, pd.DataFrame())
    df_compare = scan_lists.MEMB_LISTS.get(date_compare_selected, pd.DataFrame())

    def multiple_choice(df_mc: pd.DataFrame, target_column: str, separator: str) -> pd.DataFrame:
        """Split a character-separated list string into an iterable object."""
        return df_mc.assign(**{target_column: df_mc[target_column].str.split(separator)}).explode(target_column).reset_index(drop=True)

    membersdf = df.query('membership_status != "lapsed" and membership_status != "expired"')
    membersdf_compare = (
        df_compare.query('membership_status != "lapsed" and membership_status != "expired"') if "membership_status" in df_compare else pd.DataFrame()
    )

    charts = [
        create_chart(
            df["membership_status"] if "membership_status" in df else pd.DataFrame(),
            df_compare["membership_status"] if "membership_status" in df_compare else pd.DataFrame(),
            "Membership Counts",
            "Members",
            log=False,
        ),
        create_chart(
            df.loc[df["membership_status"] == "member in good standing"]["membership_type"] if "membership_status" in df else pd.DataFrame(),
            df_compare.loc[df_compare["membership_status"] == "member in good standing"]["membership_type"]
            if "membership_status" in df_compare
            else pd.DataFrame(),
            "Dues of Members in Good Standing",
            "Members",
            log=True,
        ),
        create_chart(
            membersdf["union_member"] if "union_member" in df else pd.DataFrame(),
            membersdf_compare["union_member"] if "union_member" in df_compare else pd.DataFrame(),
            "Union Membership of Constitutional Members",
            "Members",
            log=True,
        ),
        create_chart(
            membersdf["membership_length_years"].clip(upper=8) if "membership_length_years" in df else pd.DataFrame(),
            membersdf_compare["membership_length_years"].clip(upper=8) if "membership_length_years" in membersdf_compare else pd.DataFrame(),
            "Length of Membership of Constitutional Members (0 - 8+yrs)",
            "Members",
            log=False,
        ),
        create_chart(
            multiple_choice(membersdf, "race", ",")["race"] if "race" in df else pd.DataFrame(),
            multiple_choice(membersdf_compare, "race", ",")["race"] if "race" in membersdf_compare else pd.DataFrame(),
            "Racial Demographics of Constitutional Members",
            "Members",
            log=True,
        ),
    ]

    return [dark_mode.with_template_if_dark(chart, is_dark_mode) for chart in charts]
