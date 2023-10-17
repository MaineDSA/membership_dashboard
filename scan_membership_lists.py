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


def data_cleaning(date_formatted:str) -> pd.DataFrame:
    """Clean and standardize dataframe according to specified rules."""
    df = memb_lists[date_formatted].copy()  # To avoid modifying original data
    # Ensure column names are lowercase
    df.columns = df.columns.str.lower()

    # Mapping of old column names to new ones
    column_mapping = {
        "billing_city": "city",
        "akid": "actionkit_id",
        "ak_id": "actionkit_id",
        "accomodations": "accommodations",
        "annual_recurring_dues_status": "yearly_dues_status",
    }

    # Rename the old columns to new names
    for old, new in column_mapping.items():
        if (new not in df.columns) & (old in df.columns):
            df[new] = df[old]
            df = df.drop(old, axis=1)

    df.set_index("actionkit_id", inplace=True)

    # Apply the membership_length function to join_date
    df["membership_length"] = df["join_date"].apply(membership_length, list_date=date_formatted)

    # Standardize other columns
    for col, default in [("memb_status", "unknown"), ("membership_type", "unknown"),
                         ("do_not_call", False), ("p2ptext_optout", False), ("race", "unknown"),
                         ("union_member", "unknown"), ("accommodations", "no")]:
        df[col] = df.get(col, default)
        df[col] = df[col].fillna(default)

    # Standardize membership_status column
    if ("membership_status" not in df.columns) & ("xdate" in df.columns):
        df["membership_status"] = np.where(
            df["xdate"] < date_formatted,
            "member in good standing",
            "unknown",
        )
    df["membership_status"] = (
        df.get("membership_status", "unknown")
        .replace({"annual": "yearly", "expired": "lapsed"})
        .str.lower()
    )

    df["accommodations"] = (
        df.get("accommodations", "no")
        .str.lower()
        .replace(
            {
                "none": None,
                "n/a": None,
                "no.": None,
                "no": None,
            }
        )
    )

    # Standardize membership_type column
    df["membership_type"] = np.where(
        df["xdate"] == "2099-11-01", "lifetime", df["membership_type"].str.lower(),
    )

    return df


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
            memb_lists[date_formatted] = data_cleaning(date_formatted)

            for column in memb_lists[date_formatted].columns:
                if column not in memb_lists_metrics:
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