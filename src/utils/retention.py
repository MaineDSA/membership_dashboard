"""Provides utility functions for calculating membership retention of various cohorts with varying levels of resolution."""

from enum import Enum

import pandas as pd


class Columns(Enum):
    """Strings representing formatted column names."""

    COUNTING_COLUMN = "zip"
    JOIN_YEAR = "join_year"
    JOIN_QUARTER = "join_quarter"
    MEMBERSHIP_LENGTH_YEARS = "membership_length_years"
    MEMBERSHIP_LENGTH_MONTHS = "membership_length_months"


# These functions are based on the work of @bunsenmcdubbs:
# https://github.com/bunsenmcdubbs/dsa_retention/blob/main/retention.ipynb


def retention_pivot(df: pd.DataFrame, join_interval: str, membership_length: str) -> pd.DataFrame:
    """Return the transposed pivot table to be used in other retention functions."""
    return df.pivot_table(
        index=[join_interval],
        columns=[membership_length],
        values=Columns.COUNTING_COLUMN,
        fill_value=0,
        aggfunc=len,
    ).transpose()[::-1]


def retention_origin(df: pd.DataFrame, join_year: str, length: str) -> pd.DataFrame:
    """
    Construct a dataframe of membership data showing the number of members who joined each year who are still in good standing.

    Params:
        df: a dataframe containing a membership list
        join_year: the title of a dataframe column containing the year that each member joined
        length: the title of a dataframe column containing an integer representing the length of membership
    """
    return retention_pivot(df, join_year, length).cumsum()[::-1].transpose().replace(to_replace=0, value=None)


def retention_year(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate membership retention based on year each member joined, with a resolution of years."""
    return retention_origin(df, Columns.JOIN_YEAR, Columns.MEMBERSHIP_LENGTH_YEARS)


def retention_mos(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate membership retention based on year each member joined, with a resolution of months."""
    return retention_origin(df, Columns.JOIN_YEAR, Columns.MEMBERSHIP_LENGTH_MONTHS)


def retention_pct_origin(df: pd.DataFrame, join_year: str, length: str) -> pd.DataFrame:
    """
    Construct a dataframe of membership data showing the percentage of members who joined each year who are still in good standing.

    Params:
        df: a dataframe containing a membership list
        join_year: the title of a dataframe column containing the year that each member joined
        length: the title of a dataframe column containing an integer representing the length of membership
    """
    pivot = retention_pivot(df, join_year, length)
    return (pivot.cumsum() / pivot.sum())[::-1].transpose().replace(to_replace=0, value=None)


def retention_pct_year(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate percentage of membership retention based on year each member joined, with a resolution of years."""
    return retention_pct_origin(df, Columns.JOIN_YEAR, Columns.MEMBERSHIP_LENGTH_YEARS)


def retention_pct_mos(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate percentage of membership retention based on year each member joined, with a resolution of months."""
    return retention_pct_origin(df, Columns.JOIN_YEAR, Columns.MEMBERSHIP_LENGTH_MONTHS)


def retention_pct_quarter(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate percentage of membership retention based on quich quarter each member joined, with a resolution of years."""
    pivot = retention_pivot(df, Columns.JOIN_QUARTER, Columns.MEMBERSHIP_LENGTH_YEARS)
    return (
        (pivot.cumsum() / pivot.sum())[::-1].transpose().replace(to_replace=0, value=None).infer_objects().interpolate(limit=1, limit_area="inside")
    )
