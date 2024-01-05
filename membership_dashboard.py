"""Construct a membership dashboard showing various graphs and metrics to illustrate changes over time."""

import logging
from pathlib import Path

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from dash_bootstrap_templates import load_figure_template
from dash import (
    Dash,
    Input,
    Output,
    callback,
    clientside_callback,
    html,
)

import utils.membership_dashboard_components as mdc
from utils.list_schema import schema
from utils.scan_membership_lists import get_membership_lists
from utils.membership_retention import retention_year, retention_mos, retention_pct_year, retention_pct_mos, retention_pct_quarter


def get_membership_list_metrics(members: dict[str, pd.DataFrame]) -> dict[str, dict[str, pd.Series]]:
    """Restructure a dictionary of dataframs keyed to dates into a dictionary of pandas column names containing the columns keyed to each date."""
    logging.info("Calculating metrics for %s membership lists", len(members))
    columns = set(column for memb_list in members.values() for column in memb_list.columns)
    return {
        column: {list_date: members[list_date].get(column) for list_date, memb_list in members.items() if column in memb_list.columns} for column in columns
    }


MEMB_LISTS = get_membership_lists()
MEMB_METRICS = get_membership_list_metrics(MEMB_LISTS)
DBC_CSS = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
MAPBOX_TOKEN_PATH = Path(".mapbox_token")
if MAPBOX_TOKEN_PATH.is_file():
    px.set_mapbox_access_token(MAPBOX_TOKEN_PATH.read_text(encoding="UTF-8"))
COLORS = [
    "#ee8cb5",  # A list of colors for graphs.
    "#c693be",  # The first and eigth hex codes are used for default and comparison graph bars when comparing dates.
    "#937dc0",
    "#5fa3d9",
    "#00b2e2",
    "#54bcbb",
    "#69bca8",
    "#8dc05a",
    "#f9e442",
    "#f7ce63",
    "#f3aa79",
    "#f0959e",
]
COMPARE_COLORS = [COLORS[0], COLORS[7]]
PAGES = {
    "/": {"name": "Timeline", "schema": True, "generator": mdc.timeline},
    "/list": {"name": "List", "schema": True, "generator": mdc.member_list},
    "/metrics": {"name": "Metrics", "generator": mdc.metrics},
    "/graphs": {"name": "Graphs", "generator": mdc.graphs},
    "/retention": {"name": "Retention", "generator": mdc.retention},
    "/map": {"name": "Map", "schema": True, "generator": mdc.member_map},
}


# Initialize the app
app = Dash(
    external_stylesheets=[
        dbc.themes.DARKLY,
        dbc.themes.JOURNAL,
        DBC_CSS,
        dbc.icons.FONT_AWESOME,
    ],
    # these meta_tags ensure content is scaled correctly on different devices
    # see: https://www.w3schools.com/css/css_rwd_viewport.asp for more
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
)
app.layout = mdc.layout(list(MEMB_LISTS.keys()), PAGES)
load_figure_template(["darkly", "journal"])
logging.basicConfig(level=logging.WARNING, format="%(asctime)s : %(levelname)s : %(message)s")


def include_template_if_not_dark(fig: go.Figure, dark_mode: bool) -> go.Figure:
    """Update the figure template based on the dark mode setting."""
    if not dark_mode:
        fig["layout"]["template"] = pio.templates["journal"]
    return fig


##
## Pages
##


@callback(
    Output(component_id="membership_timeline", component_property="figure"),
    Input(component_id="timeline_columns", component_property="value"),
    Input(component_id="color-mode-switch", component_property="value"),
)
def create_timeline(selected_columns: list[str], dark_mode: bool) -> go.Figure:
    """Update the timeline plotting selected columns."""
    fig = go.Figure(layout={"title": "Membership Trends Timeline", "yaxis_title": "Members"})

    selected_metrics = {}
    for selected_column in selected_columns:
        selected_metrics[selected_column] = {}
        for date in MEMB_METRICS[selected_column]:
            for value, count in MEMB_METRICS[selected_column][date].value_counts().items():
                selected_metrics[selected_column].setdefault(value, {}).setdefault(date, count)

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
    fig = include_template_if_not_dark(fig, dark_mode)

    return fig


