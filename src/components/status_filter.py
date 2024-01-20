import dash_bootstrap_components as dbc
from dash import dcc

from src.utils.schema import ColumnValidation


def status_filter_col() -> dbc.Col:
    return dbc.Col(
        dcc.Checklist(
            ColumnValidation.MEMBERSHIP_STATUS,
            ColumnValidation.MEMBERSHIP_STATUS,
            id="status-filter",
            inline=True,
        ),
        width="auto",
    )
