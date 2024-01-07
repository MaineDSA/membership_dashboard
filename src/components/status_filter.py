import dash_bootstrap_components as dbc
from dash import dcc

from utils.schema import ColumnValidation


def status_filter() -> dcc.Checklist:
    return dcc.Checklist(
        ColumnValidation.MEMBERSHIP_STATUS,
        ColumnValidation.MEMBERSHIP_STATUS,
        id="status-filter",
        inline=True,
    )


def status_filter_col() -> dbc.Col:
    return dbc.Col(
        status_filter(),
        width="auto",
    )
