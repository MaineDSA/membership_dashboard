import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, callback, html
from dash.dash_table.DataTable import DataTable

from src.components import colors, sidebar
from src.utils import scan_lists, schema

ListFigures = tuple[list[dict], list]

dash.register_page(__name__, path="/list", title=f"Membership Dashboard: {__name__.title()}", order=1)

membership_list = html.Div(
    children=[
        DataTable(
            data=[],
            columns=[{"name": i, "id": i, "selectable": True} for i in schema.schema.columns],
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
                "height": "86svh",
                "overflowY": "auto",
                "overflowX": "auto",
            },
            id="list",
        ),
    ],
)


def layout() -> dbc.Row:
    return dbc.Row([dbc.Col(sidebar.sidebar(), width=2), dbc.Col(membership_list, width=10)], className="dbc", style={"margin": "1em"})


@callback(
    output={
        "timeline": [
            Output(component_id="list", component_property="data"),
            Output(component_id="list", component_property="style_data_conditional"),
        ],
    },
    inputs={
        "date_selected": Input(component_id="list-selected", component_property="value"),
        "date_compare_selected": Input(component_id="list-compare", component_property="value"),
    },
)
def create_list(date_selected: str, date_compare_selected: str) -> ListFigures:
    """Update the list shown based on the selected membership list date."""
    df = scan_lists.MEMB_LISTS.get(date_selected, pd.DataFrame())
    df_compare = scan_lists.MEMB_LISTS.get(date_compare_selected, pd.DataFrame())

    if df_compare.empty:
        df.reset_index(drop=False)
        return df.to_dict("records"), []

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
        for query in [
            {"date": date_compare_selected, "color": colors.COMPARE_COLORS[0]},
            {"date": date_selected, "color": colors.COMPARE_COLORS[1]},
        ]
    ]

    figures: ListFigures = (records, conditional_style)

    return figures
