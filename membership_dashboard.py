"""Parse membership lists and construct a membership dashboard showing various graphs and metrics to illustrate changes over time."""

import os
import glob
import zipfile
import numpy as np
import pandas as pd
from dash import Dash, html, dash_table, dcc, callback, Output, Input, State
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

TESTMODE = False
"""If set to true, a limited number of lists will be read and the interface will be run in Debug mode."""

MEMB_LIST_NAME = "maine_membership_list"
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

memb_lists = {}
"""Contains data organized as column:value pairs within a dict of membership list dates."""
memb_lists_metrics = {}
"""Contains data organized as date:value pairs within a dict of original columns names."""


def membership_length(date: str, **kwargs):
    """Return an integer representing how many years between the supplied dates."""
    return (pd.to_datetime(kwargs["list_date"]) - pd.to_datetime(date)) // pd.Timedelta(
        days=365
    )


def fill_empties(date_formatted, column, default):
    """Fill any empty values in the specified column with the supplied default value."""
    if column not in memb_lists[date_formatted]:
        memb_lists[date_formatted][column] = default
    memb_lists[date_formatted][column] = memb_lists[date_formatted][column].fillna(
        default
    )


def data_fixes(date_formatted):
    """Standardize data, taking into account changes in membership list format."""
    memb_lists[date_formatted].columns = memb_lists[date_formatted].columns.str.lower()
    columns_to_fill = {
        "akid": "actionkit_id",
        "ak_id": "actionkit_id",
        "billing_city": "city",
        "accomodations": "accommodations",
    }
    for old, new in columns_to_fill.items():
        if (new not in memb_lists[date_formatted]) & (
            old in memb_lists[date_formatted]
        ):
            memb_lists[date_formatted][new] = memb_lists[date_formatted][old]
    memb_lists[date_formatted].set_index("actionkit_id")
    memb_lists[date_formatted]["membership_length"] = memb_lists[date_formatted][
        "join_date"
    ].apply(membership_length, list_date=date_formatted)
    if "membership_status" not in memb_lists[date_formatted]:
        memb_lists[date_formatted]["membership_status"] = np.where(
            memb_lists[date_formatted]["memb_status"] == "M",
            "member in good standing",
            "n/a",
        )
    memb_lists[date_formatted]["membership_status"] = (
        memb_lists[date_formatted]["membership_status"]
        .replace({"expired": "lapsed"})
        .str.lower()
    )
    memb_lists[date_formatted]["membership_type"] = np.where(
        memb_lists[date_formatted]["xdate"] == "2099-11-01",
        "lifetime",
        memb_lists[date_formatted]["membership_type"].str.lower(),
    )
    memb_lists[date_formatted]["membership_type"] = (
        memb_lists[date_formatted]["membership_type"]
        .replace({"annual": "yearly"})
        .str.lower()
    )
    fill_empties(date_formatted, "do_not_call", False)
    fill_empties(date_formatted, "p2ptext_optout", False)
    fill_empties(date_formatted, "race", "unknown")
    fill_empties(date_formatted, "union_member", "unknown")
    memb_lists[date_formatted]["union_member"] = (
        memb_lists[date_formatted]["union_member"]
        .replace(
            {
                0: "No",
                1: "Yes",
                "Yes, retired union member": "Yes, retired",
                "Yes, current union member": "Yes, current",
                "Currently organizing my workplace": "No, organizing",
                "No, but former union member": "No, former",
                "No, not a union member": "No",
            }
        )
        .str.lower()
    )
    fill_empties(date_formatted, "accommodations", "no")
    memb_lists[date_formatted]["accommodations"] = (
        memb_lists[date_formatted]["accommodations"]
        .str.lower()
        .replace(
            {
                "n/a": None,
                "no.": None,
                "no": None,
            }
        )
    )


