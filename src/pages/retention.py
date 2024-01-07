import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from components.colors import COLORS
from components.dark_mode import with_template_if_dark
from components.sidebar import sidebar
from dash import Input, Output, callback, dcc, html
from pandas.tseries.offsets import DateOffset
from utils.retention import retention_year, retention_mos, retention_pct_year, retention_pct_mos, retention_pct_quarter
from utils.scan_lists import MEMB_LISTS

dash.register_page(__name__, path="/retention", title=f"Membership Dashboard: {__name__.title()}", order=4)

today_date = pd.to_datetime("today")
earliest_year = 1982
today_year = int(today_date.date().strftime("%Y"))

default_start_year = 2016
default_end_date = pd.to_datetime("today") - DateOffset(months=14)
default_end_year = int(default_end_date.date().strftime("%Y"))
years_between = {i: "{}".format(i) for i in range(earliest_year, today_year, 4)}

membership_retention = html.Div(
    children=[
        dbc.Row(
            dbc.Col(
                dcc.RangeSlider(
                    min=earliest_year,
                    max=today_year,
                    step=1,
                    marks=years_between,
                    value=[default_start_year, default_end_year],
                    id="retention-years-slider",
                    tooltip={"placement": "bottom"},
                    className="dbc",
                ),
            ),
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="retention-count-years",
                        style={"height": "43svh"},
                    ),
                    md=6,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="retention-count-months",
                        style={"height": "43svh"},
                    ),
                    md=6,
                ),
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="retention-percent-years",
                        style={"height": "43svh"},
                    ),
                    md=6,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="retention-percent-months",
                        style={"height": "43svh"},
                    ),
                    md=6,
                ),
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="retention-nth-year",
                        style={"height": "43svh"},
                    ),
                    md=6,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="retention-nth-quarter",
                        style={"height": "43svh"},
                    ),
                    md=6,
                ),
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="retention-yoy-year",
                        style={"height": "43svh"},
                    ),
                    md=6,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="retention-yoy-month",
                        style={"height": "43svh"},
                    ),
                    md=6,
                ),
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="retention-tenure-member",
                        style={"height": "43svh"},
                    ),
                    md=6,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="retention-tenure-lapsed",
                        style={"height": "43svh"},
                    ),
                    md=6,
                ),
            ],
            align="center",
        ),
    ],
)


def layout():
    return dbc.Row([dbc.Col(sidebar(), width=2), dbc.Col(membership_retention, width=10)])