@callback(
    Output(component_id="membership_list", component_property="data"),
    Output(component_id="membership_list", component_property="style_data_conditional"),
    Input(component_id="list_dropdown", component_property="value"),
    Input(component_id="list_compare_dropdown", component_property="value"),
)
def create_list(date_selected: str, date_compare_selected: str) -> dict:
    """Update the list shown based on the selected membership list date."""
    df = MEMB_LISTS.get(date_selected, pd.DataFrame())
    df_compare = MEMB_LISTS.get(date_compare_selected, pd.DataFrame())

    if df_compare.empty:
        return df.reset_index(drop=False).to_dict("records"), []

    df["list_date"] = date_selected
    df_compare["list_date"] = date_compare_selected

    records = (
        pd.concat([df, df_compare])
        .reset_index(drop=False)
        .drop_duplicates(
            subset=[
                "actionkit_id",
                "accommodations",
                "city",
                "membership_status",
                "membership_type",
                "monthly_dues_status",
                "yearly_dues_status",
            ],
            keep=False,
        )
    ).to_dict("records")

    conditional_style = [
        {
            "if": {
                "filter_query": '{list_date} = "' + query["date"] + '"',
            },
            "backgroundColor": query["color"],
            "color": "black",
        }
        for query in [{"date": date_compare_selected, "color": COMPARE_COLORS[0]}, {"date": date_selected, "color": COMPARE_COLORS[1]}]
    ]

    return records, conditional_style


def calculate_metric(df: pd.DataFrame, df_compare: pd.DataFrame, plan: list, dark_mode: bool) -> go.Figure:
    """Construct string showing value and change (if comparison data is provided)."""
    column, value, title = plan
    count = df[column].eq(value).sum()
    indicator_mode = "number"
    indicator_delta = None

    if not df_compare.empty:
        count_compare = df_compare[column].eq(value).sum()
        indicator_mode = "number+delta"
        indicator_delta = {"position": "top", "reference": count_compare, "valueformat": ".0f"}

    indicator = go.Indicator(
        mode=indicator_mode,
        value=count,
        delta=indicator_delta,
    )

    fig = go.Figure(data=indicator, layout={"title": title})
    fig = include_template_if_not_dark(fig, dark_mode)

    return fig


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
        indicator_delta = {"position": "top", "reference": rate_compare, "valueformat": ".2"}

    indicator = go.Indicator(
        mode=indicator_mode,
        value=rate,
        delta=indicator_delta,
        number={"suffix": "%"},
    )

    fig = go.Figure(data=indicator, layout={"title": "Retention Rate (MIGS / Constitutional)"})
    fig = include_template_if_not_dark(fig, dark_mode)

    return fig


