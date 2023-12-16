"""Construct a membership dashboard showing various graphs and metrics to illustrate changes over time."""

import logging
from pathlib import Path
import pandas as pd
import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from dash import Dash, html, dash_table, dcc, callback, clientside_callback, Output, Input
from scan_membership_lists import get_membership_lists


# A list of colors for graphs.
# The first and sixth hex codes are used for default and comparison graph bars when comparing dates.
COLORS = [
    "#ee8cb5",
    "#c693be",
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


px.set_mapbox_access_token(Path(".mapbox_token").read_text(encoding="UTF-8"))
logging.basicConfig(level=logging.WARNING, format="%(asctime)s : %(levelname)s : %(message)s")


def get_membership_list_metrics(members: pd.DataFrame) -> dict:
    """Scan memb_lists and calculate metrics."""
    logging.info("Calculating metrics for %s membership lists", len(members))
    return {
        column: {
            date_formatted: members[date_formatted].get(column)
            for date_formatted, membership_list in members.items()
            if column in membership_list.columns
        }
        for column in set(column for membership_list in members.values() for column in membership_list.columns)
    }


memb_lists = get_membership_lists()
memb_lists_metrics = get_membership_list_metrics(memb_lists)


# Initialize the app
DBC_CSS = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
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
load_figure_template(["darkly", "journal"])

sidebar_header = dbc.Row(
    [
        dbc.Col(
            html.Img(
                src=r"https://www.mainedsa.org/wp-content/uploads/2023/07/Maine-DSA-Moose-with-Rose-Logo.svg",
                alt="Red Maine DSA logo of a moose holding a rose in its mouth under the text Maine DSA",
            ),
            align="center",
        ),
        dbc.Col(
            [
                dbc.Row(
                    [
                        dbc.Col(dbc.Label(className="fa fa-sun", html_for="color-mode-switch")),
                        dbc.Col(
                            dbc.Switch(
                                id="color-mode-switch",
                                value=True,
                                className="d-inline-block ms-1",
                                persistence=True,
                            )
                        ),
                        dbc.Col(dbc.Label(className="fa fa-moon", html_for="color-mode-switch")),
                    ],
                    className="g-0",
                )
            ],
            width="auto",
            align="center",
        ),
    ]
)

sidebar = html.Div(
    id="sidebar",
    children=[
        sidebar_header,
        # we wrap the horizontal rule and short blurb in a div that can be hidden on a small screen
        html.Div(
            [
                html.Hr(),
                html.P("Membership Dasboard", className="lead"),
            ],
            id="blurb",
        ),
        dcc.Dropdown(
            options=list(memb_lists.keys()),
            value=list(memb_lists.keys())[0],
            id="list_dropdown",
        ),
        html.Div(
            [
                html.P("Active List"),
            ],
            id="list_dropdown_label",
        ),
        dcc.Dropdown(
            options=list(memb_lists.keys()),
            id="list_compare_dropdown",
        ),
        html.Div(
            [
                html.P("Compare To"),
            ],
            id="list_compare_dropdown_label",
        ),
        dbc.Nav(
            [
                dbc.NavLink("Timeline", href="/", active="exact"),
                dbc.NavLink("List", href="/list", active="exact"),
                dbc.NavLink("Metrics", href="/metrics", active="exact"),
                dbc.NavLink("Graphs", href="/graphs", active="exact"),
                dbc.NavLink("Map", href="/map", active="exact"),
            ],
            id="navigation",
            vertical=True,
            pills=True,
        ),
    ],
)

content = html.Div(id="page-content")

app.layout = dbc.Container([dcc.Location(id="url"), sidebar, content], className="dbc dbc-ag-grid", fluid=True)

timeline = html.Div(
    id="timeline-container",
    children=[
        dcc.Dropdown(
            options=list(memb_lists_metrics.keys()),
            value=["membership_status"],
            multi=True,
            id="timeline_columns",
        ),
        dcc.Graph(
            figure={},
            id="membership_timeline",
            style={
                "display": "inline-block",
                "height": "85vh",
                "width": "100%",
                "padding-left": "-1em",
                "padding-right": "-1em",
                "padding-bottom": "-1em",
            },
        ),
    ],
)

member_list = html.Div(
    id="list-container",
    children=[
        dash_table.DataTable(
            data=memb_lists[list(memb_lists.keys())[0]].to_dict("records"),
            columns=[{"name": i, "id": i, "selectable": True} for i in memb_lists[list(memb_lists.keys())[0]].columns],
            sort_action="native",
            sort_by=[
                {"column_id": "last_name", "direction": "asc"},
                {"column_id": "first_name", "direction": "asc"},
            ],
            filter_action="native",
            filter_options={"case": "insensitive"},
            export_format="csv",
            page_size=20,
            style_table={
                "display": "inline-block",
                "height": "80vh",
                "overflowY": "auto",
                "overflowX": "auto",
            },
            id="membership_list",
        ),
    ],
)

metrics = html.Div(
    id="metrics-container",
    children=[
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="members_lifetime",
                        style={"height": "30vh"},
                    ),
                    width=6,
                ),
                dbc.Col(
                    dcc.Graph(figure=go.Figure(), id="members_migs", style={"height": "30vh"}),
                    width=6,
                ),
            ],
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="members_expiring",
                        style={"height": "30vh"},
                    ),
                    width=6,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="members_lapsed",
                        style={"height": "30vh"},
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
                        id="metric_retention",
                        style={"height": "30vh"},
                    ),
                    width=6,
                ),
            ]
        ),
    ],
)