def scan_membership_list(filename: str, filepath: str):
    """Scan the requested membership list and add data to memb_lists and memb_lists_metrics."""
    date_from_name = pd.to_datetime(
        os.path.splitext(filename)[0].split("_")[3], format="%Y%m%d"
    ).date()
    if not date_from_name:
        print(f"No date detected in name of {filename}. Skipping file.")
        return

    with zipfile.ZipFile(filepath) as memb_list_zip:
        with memb_list_zip.open(f"{MEMB_LIST_NAME}.csv") as memb_list:
            print(f"Loading data from {MEMB_LIST_NAME}.csv in {filename}.")
            date_formatted = date_from_name.isoformat()

            memb_lists[date_formatted] = pd.read_csv(memb_list, header=0)
            data_fixes(date_formatted)

            for column in memb_lists[date_formatted].columns:
                if not column in memb_lists_metrics:
                    memb_lists_metrics[column] = {}
                memb_lists_metrics[column][date_formatted] = memb_lists[date_formatted][
                    column
                ]


def scan_all_membership_lists(directory: str):
    """Scan all zip files in the supplied directory and call scan_membership_list on each."""
    print(f"Scanning {directory} for zipped membership lists.")
    files = sorted(
        glob.glob(os.path.join(directory, "**/*.zip"), recursive=True), reverse=True
    )
    if TESTMODE:
        for count, file in enumerate(files):
            scan_membership_list(os.path.basename(file), os.path.abspath(file))
            if count > 10:
                return
    for file in files:
        scan_membership_list(os.path.basename(file), os.path.abspath(file))


# Initialize the app
scan_all_membership_lists(MEMB_LIST_NAME)
app = Dash(
    external_stylesheets=[dbc.themes.DARKLY],
    # these meta_tags ensure content is scaled correctly on different devices
    # see: https://www.w3schools.com/css/css_rwd_viewport.asp for more
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
)
load_figure_template(["darkly"])

# we use the Row and Col components to construct the sidebar header
# it consists of a title, and a toggle, the latter is hidden on large screens
sidebar_header = dbc.Row(
    [
        dbc.Col(
            html.Img(
                src=r"https://www.mainedsa.org/wp-content/uploads/2023/07/Maine-DSA-Moose-with-Rose-Logo.svg",
                alt="Red Maine DSA logo of a moose holding a rose in its mouth under the text Maine DSA",
            )
        ),
        dbc.Col(
            [
                dbc.Button(
                    # use the Bootstrap navbar-toggler classes to style
                    html.Span(className="navbar-toggler-icon"),
                    className="navbar-toggler",
                    # the navbar-toggler classes don't set color
                    style={
                        "color": "rgba(0,0,0,.5)",
                        "border-color": "rgba(0,0,0,.1)",
                    },
                    id="navbar-toggle",
                ),
                dbc.Button(
                    # use the Bootstrap navbar-toggler classes to style
                    html.Span(className="navbar-toggler-icon"),
                    className="navbar-toggler",
                    # the navbar-toggler classes don't set color
                    style={
                        "color": "rgba(0,0,0,.5)",
                        "border-color": "rgba(0,0,0,.1)",
                    },
                    id="sidebar-toggle",
                ),
            ],
            # the column containing the toggle will be only as wide as the
            # toggle, resulting in the toggle being right aligned
            width="auto",
            # vertically align the toggle in the center
            align="center",
        ),
    ]
)