@callback(
    Output(component_id="retention-count-years", component_property="figure"),
    Output(component_id="retention-count-months", component_property="figure"),
    Output(component_id="retention-percent-years", component_property="figure"),
    Output(component_id="retention-percent-months", component_property="figure"),
    Output(component_id="retention-nth-year", component_property="figure"),
    Output(component_id="retention-nth-quarter", component_property="figure"),
    Output(component_id="retention-yoy-year", component_property="figure"),
    Output(component_id="retention-yoy-month", component_property="figure"),
    Output(component_id="retention-tenure-member", component_property="figure"),
    Output(component_id="retention-tenure-lapsed", component_property="figure"),
    Input(component_id="list-selected", component_property="value"),
    Input(component_id="retention-years-slider", component_property="value"),
    Input(component_id="color-mode-switch", component_property="value"),
)
def create_retention(date_selected: str, years: list[int], dark_mode: bool) -> [go.Figure] * 10:
    """Update the retention graphs shown based on the selected membership list date."""
    if not date_selected:
        return [go.Figure()] * 10

    df = MEMB_LISTS.get(date_selected, pd.DataFrame())
    df_df = df.loc[df["membership_type"] != "lifetime"]
    df_df = df_df.loc[(df["join_year"] >= pd.to_datetime(years[0], format="%Y")) & (df_df["join_year"] <= pd.to_datetime(years[1], format="%Y"))]
    df_df.loc[
        df_df["membership_status"] == "member in good standing",
        "membership_length_months",
    ] = df_df["membership_length_years"].multiply(12)

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
                go.Scatter(
                    x=df_ry.columns,
                    y=df_ry.loc[year],
                    mode="lines+markers",
                    name=str(year.year),
                    line={"color": COLORS[i % color_len]},
                )
                for i, year in enumerate(df_ry.index)
            ],
            layout=go.Layout(
                title="Member Retention (annual cohort)",
                xaxis={
                    "title": "Years since joining",
                    "range": [1, df_ry.columns.max()],
                },
                yaxis={
                    "title": r"# of cohort retained",
                    "range": [0, df_ry.max().max()],
                },
            ),
        ),
        go.Figure(
            data=[
                go.Scatter(
                    x=df_rm.columns,
                    y=df_rm.loc[year],
                    mode="lines",
                    name=str(year.year),
                    line={"color": COLORS[i % color_len]},
                )
                for i, year in enumerate(df_rm.index)
            ],
            layout=go.Layout(
                xaxis={
                    "title": "Months since joining",
                    "range": [12, df_rm.columns.max()],
                },
                yaxis={
                    "title": r"# of cohort retained",
                    "range": [0, df_rm.max().max()],
                },
            ),
        ),
        go.Figure(
            data=[
                go.Scatter(
                    x=df_rpy.columns,
                    y=df_rpy.loc[year],
                    mode="lines+markers",
                    name=str(year.year),
                    line={"color": COLORS[i % color_len]},
                )
                for i, year in enumerate(df_rpy.index)
            ],
            layout=go.Layout(
                xaxis={
                    "title": "Years since joining",
                    "range": [1, df_rpy.columns.max()],
                },
                yaxis={
                    "title": r"% of cohort retained",
                    "tickformat": ".0%",
                    "range": [0, 1],
                },
            ),
        ),
        go.Figure(
            data=[
                go.Scatter(
                    x=df_rpm.columns,
                    y=df_rpm.loc[year],
                    mode="lines",
                    name=str(year.year),
                    line={"color": COLORS[i % color_len]},
                )
                for i, year in enumerate(df_rpm.index)
            ],
            layout=go.Layout(
                xaxis={
                    "title": "Months since joining",
                    "range": [12, df_rpm.columns.max()],
                },
                yaxis={
                    "title": r"% of cohort retained",
                    "tickformat": ".0%",
                    "range": [0, 1],
                },
            ),
        ),
        go.Figure(
            data=[
                go.Scatter(
                    x=df_rpy.index,
                    y=df_rpy[c],
                    mode="lines+markers",
                    name=c,
                    line={"color": COLORS[c % color_len]},
                )
                for c in df_rpy.columns
                if c not in [0, 1]
            ],
            layout=go.Layout(
                title="Nth year Retention Rates over Time (join-date cohort)",
                xaxis={"title": "Cohort (year joined)"},
                yaxis={
                    "title": r"% of cohort retained",
                    "tickformat": ".0%",
                    "range": [0, 1],
                },
                legend={"title": "Years since joined", "x": 1, "y": 1},
            ),
        ),
        go.Figure(
            data=[
                go.Scatter(
                    x=df_rpq.index,
                    y=df_rpq[c],
                    mode="lines+markers",
                    name=c,
                    line={"color": COLORS[c % color_len]},
                )
                for c in df_rpq.columns
                if c not in [0, 1]
            ],
            layout=go.Layout(
                xaxis={"title": "Cohort (by quarter)"},
                yaxis={
                    "title": r"% of cohort retained",
                    "tickformat": ".0%",
                    "range": [0, 1],
                },
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
                xaxis={
                    "title": "Years since joining",
                    "range": [2, df_ry.columns.max()],
                },
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
                xaxis={
                    "title": "Months since joining",
                    "range": [24, df_rpm.columns.max()],
                },
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

    return [with_template_if_dark(chart, dark_mode) for chart in charts]
