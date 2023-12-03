"""Construct a membership dashboard showing various graphs and metrics to illustrate changes over time."""

import pandas as pd
import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from dash import Dash, html, dash_table, dcc, callback, clientside_callback, Output, Input
from scan_membership_lists import get_all_membership_lists, get_membership_list_metrics


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


memb_lists = get_all_membership_lists()
memb_lists_metrics = get_membership_list_metrics()


# pylint: disable-next=consider-using-with
px.set_mapbox_access_token(open(".mapbox_token", encoding="utf8").read())


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
                        dbc.Col(
                            dbc.Label(
                                className="fa fa-sun", html_for="color-mode-switch"
                            )
                        ),
                        dbc.Col(
                            dbc.Switch(
                                id="color-mode-switch",
                                value=True,
                                className="d-inline-block ms-1",
                                persistence=True,
                            )
                        ),
                        dbc.Col(
                            dbc.Label(
                                className="fa fa-moon", html_for="color-mode-switch"
                            )
                        ),
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

app.layout = dbc.Container(
    [dcc.Location(id="url"), sidebar, content], className="dbc dbc-ag-grid", fluid=True
)

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
                "height": "90vh",
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
            columns=[
                {"name": i, "id": i, "selectable": True}
                for i in memb_lists[list(memb_lists.keys())[0]].columns
            ],
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
                "overflowY": "auto",
                "overflowX": "auto",
                "padding-left": "-.5em",
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
                    ),
                    width=6,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="members_migs",
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
                        id="members_expiring",
                    ),
                    width=6,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="members_lapsed",
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
                    ),
                    width=4,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="membership_type",
                    ),
                    width=4,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="union_member",
                    ),
                    width=4,
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="membership_length",
                    ),
                    width=6,
                ),
                dbc.Col(
                    dcc.Graph(
                        figure=go.Figure(),
                        id="race",
                    ),
                    width=6,
                ),
            ]
        ),
    ],
)

member_map = html.Div(
    id="map-container",
    children=[
        dcc.Graph(
            figure=go.Figure(),
            id="membership_map",
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
            value_counts = memb_lists_metrics[selected_column][date].value_counts()
            for value, count in value_counts.items():
                if value not in selected_metrics[selected_column]:
                    selected_metrics[selected_column][value] = {}
                selected_metrics[selected_column][value][date] = count
        for _, metric in selected_metrics.items():
            for count, value in enumerate(metric):
                timeline_figure.add_trace(
                    go.Scatter(
                        name=value,
                        x=list(metric[value].keys()),
                        y=list(metric[value].values()),
                        mode="lines",
                        marker_color=COLORS[count % len(COLORS)],
                    )
                )
    timeline_figure.update_layout(
        title="Membership Trends Timeline", yaxis_title="Members"
    )
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
    if not df_compare.empty:
        df = (
            pd.concat([df, df_compare])
            .reset_index(drop=False)
            .drop_duplicates(
                subset=["actionkit_id", "membership_status", "membership_type"],
                keep=False,
            )
            .drop_duplicates(subset=["actionkit_id"])
        )
    return df.to_dict("records")


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
        compare_migs = (
            df_compare["membership_status"].eq("member in good standing").sum()
        )
        compare_constitutional = df_compare["membership_status"].eq("member").sum()
        rate_compare = (compare_migs / (compare_constitutional + compare_migs)) * 100
        indicator = go.Indicator(
            mode="number+delta",
            value=rate,
            delta={"position": "top", "reference": rate_compare, "valueformat": ".2"},
            number={"suffix": "%"},
        )

    fig = go.Figure(
        data=indicator, layout={"title": "Retention Rate (MIGS / Constitutional)"}
    )

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

    metric_count_frames = [
        calculate_metric(df, df_compare, metric_plan, dark_mode)
        for metric_plan in metrics_plan
    ]
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

    if log:
        chart.update_yaxes(type="log")
        ylabel = ylabel + " (Logarithmic)"

    chart.update_layout(title=title, yaxis_title=ylabel)

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
def create_graphs(date_selected: str, date_compare_selected: str, dark_mode: bool) -> ([go.Figure] * 5):
    """Update the graphs shown based on the selected membership list date and compare date (if applicable)."""
    if not date_selected:
        return go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure()

    df = selected_data(date_selected)
    df_compare = selected_data(date_compare_selected)

    chart1 = create_chart(
        df["membership_status"] if "membership_status" in df else pd.DataFrame(),
        df_compare["membership_status"]
        if "membership_status" in df_compare
        else pd.DataFrame(),
        "Membership Counts (all-time)",
        "Members",
        False,
    )

    chart2 = create_chart(
        df.loc[df["membership_status"] == "member in good standing"]["membership_type"]
        if "membership_status" in df
        else pd.DataFrame(),
        df_compare.loc[df_compare["membership_status"] == "member in good standing"][
            "membership_type"
        ]
        if "membership_status" in df_compare
        else pd.DataFrame(),
        "Dues (members in good standing)",
        "Members",
        True,
    )

    membersdf = df.query(
        'membership_status != "lapsed" and membership_status != "expired"'
    )
    membersdf_compare = (
        df_compare.query(
            'membership_status != "lapsed" and membership_status != "expired"'
        )
        if "membership_status" in df_compare
        else pd.DataFrame()
    )

    chart3 = create_chart(
        membersdf["union_member"] if "union_member" in df else pd.DataFrame(),
        membersdf_compare["union_member"]
        if "union_member" in df_compare
        else pd.DataFrame(),
        "Union Membership (not lapsed)",
        "Members",
        True,
    )

    chart4 = create_chart(
        membersdf["membership_length"].clip(upper=8)
        if "membership_length" in df
        else pd.DataFrame(),
        membersdf_compare["membership_length"].clip(upper=8)
        if "membership_length" in membersdf_compare
        else pd.DataFrame(),
        "Length of Membership (0 - 8+yrs, not lapsed)",
        "Members",
        False,
    )

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

    chart5 = create_chart(
        multiple_choice(membersdf, "race", ",")["race"]
        if "race" in df
        else pd.DataFrame(),
        multiple_choice(membersdf_compare, "race", ",")["race"]
        if "race" in membersdf_compare
        else pd.DataFrame(),
        "Racial Demographics (self-reported)",
        "Members",
        True,
    )

    if not dark_mode:
        chart1["layout"]["template"] = pio.templates["journal"]
        chart2["layout"]["template"] = pio.templates["journal"]
        chart3["layout"]["template"] = pio.templates["journal"]
        chart4["layout"]["template"] = pio.templates["journal"]
        chart5["layout"]["template"] = pio.templates["journal"]

    return chart1, chart2, chart3, chart4, chart5


@callback(
    Output(component_id="membership_map", component_property="figure"),
    Input(component_id="list_dropdown", component_property="value"),
    Input(component_id="color-mode-switch", component_property="value"),
)
def create_map(date_selected: str, dark_mode: bool):
    """Set up html data to show a map of Maine DSA members."""
    df_map = selected_data(date_selected)
    df_map[["lon", "lat"]] = pd.DataFrame(
        df_map["latlon"].tolist(), index=df_map.index
    )

    map_figure = px.scatter_mapbox(
        df_map,
        lat="lat",
        lon="lon",
        hover_name="first_name",
        hover_data=[
            "first_name",
            "last_name",
            "best_phone",
            "membership_type",
            "membership_status",
        ],
        color="membership_status",
        color_discrete_sequence=COLORS,
        zoom=6,
        height=1100,
    )
    display_mode = "light"
    if dark_mode:
        display_mode = "dark"
    map_figure.update_layout(mapbox_style=display_mode)
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