sidebar = html.Div(
    [
        sidebar_header,
        # we wrap the horizontal rule and short blurb in a div that can be
        # hidden on a small screen
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
            className="dash-bootstrap",
        ),
        html.Div(
            [
                html.P("Active List"),
            ],
            id="list_dropdown_label",
        ),
        dcc.Dropdown(
            options=list(memb_lists.keys()),
            value="",
            id="list_compare_dropdown",
            className="dash-bootstrap",
        ),
        html.Div(
            [
                html.P("Compare To"),
            ],
            id="list_compare_dropdown_label",
        ),
        # use the Collapse component to animate hiding / revealing links
        dbc.Collapse(
            dbc.Nav(
                [
                    dbc.NavLink("Timeline", href="/", active="exact"),
                    dbc.NavLink("List", href="/list", active="exact"),
                    dbc.NavLink("Metrics", href="/metrics", active="exact"),
                    dbc.NavLink("Graphs", href="/graphs", active="exact"),
                    dbc.NavLink("Map", href="/map", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
            id="collapse",
        ),
    ],
    id="sidebar",
)

content = html.Div(id="page-content")

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

timeline = html.Div(
    id="timeline-container",
    children=[
        dcc.Dropdown(
            options=list(memb_lists_metrics.keys()),
            value=["membership_status"],
            multi=True,
            id="timeline_columns",
            className="dash-bootstrap",
        ),
        dcc.Graph(
            figure={},
            id="membership_timeline",
            className="dash-bootstrap",
            style={
                "display": "inline-block",
                "width": "100%",
                "padding-left": "-1em",
                "padding-right": "-1em",
                "padding-bottom": "-1em",
            },
        ),
    ],
)

member_list_page = html.Div(
    id="list-container",
    className="dbc",
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


def create_jumbotron(title, index):
    """Set up html data to show a jumbotron with title and value for metrics page."""
    return dbc.Col(
        html.Div(
            [
                html.H3(title, className="display-8"),
                html.Hr(className="my-2"),
                html.P("0", id=index),
            ],
            className="h-100 p-5 text-white bg-dark rounded-3",
        ),
        md=6,
    )


lifetime_jumbotron = create_jumbotron("Lifetime Members", "members_lifetime")
migs_jumbotron = create_jumbotron("Members in Good Standing", "members_migs")
expiring_jumbotron = create_jumbotron("Expiring Members", "members_expiring")
lapsed_jumbotron = create_jumbotron("Lapsed Members", "members_lapsed")
retention_jumbotron = create_jumbotron("Retention Rate", "metric_retention")

metrics = dbc.Col(
    [
        dbc.Row(
            [lifetime_jumbotron, migs_jumbotron], className="align-items-md-stretch"
        ),
        dbc.Row(
            [expiring_jumbotron, lapsed_jumbotron], className="align-items-md-stretch"
        ),
        dbc.Row(
            [retention_jumbotron], className="align-items-md-stretch"
        ),
    ],
    className="d-grid gap-4",
)


style_graphs_2 = {"display": "inline-block", "width": "50%"}
style_graphs_3 = {"display": "inline-block", "width": "33.33%"}

graphs = html.Div(
    id="graphs-container",
    children=[
        dcc.Graph(
            figure={},
            id="membership_status",
            className="dash-bootstrap",
            style=style_graphs_3,
        ),
        dcc.Graph(
            figure={},
            id="membership_type",
            className="dash-bootstrap",
            style=style_graphs_3,
        ),
        dcc.Graph(
            figure={},
            id="union_member",
            className="dash-bootstrap",
            style=style_graphs_3,
        ),
        dcc.Graph(
            figure={},
            id="membership_length",
            className="dash-bootstrap",
            style=style_graphs_2,
        ),
        dcc.Graph(
            figure={}, id="race", className="dash-bootstrap", style=style_graphs_2
        ),
    ],
)


def selected_data(child: str):
    """Return a pandas dataframe, either empty or containing a membership list."""
    return memb_lists[child] if child else pd.DataFrame()


##
## Pages
##


@callback(
    Output(component_id="membership_timeline", component_property="figure"),
    Input(component_id="timeline_columns", component_property="value"),
)
def update_timeline(selected_columns: list):
    """Update the timeline plotting selected columns."""
    timeline_figure = go.Figure()
    selected_metrics = {}
    for selected_column in selected_columns:
        selected_metrics[selected_column] = {}
        for date in memb_lists_metrics[selected_column]:
            value_counts = memb_lists_metrics[selected_column][date].value_counts()
            for value, count in value_counts.items():
                if not value in selected_metrics[selected_column]:
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

    return timeline_figure


@callback(
    Output(component_id="membership_list", component_property="data"),
    Input(component_id="list_dropdown", component_property="value"),
    Input(component_id="list_compare_dropdown", component_property="value"),
)
def update_list(date_selected: str, date_compare_selected: str):
    """Update the list shown based on the selected membership list date."""
    df = selected_data(date_selected)
    df_compare = selected_data(date_compare_selected)

    return df.to_dict("records")


@callback(
    Output(component_id="members_lifetime", component_property="children"),
    Output(component_id="members_migs", component_property="children"),
    Output(component_id="members_expiring", component_property="children"),
    Output(component_id="members_lapsed", component_property="children"),
    Output(component_id="metric_retention", component_property="children"),
    Input(component_id="list_dropdown", component_property="value"),
    Input(component_id="list_compare_dropdown", component_property="value"),
)
def update_metrics(date_selected: str, date_compare_selected: str):
    """Update the numeric metrics shown based on the selected membership list date and compare date (if applicable)."""
    if not date_selected:
        return "", "", "", ""

    df = selected_data(date_selected)
    df_compare = selected_data(date_compare_selected)

    def calculate_metric(df, df_compare, column: str, value: str):
        """Construct string showing value and change (if comparison data is provided)."""
        count = df[column].eq(value).sum()
        if not df_compare.empty:
            count_compare = df_compare[column].eq(value).sum()
            count_delta = count - count_compare
            if count_delta > 0:
                return f"{count} (+{count_delta})"
            if count_delta < 0:
                return f"{count} ({count_delta})"
        return f"{count}"

    def calculate_retention_rate(df, df_compare):
        """Construct string showing retention rate and change vs another date (if comparison data is provided)."""
        migs = df['membership_status'].eq('member in good standing').sum()
        constitutional = df['membership_status'].eq('member').sum()
        rate = (migs / (constitutional + migs)) * 100
        if not df_compare.empty:
            compare_migs = df_compare['membership_status'].eq('member in good standing').sum()
            compare_constitutional = df_compare['membership_status'].eq('member').sum()
            rate_delta = rate - ((compare_migs / (compare_constitutional + compare_migs)) * 100)
            if rate_delta > 0:
                return "{:0.2f}% (+{:0.2f}%)".format(rate, rate_delta)
            if rate_delta < 0:
                return "{:0.2f}% ({:0.2f}%)".format(rate, rate_delta)
        return "{:0.2f}%".format(rate)

    num1 = calculate_metric(df, df_compare, "membership_type", "lifetime")
    num2 = calculate_metric(
        df, df_compare, "membership_status", "member in good standing"
    )
    num3 = calculate_metric(df, df_compare, "membership_status", "member")
    num4 = calculate_metric(df, df_compare, "membership_status", "lapsed")
    num5 = calculate_retention_rate(df, df_compare)

    return num1, num2, num3, num4, num5


@callback(
    Output(component_id="membership_status", component_property="figure"),
    Output(component_id="membership_type", component_property="figure"),
    Output(component_id="union_member", component_property="figure"),
    Output(component_id="membership_length", component_property="figure"),
    Output(component_id="race", component_property="figure"),
    Input(component_id="list_dropdown", component_property="value"),
    Input(component_id="list_compare_dropdown", component_property="value"),
)
def update_graph(date_selected, date_compare_selected):
    """Update the graphs shown based on the selected membership list date and compare date (if applicable)."""

    if not date_selected:
        return go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure()

    df = selected_data(date_selected)
    df_compare = selected_data(date_compare_selected)

    def create_chart(df_field, df_compare_field, title: str, ylabel: str, log: bool):
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

    def multiple_choice(df, target_column: str, separator: str):
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

    return chart1, chart2, chart3, chart4, chart5


##
## Sidebar
##


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    """Display the correct page based on the user's navigation path."""
    if pathname == "/":
        return timeline
    if pathname == "/list":
        return member_list_page
    if pathname == "/metrics":
        return metrics
    if pathname == "/graphs":
        return graphs
    if pathname == "/map":
        return html.P(
            "Implementation of a map is planned: https://github.com/MaineDSA/MembershipDashboard/issues/8."
        )
    # If the user tries to reach a different page, return a 404 message
    return html.Div(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ],
        className="p-3 bg-light rounded-3",
    )


@app.callback(
    Output("sidebar", "className"),
    [Input("sidebar-toggle", "n_clicks")],
    [State("sidebar", "className")],
)
def toggle_classname(n, classname):
    """Assign CSS class to sidebar based on whether it's collapsed or expanded."""
    if n and classname == "":
        return "collapsed"
    return ""


@app.callback(
    Output("collapse", "is_open"),
    [Input("navbar-toggle", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    """Handle expanding/collapsing the sidebar when the button is clicked."""
    if n:
        return not is_open
    return is_open


if __name__ == "__main__":
    app.run_server(debug=TESTMODE)