@callback(
    Output(component_id="members_lifetime", component_property="figure"),
    Output(component_id="members_migs", component_property="figure"),
    Output(component_id="members_expiring", component_property="figure"),
    Output(component_id="members_lapsed", component_property="figure"),
    Output(component_id="metric_retention", component_property="figure"),
    Input(component_id="list_dropdown", component_property="value"),
    Input(component_id="list_compare_dropdown", component_property="value"),
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
        return [""] * len(metrics_plan + 1)

    df = MEMB_LISTS.get(date_selected, pd.DataFrame())
    df_compare = MEMB_LISTS.get(date_compare_selected, pd.DataFrame())

    metric_count_frames = [calculate_metric(df, df_compare, metric_plan, dark_mode) for metric_plan in metrics_plan]
    metric_count_frames.append(calculate_retention_rate(df, df_compare, dark_mode))

    return metric_count_frames


def get_positive_sign(num: float) -> str:
    """Return a string indicating if a number is positive."""
    return "+" if num > 0 else ""


def create_chart(
    df_field: pd.DataFrame,
    df_compare_field: pd.DataFrame,
    title: str,
    ylabel: str,
    log: bool,
) -> go.Figure:
    """Set up html data to show a chart of 1-2 dataframes."""
    chartdf_vc = df_field.value_counts()
    chartdf_compare_vc = df_compare_field.value_counts()

    color, color_compare = COLORS, COLORS
    active_labels = [str(val) for val in chartdf_vc.values]

    if not df_compare_field.empty:
        color, color_compare = COMPARE_COLORS[1], COMPARE_COLORS[0]
        diff_counts = [count - chartdf_compare_vc.get(val, 0) for val, count in zip(chartdf_vc.index, chartdf_vc.values)]
        active_labels = [f"{count} ({get_positive_sign(diff)}{diff})" for count, diff in zip(chartdf_vc.values, diff_counts)]

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
    Output(component_id="membership_status", component_property="figure"),
    Output(component_id="membership_type", component_property="figure"),
    Output(component_id="union_member", component_property="figure"),
    Output(component_id="membership_length", component_property="figure"),
    Output(component_id="race", component_property="figure"),
    Input(component_id="list_dropdown", component_property="value"),
    Input(component_id="list_compare_dropdown", component_property="value"),
    Input(component_id="color-mode-switch", component_property="value"),
)
def create_graphs(date_selected: str, date_compare_selected: str, dark_mode: bool) -> [go.Figure] * 5:
    """Update the graphs shown based on the selected membership list date and compare date (if applicable)."""
    if not date_selected:
        return [go.Figure()] * 5

    df = MEMB_LISTS.get(date_selected, pd.DataFrame())
    df_compare = MEMB_LISTS.get(date_compare_selected, pd.DataFrame())

    def multiple_choice(df: pd.DataFrame, target_column: str, separator: str) -> pd.DataFrame:
        """Split a character-separated list string into an iterable object."""
        return df.assign(**{target_column: df[target_column].str.split(separator)}).explode(target_column).reset_index(drop=True)

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
            False,
        ),
        create_chart(
            df.loc[df["membership_status"] == "member in good standing"]["membership_type"] if "membership_status" in df else pd.DataFrame(),
            df_compare.loc[df_compare["membership_status"] == "member in good standing"]["membership_type"]
            if "membership_status" in df_compare
            else pd.DataFrame(),
            "Dues of Members in Good Standing",
            "Members",
            True,
        ),
        create_chart(
            membersdf["union_member"] if "union_member" in df else pd.DataFrame(),
            membersdf_compare["union_member"] if "union_member" in df_compare else pd.DataFrame(),
            "Union Membership of Constitutional Members",
            "Members",
            True,
        ),
        create_chart(
            membersdf["membership_length_years"].clip(upper=8) if "membership_length_years" in df else pd.DataFrame(),
            membersdf_compare["membership_length_years"].clip(upper=8) if "membership_length_years" in membersdf_compare else pd.DataFrame(),
            "Length of Membership of Constitutional Members (0 - 8+yrs)",
            "Members",
            False,
        ),
        create_chart(
            multiple_choice(membersdf, "race", ",")["race"] if "race" in df else pd.DataFrame(),
            multiple_choice(membersdf_compare, "race", ",")["race"] if "race" in membersdf_compare else pd.DataFrame(),
            "Racial Demographics of Constitutional Members",
            "Members",
            True,
        ),
    ]

    return [include_template_if_not_dark(chart, dark_mode) for chart in charts]


