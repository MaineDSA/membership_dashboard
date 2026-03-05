import logging
from typing import Literal, TypedDict

import pandas as pd

from src.utils import scan_lists

FilterKeys = Literal["options", "value"]
FilterDicts = dict[FilterKeys, list]

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


def column_values_for_filter(selected_column: str) -> FilterDicts:
    if not selected_column:
        filters: FilterDicts = {"options": [], "value": []}
        return filters

    membership_value_counts = get_membership_list_metrics(scan_lists.MEMB_LISTS)
    pivot_data = pivot_with_summary(membership_value_counts[selected_column])

    return {"options": [{"label": i, "value": i} for i in pivot_data["totals"]], "value": list(pivot_data["totals"].keys())}