graphs = html.Div(
    id="graphs-container",
    children=[
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="membership_status",
                        style={"height": "46vh"},
                    ),
                    md=4,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="membership_type",
                        style={"height": "46vh"},
                    ),
                    md=4,
                ),
                dbc.Col(
                    dcc.Graph(figure=go.Figure(), id="union_member", style={"height": "46vh"}),
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
                        id="membership_length",
                        style={"height": "46vh"},
                    ),
                    md=6,
                ),
                dbc.Col(
                    dcc.Graph(figure=go.Figure(), id="race", style={"height": "46vh"}),
                    md=6,
                ),
            ],
            align="center",
        ),
    ],
)

member_map = html.Div(
    id="map-container",
    children=[
        dcc.Dropdown(
            options=list(memb_lists_metrics.keys()),
            value="membership_status",
            multi=False,
            id="map_column",
        ),
        dcc.Graph(
            figure=go.Figure(),
            id="membership_map",
            style={
                "display": "inline-block",
                "height": "85vh",
                "width": "100%",
                "padding-left": "-1em",
                "padding-right": "-1em",
                "padding-bottom": "-1em",
            },
        ),
    ],
)


def selected_data(child: str) -> pd.DataFrame:
    """Return a pandas dataframe, either empty or containing a membership list."""
    return memb_lists[child] if child else pd.DataFrame()


##
## Pages
##


@callback(
    Output(component_id="membership_timeline", component_property="figure"),
    Input(component_id="timeline_columns", component_property="value"),
    Input(component_id="color-mode-switch", component_property="value"),
)
def create_timeline(selected_columns: list, dark_mode: bool) -> go.Figure:
    """Update the timeline plotting selected columns."""
    timeline_figure = go.Figure()
    selected_metrics = {}

    for selected_column in selected_columns:
        selected_metrics[selected_column] = {}
        for date in memb_lists_metrics[selected_column]:
            for value, count in memb_lists_metrics[selected_column][date].value_counts().items():
                selected_metrics[selected_column].setdefault(value, {}).setdefault(date, count)

    timeline_figure.add_traces(
        [
            go.Scatter(
                name=value,
                x=list(timeline_metric[value].keys()),
                y=list(timeline_metric[value].values()),
                mode="lines",
                marker_color=COLORS[count % len(COLORS)],
            )
            for count, (selected_column, timeline_metric) in enumerate(selected_metrics.items())
            for value in timeline_metric
        ]
    )

    timeline_figure.update_layout(title="Membership Trends Timeline", yaxis_title="Members")
    if not dark_mode:
        timeline_figure["layout"]["template"] = pio.templates["journal"]

    return timeline_figure