@callback(
    Output(component_id="retention_count_years", component_property="figure"),
    Output(component_id="retention_count_months", component_property="figure"),
    Output(component_id="retention_percent_years", component_property="figure"),
    Output(component_id="retention_percent_months", component_property="figure"),
    Output(component_id="retention_nth_year_year", component_property="figure"),
    Output(component_id="retention_nth_year_quarter", component_property="figure"),
    Output(component_id="retention_year_over_year_year", component_property="figure"),
    Output(component_id="retention_year_over_year_month", component_property="figure"),
    Output(component_id="rentention_tenure_current", component_property="figure"),
    Output(component_id="rentention_tenure_former", component_property="figure"),
    Input(component_id="list_dropdown", component_property="value"),
    Input(component_id="rentention_years_slider", component_property="value"),
    Input(component_id="color-mode-switch", component_property="value"),
)
def create_retention(date_selected: str, years: list[int], dark_mode: bool) -> [go.Figure] * 8:
    """Update the retention graphs shown based on the selected membership list date."""
    if not date_selected:
        return [go.Figure()] * 8

    df = MEMB_LISTS.get(date_selected, pd.DataFrame())
    df_df = df.loc[df["membership_type"] != "lifetime"]
    df_df = df_df.loc[(df["join_year"] >= pd.to_datetime(years[0], format="%Y")) & (df_df["join_year"] <= pd.to_datetime(years[1], format="%Y"))]
    df_df.loc[df_df["membership_status"] == "member in good standing", "membership_length_months"] = df_df["membership_length_years"].multiply(12)

    df_ry = retention_year(df_df)
    df_rm = retention_mos(df_df)
    df_rpy = retention_pct_year(df_df)
    df_rpm = retention_pct_mos(df_df)
    df_rpq = retention_pct_quarter(df_df)

    df_ml_vc = df[df["memb_status_letter"] == "M"]["membership_length_years"].clip(upper=8).value_counts(normalize=True)
    df_ll_vc = df[df["memb_status_letter"] == "L"]["membership_length_years"].clip(upper=8).value_counts(normalize=True)

    color_len = len(COLORS)

    charts = [
        go.Figure(
            data=[
                go.Scatter(x=df_ry.columns, y=df_ry.loc[year], mode="lines+markers", name=str(year.year), line={"color": COLORS[i % color_len]})
                for i, year in enumerate(df_ry.index)
            ],
            layout=go.Layout(
                title="Member Retention (annual cohort)",
                xaxis={"title": "Years since joining", "range": [1, df_ry.columns.max()]},
                yaxis={"title": r"# of cohort retained", "range": [0, df_ry.max().max()]},
            ),
        ),
        go.Figure(
            data=[
                go.Scatter(x=df_rm.columns, y=df_rm.loc[year], mode="lines", name=str(year.year), line={"color": COLORS[i % color_len]})
                for i, year in enumerate(df_rm.index)
            ],
            layout=go.Layout(
                xaxis={"title": "Months since joining", "range": [12, df_rm.columns.max()]},
                yaxis={"title": r"# of cohort retained", "range": [0, df_rm.max().max()]},
            ),
        ),
        go.Figure(
            data=[
                go.Scatter(x=df_rpy.columns, y=df_rpy.loc[year], mode="lines+markers", name=str(year.year), line={"color": COLORS[i % color_len]})
                for i, year in enumerate(df_rpy.index)
            ],
            layout=go.Layout(
                xaxis={"title": "Years since joining", "range": [1, df_rpy.columns.max()]},
                yaxis={"title": r"% of cohort retained", "tickformat": ".0%", "range": [0, 1]},
            ),
        ),
        go.Figure(
            data=[
                go.Scatter(x=df_rpm.columns, y=df_rpm.loc[year], mode="lines", name=str(year.year), line={"color": COLORS[i % color_len]})
                for i, year in enumerate(df_rpm.index)
            ],
            layout=go.Layout(
                xaxis={"title": "Months since joining", "range": [12, df_rpm.columns.max()]},
                yaxis={"title": r"% of cohort retained", "tickformat": ".0%", "range": [0, 1]},
            ),
        ),
        go.Figure(
            data=[
                go.Scatter(x=df_rpy.index, y=df_rpy[c], mode="lines+markers", name=c, line={"color": COLORS[c % color_len]})
                for c in df_rpy.columns
                if c not in [0, 1]
            ],
            layout=go.Layout(
                title="Nth year Retention Rates over Time (join-date cohort)",
                xaxis={"title": "Cohort (year joined)"},
                yaxis={"title": r"% of cohort retained", "tickformat": ".0%", "range": [0, 1]},
                legend={"title": "Years since joined", "x": 1, "y": 1},
            ),
        ),
        go.Figure(
            data=[
                go.Scatter(x=df_rpq.index, y=df_rpq[c], mode="lines+markers", name=c, line={"color": COLORS[c % color_len]})
                for c in df_rpq.columns
                if c not in [0, 1]
            ],
            layout=go.Layout(
                xaxis={"title": "Cohort (by quarter)"},
                yaxis={"title": r"% of cohort retained", "tickformat": ".0%", "range": [0, 1]},
                legend={"title": "Years since joined", "x": 1, "y": 1},
            ),
        ),
        go.Figure(
            data=[
                go.Scatter(
                    x=df_ry.columns,
                    y=df_ry.loc[year].pct_change(fill_method=None),
                    mode="markers+lines",
                    name=str(year.year),
                    line={"color": COLORS[i % color_len]},
                )
                for i, year in enumerate(df_ry.index)
            ],
            layout=go.Layout(
                title="Year-Over-Year Retention (annual cohort)",
                xaxis={"title": "Years since joining", "range": [2, df_ry.columns.max()]},
                yaxis={"title": r"YOY % change", "tickformat": ".0%"},
                legend={"x": 1, "y": 1},
                hovermode="closest",
            ),
        ),
        go.Figure(
            data=[
                go.Scatter(
                    x=df_rpm.columns,
                    y=df_rpm.loc[year].pct_change(periods=12, fill_method=None),
                    mode="lines",
                    name=str(year.year),
                    line={"color": COLORS[i % color_len]},
                )
                for i, year in enumerate(df_rpm.index)
            ],
            layout=go.Layout(
                xaxis={"title": "Months since joining", "range": [24, df_rpm.columns.max()]},
                yaxis={"title": r"YOY % change", "tickformat": ".0%"},
                legend={"x": 1, "y": 1},
                hovermode="closest",
            ),
        ),
        go.Figure(
            data=[
                go.Bar(
                    name="Current members",
                    x=df_ml_vc.index,
                    y=df_ml_vc.values,
                    text=df_ml_vc.values,
                    texttemplate="%{value:.0%}",
                    hovertemplate="%{label}, %{value:.0%}",
                    marker_color=COLORS,
                ),
            ],
            layout=go.Layout(
                title="Tenure of Members",
                xaxis={"title": "Years since joining"},
                yaxis={"title": r"% of current members", "tickformat": ".0%"},
                legend={"x": 1, "y": 1},
            ),
        ),
        go.Figure(
            data=[
                go.Bar(
                    name="Current members",
                    x=df_ll_vc.index,
                    y=df_ll_vc.values,
                    text=df_ll_vc.values,
                    texttemplate="%{value:.0%}",
                    hovertemplate="%{label}, %{value:.0%}",
                    marker_color=COLORS,
                ),
            ],
            layout=go.Layout(
                xaxis={"title": "Years after joining"},
                yaxis={"title": r"% of former members", "tickformat": ".0%"},
                legend={"x": 1, "y": 1},
            ),
        ),
    ]

    return [include_template_if_not_dark(chart, dark_mode) for chart in charts]


