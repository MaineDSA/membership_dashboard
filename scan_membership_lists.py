"""Parse all membership lists into pandas dataframes for display on dashboard"""

import os
import glob
import pickle
import zipfile
import numpy as np
import pandas as pd
from tqdm import tqdm


MEMB_LIST_NAME = "maine_membership_list"


def get_membership_list_metrics(memb_lists: pd.DataFrame) -> dict:
    """Scan memb_lists and calculate metrics."""
    memb_lists_metrics = {}

    print(f"Calculating metrics for {len(memb_lists)} membership lists")
    for date_formatted, membership_list in memb_lists.items():
        for column in membership_list.columns:
            if column not in memb_lists_metrics:
                memb_lists_metrics[column] = {}
            memb_lists_metrics[column][date_formatted] = memb_lists[date_formatted][
                column
            ]

    return memb_lists_metrics


def membership_length(date: str, **kwargs) -> int:
    """Return an integer representing how many years between the supplied dates."""
    return (pd.to_datetime(kwargs["list_date"]) - pd.to_datetime(date)) // pd.Timedelta(
        days=365
    )


def data_cleaning(df: pd.DataFrame, list_date: str) -> pd.DataFrame:
    """Clean and standardize dataframe according to specified rules."""
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
    df["membership_length"] = df["join_date"].apply(
        membership_length, list_date=list_date
    )

    # Standardize other columns
    for col, default in [
        ("membership_type", "unknown"),
        ("do_not_call", False),
        ("p2ptext_optout", False),
        ("race", "unknown"),
        ("union_member", "unknown"),
        ("accommodations", "no"),
    ]:
        df[col] = df.get(col, default)
        df[col] = df[col].fillna(default)

    # Standardize membership_status column
    df["membership_status"] = (
        df.get("membership_status", "unknown")
        .replace({"expired": "lapsed"})
        .str.lower()
    )

    # Standardize accommodations column
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
        df["xdate"] == "2099-11-01",
        "lifetime",
        df["membership_type"].replace({"annual": "yearly"}).str.lower(),
    )

    return df


def scan_membership_list(filename: str, filepath: str) -> pd.DataFrame:
    """Scan the requested membership list and add data to memb_lists."""
    date_from_name = pd.to_datetime(
        os.path.splitext(filename)[0].split("_")[3], format="%Y%m%d"
    ).date()
    if not date_from_name:
        print(f"No date detected in name of {filename}. Skipping file.")
        return pd.DataFrame()

    with zipfile.ZipFile(filepath) as memb_list_zip:
        with memb_list_zip.open(f"{MEMB_LIST_NAME}.csv") as memb_list:
            # print(f"Loading data from {MEMB_LIST_NAME}.csv in {filename}.")
            return pd.read_csv(memb_list, header=0)


def scan_all_membership_lists() -> dict:
    """Scan all zip files and call scan_membership_list on each."""
    memb_lists = {}

    print(f"Scanning zipped membership lists in ./{MEMB_LIST_NAME}/.")
    files = sorted(
        glob.glob(os.path.join(MEMB_LIST_NAME, "**/*.zip"), recursive=True),
        reverse=True,
    )
    for zip_file in tqdm(files, unit="lists"):

        # Get date from each file name
        filename = os.path.basename(zip_file)
        date_from_name = pd.to_datetime(
            os.path.splitext(filename)[0].split("_")[3], format="%Y%m%d"
        ).date()
        if not date_from_name:
            print(f"No date detected in name of {filename}. Skipping file.")
            continue

        # Save contents of each zip file into dict keyed to date
        memb_lists[date_from_name.isoformat()] = scan_membership_list(filename, os.path.abspath(zip_file))

    print(f"Found {len(memb_lists)} zipped membership lists.")
    return memb_lists


def get_pickled_dict() -> dict:
    """Return the last scanned membership lists."""
    try:
        with open(f"{MEMB_LIST_NAME}.pkl", "rb") as pickled_file:
            pickled_dict = pickle.load(pickled_file)
            print(f"Found {len(pickled_dict)} pickled membership lists.")
            return pickled_dict
    except FileNotFoundError:
        pass

    return {}

def get_membership_lists() -> dict:
    """Return all membership lists, preferring pickled lists for speed."""
    memb_lists = scan_all_membership_lists()
    pickled_lists = get_pickled_dict()
    new_lists = {k: v for k, v in memb_lists.items() if k not in pickled_lists}
    print(f"Found {len(new_lists)} new lists")
    if len(new_lists) > 0:
        new_lists = {k: data_cleaning(v, k) for k, v in tqdm(new_lists.items(), unit="lists")}
    memb_lists = new_lists | pickled_lists

    with open(f"{MEMB_LIST_NAME}.pkl", "wb") as pickled_file:
        pickle.dump(memb_lists, pickled_file)

    return memb_lists
