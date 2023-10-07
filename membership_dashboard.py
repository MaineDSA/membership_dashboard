"""Parse membership lists and construct a membership dashboard showing various graphs and metrics to illustrate changes over time."""

import os
import glob
import zipfile
import argparse
import numpy as np
import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from dash import Dash, html, dash_table, dcc, callback, clientside_callback, Output, Input, State

parser = argparse.ArgumentParser(
                    prog='DSA Membership Dashboard',
                    description="""Parses membership lists and constructs a membership dashboard
                        showing various graphs and metrics to illustrate changes over time."""
                    )
parser.add_argument("-t", "--test", action='store_true', help='Read a limited subset of the most recent lists and run dash in Debug mode')
args = parser.parse_args()

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
    if args.test:
        for count, file in enumerate(files):
            scan_membership_list(os.path.basename(file), os.path.abspath(file))
            if count > 10:
                return
    for file in files:
        scan_membership_list(os.path.basename(file), os.path.abspath(file))


# Initialize the app
scan_all_membership_lists(MEMB_LIST_NAME)
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash(
    external_stylesheets=[dbc.themes.DARKLY, dbc.themes.FLATLY, dbc_css, dbc.icons.FONT_AWESOME],
    # these meta_tags ensure content is scaled correctly on different devices
    # see: https://www.w3schools.com/css/css_rwd_viewport.asp for more
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
)
load_figure_template(["darkly", "flatly"])

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
            html.Span(
                [
                    #dbc.Label(className="fa fa-sun", html_for="color-mode-switch"),
                    dbc.Switch(id="color-mode-switch", value=True, className="d-inline-block ms-1", persistence=True),
                    dbc.Label(className="fa fa-moon", html_for="color-mode-switch"),
                ]
            ),
            width="auto",
            align="center",
        ),
    ]
)

sidebar = html.Div(
    id="sidebar",
    className="dash-bootstrap",
    children=[
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
    ]
)

content = html.Div(id="page-content")

app.layout = dbc.Container([dcc.Location(id="url"), sidebar, content], fluid=True, className="dbc")

timeline = html.Div(
    id="timeline-container",
    className="dash-bootstrap",
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

metrics = html.Div(
    id="metrics-container",
    className="dash-bootstrap",
    children=[
        dbc.Row(
            [
                dbc.Col(dcc.Graph(
                    figure=go.Figure(),
                    id="members_lifetime",
                ),width=6),
                dbc.Col(dcc.Graph(
                    figure=go.Figure(),
                    id="members_migs",
                ),width=6),
            ],
        ),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(
                    figure=go.Figure(),
                    id="members_expiring",
                ),width=6),
                dbc.Col(dcc.Graph(
                    figure=go.Figure(),
                    id="members_lapsed",
                ),width=6),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(
                    figure=go.Figure(),
                    id="metric_retention",
                ),width=6),
            ]
        ),
    ],
)

