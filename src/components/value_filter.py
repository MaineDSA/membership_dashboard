import logging
from typing import Literal, TypedDict

import pandas as pd
from dash import Input, Output, callback

from src.utils import scan_lists

FilterKeys = Literal["options", "value"]
FilterDicts = dict[FilterKeys, list[dict]]
ColumnDicts = dict[FilterKeys, str | list[dict]]

logger = logging.getLogger(__name__)


class PivotResult(TypedDict):
    """
    Structured output of a date-focused to metric-focused transformation.

    Attributes:
        timeline (dict):
            Outer keys are metric names (str). Inner dictionaries map dates (str)
            to their respective counts (int) for that specific metric.
            Example: {'metric_a': {'2023-01-01': 5, '2023-01-02': 3}}
        totals (dict): Map each metric name (str) to the sum of all its
            counts (int) across the entire timeline.
            Example: {'metric_a': 8}

    """

    timeline: dict[str, dict[str, int]]
    totals: dict[str, int]


def pivot_with_summary(date_counts: dict[str, pd.Series]) -> PivotResult:
    """
    Transform date-major data into both a metric-timeline and an aggregate summary.

    Args:
        date_counts (dict): A dictionary where keys are dates (str) and values are
            either a dictionary of {metric: count} or a Pandas Series.

    """
    metrics_timeline: dict[str, dict[str, int]] = {}
    metrics_total: dict[str, int] = {}

    for date, values in date_counts.items():
        counts = values.value_counts().items() if hasattr(values, "value_counts") else values.items()

        for metric_hashable, count in counts:
            metric = str(metric_hashable)
            metrics_timeline.setdefault(metric, {})[date] = count
            metrics_total[metric] = metrics_total.get(metric, 0) + count

    return {"timeline": metrics_timeline, "totals": metrics_total}


def get_membership_list_metrics(members: dict[str, pd.DataFrame]) -> dict[str, dict[str, pd.Series]]:
    """Restructure a dictionary of dataframs keyed to dates into a dictionary of pandas column names containing the columns keyed to each date."""
    logger.debug("Calculating metrics for %s membership lists", len(members))
    columns = {column for memb_list in members.values() for column in memb_list.columns}

    return {column: {list_date: memb_list[column] for list_date, memb_list in members.items() if column in memb_list.columns} for column in columns}


@callback(
    output={
        "options": Output("selected-column", "options"),
        "value": Output("selected-column", "value"),
    },
    inputs={
        "date_selected": Input("list-selected", "value"),
    },
)
def update_column_options(date_selected: str) -> ColumnDicts:
    if not date_selected or not scan_lists.MEMB_LISTS:
        return {"options": [], "value": ""}

    df = scan_lists.MEMB_LISTS.get(date_selected, pd.DataFrame())
    cols = list(df.columns)
    if not cols:
        return {"options": [], "value": ""}

    return {"options": [{"label": i, "value": i} for i in cols], "value": "membership_status" if "membership_status" in cols else cols[0]}


@callback(
    output={
        "options": Output("filtered-values", "options"),
        "value": Output("filtered-values", "value"),
    },
    inputs={
        "selected_column": Input("selected-column", "value"),
        "date_selected": Input("list-selected", "value"),
    },
)
def batch_options(selected_column: str, date_selected: str) -> FilterDicts:
    df = scan_lists.MEMB_LISTS.get(date_selected, pd.DataFrame())

    if df.empty or selected_column not in df.columns:
        return {"options": [], "value": []}

    unique_values = sorted(df[selected_column].dropna().unique().tolist())
    options = [{"label": str(v), "value": v} for v in unique_values]

    return {"options": options, "value": unique_values}
