"""Parse all membership lists into pandas dataframes for display on dashboard"""

import os
import time
import glob
import pickle
import zipfile
import numpy as np
import pandas as pd
from tqdm import tqdm
from mapbox import Geocoder


MEMB_LIST_NAME = "maine_membership_list"


memb_lists = {}
"""Contains data organized as column:value pairs within a dict of membership list dates."""
memb_lists_metrics = {}
"""Contains data organized as date:value pairs within a dict of original columns names."""


# pylint: disable-next=consider-using-with
geocoder = Geocoder(access_token=open(".mapbox_token", encoding="utf8").read())


def membership_length(date: str, **kwargs) -> int:
    """Return an integer representing how many years between the supplied dates."""
    return (pd.to_datetime(kwargs["list_date"]) - pd.to_datetime(date)) // pd.Timedelta(
        days=365
    )


def get_geocoding(address: str) -> list:
    """Return a list of lat and long coordinates from a supplied address string, using the Mapbox API"""
    if not isinstance(address, str):
        return []

    response = geocoder.forward(address, country=["us"])
    latlon = response.geojson()["features"][0]["center"]
    time.sleep(0.01) # free tier rate limit is 600/min

    return latlon


def data_cleaning(date_formatted: str) -> pd.DataFrame:
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
        # before fall of 2023
        "mailing_address1": "address1",
        "mailing_address2": "address2",
        "mailing_city": "city",
        "mailing_state": "state",
        "mailing_zip": "zip",
        # old 2020-era lists
        "address_line_1": "address1",
        "address_line_2": "address2",
    }

    # Rename the old columns to new names
    for old, new in column_mapping.items():
        if (new not in df.columns) & (old in df.columns):
            df[new] = df[old]
            df = df.drop(old, axis=1)

    df.set_index("actionkit_id", inplace=True)

    # Apply the membership_length function to join_date
    df["membership_length"] = df["join_date"].apply(
        membership_length, list_date=date_formatted
    )

    # Standardize other columns
    for col, default in [
        ("membership_type", "unknown"),
        ("address2", ""),
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

    # Create full address
    tqdm.pandas(unit="comrades", leave=False)
    df[["lon", "lat"]] = pd.DataFrame(
        (df["address1"] + ", " + df["city"] + ", " + df["state"] + " " + df["zip"]).progress_apply(get_geocoding).tolist(), index=df.index
    )

    return df


def scan_membership_list(filename: str, filepath: str):
    """Scan the requested membership list and add data to memb_lists."""
    date_from_name = pd.to_datetime(
        os.path.splitext(filename)[0].split("_")[3], format="%Y%m%d"
    ).date()
    if not date_from_name:
        print(f"No date detected in name of {filename}. Skipping file.")
        return

    with zipfile.ZipFile(filepath) as memb_list_zip:
        with memb_list_zip.open(f"{MEMB_LIST_NAME}.csv") as memb_list:
            # print(f"Loading data from {MEMB_LIST_NAME}.csv in {filename}.")
            date_formatted = date_from_name.isoformat()

            memb_lists[date_formatted] = pd.read_csv(memb_list, header=0)
            memb_lists[date_formatted] = data_cleaning(date_formatted)


def scan_membership_list_metrics() -> (dict):
    """Scan memb_lists and calculate metrics."""
    print(f"Calculating metrics for {len(memb_lists)} membership lists")
    for date_formatted, membership_list in memb_lists.items():
        for column in membership_list.columns:
            if column not in memb_lists_metrics:
                memb_lists_metrics[column] = {}
            memb_lists_metrics[column][date_formatted] = memb_lists[date_formatted][
                column
            ]

    # Pickle the scanned and calculated metrics
    with open(f"{MEMB_LIST_NAME}_metrics.pkl", "wb") as pickled_file:
        pickle.dump(memb_lists_metrics, pickled_file)

    return memb_lists_metrics


def get_membership_list_metrics() -> (dict):
    """Return the last calculated metrics."""
    try:
        with open(f"{MEMB_LIST_NAME}_metrics.pkl", "rb") as pickled_file:
            pickled_dict = pickle.load(pickled_file)
            if len(pickled_dict) > 0:
                return pickled_dict
            return scan_membership_list_metrics()
    except FileNotFoundError:
        return scan_membership_list_metrics()

    return {}


def scan_all_membership_lists() -> (dict):
    """Scan all zip files and call scan_membership_list on each."""
    print(f"Scanning zipped membership lists in ./{MEMB_LIST_NAME}/.")
    files = sorted(
        glob.glob(os.path.join(MEMB_LIST_NAME, "**/*.zip"), recursive=True),
        reverse=True,
    )
    for file in tqdm(files, unit="list"):
        scan_membership_list(os.path.basename(file), os.path.abspath(file))

    # Pickle the scanned and processed lists
    with open(f"{MEMB_LIST_NAME}.pkl", "wb") as pickled_file:
        pickle.dump(memb_lists, pickled_file)

    scan_membership_list_metrics()

    return memb_lists


def get_all_membership_lists() -> (dict):
    """Return the last scanned membership lists."""
    try:
        with open(f"{MEMB_LIST_NAME}.pkl", "rb") as pickled_file:
            pickled_dict = pickle.load(pickled_file)
            if len(pickled_dict) > 0:
                return pickled_dict
            return scan_all_membership_lists()
    except FileNotFoundError:
        return scan_all_membership_lists()

    return {}