@callback(
    Output(component_id="membership_map", component_property="figure"),
    Input(component_id="list_dropdown", component_property="value"),
    Input(component_id="map_column", component_property="value"),
    Input(component_id="color-mode-switch", component_property="value"),
)
def create_map(date_selected: str, selected_column: str, dark_mode: bool) -> px.scatter_mapbox:
    """Set up html data to show a map of Maine DSA members."""
    df_map = MEMB_LISTS.get(date_selected, pd.DataFrame())

    map_figure = px.scatter_mapbox(
        df_map,
        lat="lat",
        lon="lon",
        hover_name=df_map.index,
        hover_data={
            "first_name": True,
            "last_name": True,
            "best_phone": True,
            "email": True,
            "membership_type": True,
            "membership_status": True,
            "membership_length_years": True,
            "join_date": True,
            "xdate": True,
            "lat": False,
            "lon": False,
        },
        color=df_map[selected_column],
        color_discrete_sequence=COLORS,
        zoom=6,
        height=1100,
        mapbox_style="dark",
        template=pio.templates["darkly"],
    )

    if not dark_mode:
        map_figure.update_layout(mapbox_style="light", template=pio.templates["journal"])

    map_figure.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return map_figure


##
## Sidebar
##


clientside_callback(
    """
    (switchOn) => {
       switchOn
         ? document.documentElement.setAttribute("data-bs-theme", "dark")
         : document.documentElement.setAttribute("data-bs-theme", "light")
       return window.dash_clientside.no_update
    }
    """,
    Output(component_id="color-mode-switch", component_property="id"),
    Input(component_id="color-mode-switch", component_property="value"),
)


@app.callback(
    Output(component_id="page-content", component_property="children"),
    Input(component_id="url", component_property="pathname"),
)
def render_page_content(pathname: str):
    """Display the correct page based on the user's navigation path."""
    if pathname not in PAGES:
        return html.Div(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognised..."),
            ],
            className="p-3 bg-light rounded-3",
        )

    page = PAGES[pathname]
    if "schema" in page:
        return page["generator"](schema)
    return page["generator"]()


if __name__ == "__main__":
    app.run_server(debug=True)