graphs = html.Div(
    id="graphs-container",
    className="dash-bootstrap",
    children=[
        dbc.Row(
            [
                dbc.Col(dcc.Graph(
                        figure=go.Figure(),
                        id="membership_status",
                ),width=4),
                dbc.Col(dcc.Graph(
                        figure=go.Figure(),
                        id="membership_type",
                ),width=4),
                dbc.Col(dcc.Graph(
                        figure=go.Figure(),
                        id="union_member",
                ),width=4),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(
                        figure=go.Figure(),
                        id="membership_length",
                ),width=6),
                dbc.Col(dcc.Graph(
                        figure=go.Figure(),
                        id="race",
                ),width=6),
            ]
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
    Input(component_id="color-mode-switch", component_property="value")
)
def create_timeline(selected_columns: list, dark_mode: bool):
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
    if not dark_mode:
        timeline_figure["layout"]["template"] = pio.templates["flatly"]

    return timeline_figure


@callback(
    Output(component_id="membership_list", component_property="data"),
    Input(component_id="list_dropdown", component_property="value"),
    Input(component_id="list_compare_dropdown", component_property="value"),
    Input(component_id="color-mode-switch", component_property="value")
)
def create_list(date_selected: str, date_compare_selected: str, dark_mode:bool):
    """Update the list shown based on the selected membership list date."""
    df = selected_data(date_selected)
    df_compare = selected_data(date_compare_selected)
    if not df_compare.empty:
        df = pd.concat([df, df_compare]).reset_index(drop=True).drop_duplicates(subset=['actionkit_id'], keep=False)
    return df.to_dict("records")


def calculate_metric(df, df_compare, plan: list, dark_mode:bool):
    column, value, title = plan
    """Construct string showing value and change (if comparison data is provided)."""
    count = df[column].eq(value).sum()

    indicator = go.Indicator(
        mode = "number",
        value = count,
    )

    if not df_compare.empty:
        count_compare = df_compare[column].eq(value).sum()
        indicator = go.Indicator(
            mode = "number+delta",
            value = count,
            delta =  {'position': "top", 'reference': count - count_compare, 'valueformat':'.2'},
        )

    fig = go.Figure(data=indicator)
    fig["layout"]["title"] = title

    if not dark_mode:
        fig["layout"]["template"] = pio.templates["flatly"]

    return fig

def calculate_retention_rate(df, df_compare, dark_mode:bool):
    """Construct string showing retention rate and change vs another date (if comparison data is provided)."""
    migs = df['membership_status'].eq('member in good standing').sum()
    constitutional = df['membership_status'].eq('member').sum()
    rate = (migs / (constitutional + migs)) * 100

    indicator = go.Indicator(
        mode = "number",
        value = rate,
        number = {'suffix': "%"},
    )

    if not df_compare.empty:
        compare_migs = df_compare['membership_status'].eq('member in good standing').sum()
        compare_constitutional = df_compare['membership_status'].eq('member').sum()
        rate_compare = (compare_migs / (compare_constitutional + compare_migs)) * 100
        indicator = go.Indicator(
            mode = "number+delta",
            value = rate,
            delta = {'position': "top", 'reference': rate_compare, 'valueformat':'.2'},
            number = {'suffix': "%"},
        )

    fig = go.Figure(data=indicator, layout={'title':'Retention Rate (MIGS / Constitutional)'})

    if not dark_mode:
        fig["layout"]["template"] = pio.templates["flatly"]

    return fig


@callback(
    Output(component_id="members_lifetime", component_property="figure"),
    Output(component_id="members_migs", component_property="figure"),
    Output(component_id="members_expiring", component_property="figure"),
    Output(component_id="members_lapsed", component_property="figure"),
    Output(component_id="metric_retention", component_property="figure"),
    Input(component_id="list_dropdown", component_property="value"),
    Input(component_id="list_compare_dropdown", component_property="value"),
    Input(component_id="color-mode-switch", component_property="value")
)
def create_metrics(date_selected: str, date_compare_selected: str, dark_mode:bool):
    """Update the numeric metrics shown based on the selected membership list date and compare date (if applicable)."""
    if not date_selected:
        return "", "", "", ""

    metrics_plan = [
        ['membership_type', 'lifetime', 'Lifetime Members'],
        ['membership_status', 'member in good standing', 'Members in Good Standing'],
        ['membership_status', 'member', 'Expiring Members'],
        ['membership_status', 'lapsed', 'Lapsed Members'],
    ]

    df = selected_data(date_selected)
    df_compare = selected_data(date_compare_selected)

    metric_count_frames = [calculate_metric(df, df_compare, metric_plan, dark_mode) for metric_plan in metrics_plan]
    metric_retention = calculate_retention_rate(df, df_compare, dark_mode)

    return *metric_count_frames, metric_retention


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


@callback(
    Output(component_id="membership_status", component_property="figure"),
    Output(component_id="membership_type", component_property="figure"),
    Output(component_id="union_member", component_property="figure"),
    Output(component_id="membership_length", component_property="figure"),
    Output(component_id="race", component_property="figure"),
    Input(component_id="list_dropdown", component_property="value"),
    Input(component_id="list_compare_dropdown", component_property="value"),
    Input(component_id="color-mode-switch", component_property="value")
)
def create_graphs(date_selected, date_compare_selected, dark_mode: bool):
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

    if not dark_mode:
        chart1["layout"]["template"] = pio.templates["flatly"]
        chart2["layout"]["template"] = pio.templates["flatly"]
        chart3["layout"]["template"] = pio.templates["flatly"]
        chart4["layout"]["template"] = pio.templates["flatly"]
        chart5["layout"]["template"] = pio.templates["flatly"]

    return chart1, chart2, chart3, chart4, chart5


##
## Sidebar
##


clientside_callback(
    """
    (switchOn) => {
       switchOn
         ? document.documentElement.setAttribute('data-bs-theme', 'dark')
         : document.documentElement.setAttribute('data-bs-theme', 'light')
       return window.dash_clientside.no_update
    }
    """,
    Output("color-mode-switch", "id"),
    Input("color-mode-switch", "value"),
)

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
            "Implementation of a map is planned: https://github.com/MaineDSA/MembershipDashboard/issues/8.",
            className="dbc",
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


if __name__ == "__main__":
    app.run_server(debug=args.test)