@callback(
    Output(component_id="membership_list", component_property="data"),
    Input(component_id="list_dropdown", component_property="value"),
    Input(component_id="list_compare_dropdown", component_property="value"),
)
def create_list(date_selected: str, date_compare_selected: str) -> dict:
    """Update the list shown based on the selected membership list date."""
    df = selected_data(date_selected)
    df_compare = selected_data(date_compare_selected)

    if df_compare.empty:
        return df.to_dict("records")

    return (
        pd.concat([df, df_compare])
        .reset_index(drop=False)
        .drop_duplicates(
            subset=["actionkit_id", "membership_status", "membership_type"],
            keep=False,
        )
        .drop_duplicates(subset=["actionkit_id"])
    ).to_dict("records")


def calculate_metric(df: pd.DataFrame, df_compare: pd.DataFrame, plan: list, dark_mode: bool) -> go.Figure:
    """Construct string showing value and change (if comparison data is provided)."""
    column, value, title = plan
    count = df[column].eq(value).sum()

    indicator = go.Indicator(
        mode="number",
        value=count,
    )

    if not df_compare.empty:
        count_compare = df_compare[column].eq(value).sum()
        indicator = go.Indicator(
            mode="number+delta",
            value=count,
            delta={
                "position": "top",
                "reference": count_compare,
                "valueformat": ".2f",
            },
        )

    fig = go.Figure(data=indicator)
    fig["layout"]["title"] = title

    if not dark_mode:
        fig["layout"]["template"] = pio.templates["journal"]

    return fig


def calculate_retention_rate(df: pd.DataFrame, df_compare: pd.DataFrame, dark_mode: bool) -> go.Figure:
    """Construct string showing retention rate and change vs another date (if comparison data is provided)."""
    migs = df["membership_status"].eq("member in good standing").sum()
    constitutional = df["membership_status"].eq("member").sum()
    rate = (migs / (constitutional + migs)) * 100

    indicator = go.Indicator(
        mode="number",
        value=rate,
        number={"suffix": "%"},
    )

    if not df_compare.empty:
        compare_migs = df_compare["membership_status"].eq("member in good standing").sum()
        compare_constitutional = df_compare["membership_status"].eq("member").sum()
        rate_compare = (compare_migs / (compare_constitutional + compare_migs)) * 100
        indicator = go.Indicator(
            mode="number+delta",
            value=rate,
            delta={"position": "top", "reference": rate_compare, "valueformat": ".2"},
            number={"suffix": "%"},
        )

    fig = go.Figure(data=indicator, layout={"title": "Retention Rate (MIGS / Constitutional)"})

    if not dark_mode:
        fig["layout"]["template"] = pio.templates["journal"]

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
def create_metrics(date_selected: str, date_compare_selected: str, dark_mode: bool) -> (list, go.Figure):
    """Update the numeric metrics shown based on the selected membership list date and compare date (if applicable)."""
    if not date_selected:
        return "", "", "", ""

    metrics_plan = [
        ["membership_type", "lifetime", "Lifetime Members"],
        ["membership_status", "member in good standing", "Members in Good Standing"],
        ["membership_status", "member", "Expiring Members"],
        ["membership_status", "lapsed", "Lapsed Members"],
    ]

    df = selected_data(date_selected)
    df_compare = selected_data(date_compare_selected)

    metric_count_frames = [calculate_metric(df, df_compare, metric_plan, dark_mode) for metric_plan in metrics_plan]
    metric_retention = calculate_retention_rate(df, df_compare, dark_mode)

    return *metric_count_frames, metric_retention


