"""Parse all membership lists into pandas dataframes for display on dashboard"""

import os
import glob
import zipfile
import numpy as np
import pandas as pd


MEMB_LIST_NAME = "maine_membership_list"


memb_lists = {}
"""Contains data organized as column:value pairs within a dict of membership list dates."""
memb_lists_metrics = {}
"""Contains data organized as date:value pairs within a dict of original columns names."""


def membership_length(date: str, **kwargs) -> int:
    """Return an integer representing how many years between the supplied dates."""
    return (pd.to_datetime(kwargs["list_date"]) - pd.to_datetime(date)) // pd.Timedelta(
        days=365
    )


def fill_empties(date_formatted: str, column: str, default):
    """Fill any empty values in the specified column with the supplied default value."""
    if column not in memb_lists[date_formatted]:
        memb_lists[date_formatted][column] = default
    memb_lists[date_formatted][column] = memb_lists[date_formatted][column].fillna(
        default
    )


def data_fixes(date_formatted: str):
    """Standardize data, taking into account changes in membership list format."""
    memb_lists[date_formatted].columns = memb_lists[date_formatted].columns.str.lower()
    columns_to_fill = {
        "billing_city": "city",
        "akid": "actionkit_id",
        "ak_id": "actionkit_id",
        "accomodations": "accommodations",
        "annual_recurring_dues_status": "yearly_dues_status",
    }
    for old, new in columns_to_fill.items():
        if (new not in memb_lists[date_formatted]) & (
            old in memb_lists[date_formatted]
        ):
            memb_lists[date_formatted][new] = memb_lists[date_formatted][old]
            memb_lists[date_formatted] = memb_lists[date_formatted].drop(old, axis=1)

    memb_lists[date_formatted].set_index("actionkit_id")
    memb_lists[date_formatted]["membership_length"] = memb_lists[date_formatted][
        "join_date"
    ].apply(membership_length, list_date=date_formatted)
    fill_empties(date_formatted, "memb_status", 'unknown')
    if "membership_status" not in memb_lists[date_formatted]:
        if 'xdate' in memb_lists[date_formatted]:
            memb_lists[date_formatted]["membership_status"] = np.where(
                memb_lists[date_formatted]["xdate"] < date_formatted,
                "member in good standing",
                "unknown",
            )
    memb_lists[date_formatted]["membership_status"] = (
        memb_lists[date_formatted]["membership_status"]
        .replace({"expired": "lapsed"})
        .str.lower()
    )
    fill_empties(date_formatted, "membership_type", "unknown")
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


def scan_all_membership_lists() -> (str, str):
    """Scan all zip files and call scan_membership_list on each."""
    print(f"Scanning {MEMB_LIST_NAME} for zipped membership lists.")
    files = sorted(
        glob.glob(os.path.join(MEMB_LIST_NAME, "**/*.zip"), recursive=True), reverse=True
    )
    for file in files:
        scan_membership_list(os.path.basename(file), os.path.abspath(file))

    return memb_lists, memb_lists_metrics
