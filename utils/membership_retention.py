"""Provides utility functions for calculating membership retention of various cohorts with varying levels of resolution"""

import pandas as pd

COUNTING_COLUMN = "zip"
JOIN_YEAR = "join_year"
JOIN_QUARTER = "join_quarter"
MEMBERSHIP_LENGTH_YEARS = "membership_length_years"
MEMBERSHIP_LENGTH_MONTHS = "membership_length_months"


# These functions are based on the work of @bunsenmcdubbs:
# https://github.com/bunsenmcdubbs/dsa_retention/blob/main/retention.ipynb


def retention_year(df: pd.DataFrame):
    """Calculate membership retention based on year each member joined, with a resolution of years"""
    return (
        df.pivot_table(index=[JOIN_YEAR], columns=[MEMBERSHIP_LENGTH_YEARS], values=COUNTING_COLUMN, fill_value=0, aggfunc=len)
        .transpose()[::-1]
        .cumsum()[::-1]
        .transpose()
        .replace(to_replace=0, value=None)
    )


def retention_mos(df: pd.DataFrame):
    """Calculate membership retention based on year each member joined, with a resolution of months"""
    return (
        df.pivot_table(index=[JOIN_YEAR], columns=[MEMBERSHIP_LENGTH_MONTHS], values=COUNTING_COLUMN, fill_value=0, aggfunc=len)
        .transpose()[::-1]
        .cumsum()[::-1]
        .transpose()
        .replace(to_replace=0, value=None)
    )


def retention_pct_year(df: pd.DataFrame):
    """Calculate percentage of membership retention based on year each member joined, with a resolution of years"""
    pivot = df.pivot_table(index=[JOIN_YEAR], columns=[MEMBERSHIP_LENGTH_YEARS], values=COUNTING_COLUMN, fill_value=0, aggfunc=len).transpose()[::-1]
    return (pivot.cumsum() / pivot.sum())[::-1].transpose().replace(to_replace=0, value=None)


def retention_pct_mos(df: pd.DataFrame):
    """Calculate percentage of membership retention based on year each member joined, with a resolution of months"""
    pivot = df.pivot_table(index=[JOIN_YEAR], columns=[MEMBERSHIP_LENGTH_MONTHS], values=COUNTING_COLUMN, fill_value=0, aggfunc=len).transpose()[::-1]
    return (pivot.cumsum() / pivot.sum())[::-1].transpose().replace(to_replace=0, value=None)


def retention_pct_quarter(df: pd.DataFrame):
    """Calculate percentage of membership retention based on quich quarter each member joined, with a resolution of years"""
    pivot = df.pivot_table(index=[JOIN_QUARTER], columns=[MEMBERSHIP_LENGTH_YEARS], values=COUNTING_COLUMN, fill_value=0, aggfunc=len).transpose()[::-1]
    return (
        (pivot.cumsum() / pivot.sum())[::-1].transpose().replace(to_replace=0, value=None).infer_objects(copy=False).interpolate(limit=1, limit_area="inside")
    )