def create_chart(df_field: pd.DataFrame, df_compare_field: pd.DataFrame, title: str, ylabel: str, log: bool) -> go.Figure:
    """Set up html data to show a chart of 1-2 dataframes."""
    chartdf_vc = df_field.value_counts()
    chartdf_compare_vc = df_compare_field.value_counts()

    color, color_compare = COLORS, COLORS
    active_labels = [str(val) for val in chartdf_vc.values]

    if not df_compare_field.empty:
        color, color_compare = COLORS[0], COLORS[5]
        active_labels = [
            f"{count} (+{count - chartdf_compare_vc.get(val, 0)})"
            if count - chartdf_compare_vc.get(val, 0) > 0
            else f"{count} ({count - chartdf_compare_vc.get(val, 0)})"
            for val, count in zip(chartdf_vc.index, chartdf_vc.values)
        ]

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
        ]
    )

    chart.update_layout(title=title, yaxis_title=(ylabel + " (Logarithmic)") if log else ylabel)
    chart.update_yaxes(type="log" if log else None)

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

    df = selected_data(date_selected)
    df_compare = selected_data(date_compare_selected)

    def multiple_choice(df: pd.DataFrame, target_column: str, separator: str) -> pd.DataFrame:
        """Split a character-separated list string into an iterable object."""
        return (
            df[target_column]
            .str.split(separator, expand=True)
            .stack()
            .reset_index(level=1, drop=True)
            .to_frame(target_column)
            .join(df.drop(target_column, axis=1))
        )

    membersdf = df.query('membership_status != "lapsed" and membership_status != "expired"')
    membersdf_compare = (
        df_compare.query('membership_status != "lapsed" and membership_status != "expired"') if "membership_status" in df_compare else pd.DataFrame()
    )

    charts = [
        create_chart(
            df["membership_status"] if "membership_status" in df else pd.DataFrame(),
            df_compare["membership_status"] if "membership_status" in df_compare else pd.DataFrame(),
            "Membership Counts (all-time)",
            "Members",
            False,
        ),
        create_chart(
            df.loc[df["membership_status"] == "member in good standing"]["membership_type"] if "membership_status" in df else pd.DataFrame(),
            df_compare.loc[df_compare["membership_status"] == "member in good standing"]["membership_type"]
            if "membership_status" in df_compare
            else pd.DataFrame(),
            "Dues (members in good standing)",
            "Members",
            True,
        ),
        create_chart(
            membersdf["union_member"] if "union_member" in df else pd.DataFrame(),
            membersdf_compare["union_member"] if "union_member" in df_compare else pd.DataFrame(),
            "Union Membership (not lapsed)",
            "Members",
            True,
        ),
        create_chart(
            membersdf["membership_length"].clip(upper=8) if "membership_length" in df else pd.DataFrame(),
            membersdf_compare["membership_length"].clip(upper=8) if "membership_length" in membersdf_compare else pd.DataFrame(),
            "Length of Membership (0 - 8+yrs, not lapsed)",
            "Members",
            False,
        ),
        create_chart(
            multiple_choice(membersdf, "race", ",")["race"] if "race" in df else pd.DataFrame(),
            multiple_choice(membersdf_compare, "race", ",")["race"] if "race" in membersdf_compare else pd.DataFrame(),
            "Racial Demographics (self-reported)",
            "Members",
            True,
        ),
    ]

    if not dark_mode:
        for chart in charts:
            chart["layout"]["template"] = pio.templates["journal"]

    return charts


@callback(
    Output(component_id="membership_map", component_property="figure"),
    Input(component_id="list_dropdown", component_property="value"),
    Input(component_id="map_column", component_property="value"),
    Input(component_id="color-mode-switch", component_property="value"),
)
def create_map(date_selected: str, selected_column: str, dark_mode: bool):
    """Set up html data to show a map of Maine DSA members."""
    df_map = selected_data(date_selected)

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
            "membership_length": True,
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
    if pathname == "/":
        return timeline
    if pathname == "/list":
        return member_list
    if pathname == "/metrics":
        return metrics
    if pathname == "/graphs":
        return graphs
    if pathname == "/map":
        return member_map

    # If the user tries to reach a different page, return a 404 message
    return html.Div(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ],
        className="p-3 bg-light rounded-3",
    )


if __name__ == "__main__":
    app.run_server(debug=True)
