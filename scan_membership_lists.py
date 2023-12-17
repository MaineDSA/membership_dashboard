"""Parse all membership lists into pandas dataframes for display on dashboard"""

import os
import logging
from glob import glob
import pickle
from zipfile import ZipFile
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
from mapbox import Geocoder
from ratelimit import limits, sleep_and_retry


MEMB_LIST_NAME = Path(".list_name").read_text(encoding="UTF-8")
BRANCH_ZIPS_FILE = "branch_zips.csv"


geocoder = Geocoder(access_token=Path(".mapbox_token").read_text(encoding="UTF-8"))
logging.basicConfig(level=logging.WARNING, format="%(asctime)s : %(levelname)s : %(message)s")


def membership_length(date: str, **kwargs) -> int:
    """Return an integer representing how many years between the supplied dates."""
    return (pd.to_datetime(kwargs["list_date"]) - pd.to_datetime(date)) // pd.Timedelta(days=365)


address_cache = {}


@sleep_and_retry
@limits(calls=600, period=60)
def mapbox_geocoder(address: str) -> list:
    """Return a list of lat and long coordinates from a supplied address string, using the Mapbox API"""
    response = geocoder.forward(address, country=["us"])
    if "features" in response.geojson():
        return response.geojson()["features"][0]["center"]
    return [0, 0]


def get_geocoding(address: str) -> list:
    """Return a list of lat and long coordinates from a supplied address string, either from cache or mapbox_geocoder"""
    if not isinstance(address, str) or not Path(".mapbox_token").is_file():
        return [0, 0]

    if address not in address_cache:
        address_cache[address] = mapbox_geocoder(address)

    return address_cache[address]


def data_cleaning(df: pd.DataFrame, list_date: str) -> pd.DataFrame:
    """Clean and standardize dataframe according to specified rules."""
    # Ensure column names are lowercase
    df.columns = df.columns.str.lower()

    # Rename the old columns to new names
    for old, new in {
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
    }.items():
        if (new not in df.columns) & (old in df.columns):
            df.rename(columns={old: new}, inplace=True)

    df.set_index("actionkit_id", inplace=True)

    # Apply the membership_length function to join_date
    df["membership_length"] = df["join_date"].apply(membership_length, list_date=list_date)

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
    df["membership_status"] = df.get("membership_status", "unknown").replace({"expired": "lapsed"}).str.lower()

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
    if ("lat" not in df) and ("lon" not in df):
        tqdm.pandas(unit="comrades", leave=False)
        df[["lon", "lat"]] = pd.DataFrame(
            (df["address1"] + ", " + df["city"] + ", " + df["state"] + " " + str(df["zip"])).progress_apply(get_geocoding).tolist(),
            index=df.index,
        )

    return df


def scan_membership_list(filename: str, filepath: str) -> pd.DataFrame:
    """Scan the requested membership list and add data to memb_lists."""
    date_from_name = pd.to_datetime(os.path.splitext(filename)[0].split("_")[3], format="%Y%m%d").date()
    if not date_from_name:
        logging.warning("No date detected in name of %s. Skipping file.", filename)
        return pd.DataFrame()

    with ZipFile(filepath) as memb_list_zip:
        with memb_list_zip.open(f"{MEMB_LIST_NAME}.csv") as memb_list:
            logging.debug("Loading data from %s.csv in %s.", MEMB_LIST_NAME, filename)
            return pd.read_csv(memb_list, header=0)


def scan_all_membership_lists() -> dict:
    """Scan all zip files and call scan_membership_list on each."""
    memb_lists = {}
    logging.info("Scanning zipped membership lists in %s/.", MEMB_LIST_NAME)
    files = sorted(
        glob(os.path.join(MEMB_LIST_NAME, "**/*.zip"), recursive=True),
        reverse=True,
    )
    for zip_file in files:
        filename = os.path.basename(zip_file)
        try:
            date_from_name = pd.to_datetime(os.path.splitext(filename)[0].split("_")[3], format="%Y%m%d").date()
            # Save contents of each zip file into dict keyed to date
            memb_lists[date_from_name.isoformat()] = scan_membership_list(filename, os.path.abspath(zip_file))
        except (IndexError, ValueError):
            logging.info("No date detected in name of %s. Skipping file.", filename)
    logging.info("Found %s zipped membership lists.", len(memb_lists))
    return memb_lists


def get_pickled_dict() -> dict:
    """Return the last scanned membership lists."""
    pickled_file_path = os.path.join(MEMB_LIST_NAME, f"{MEMB_LIST_NAME}.pkl")
    if not os.path.exists(pickled_file_path):
        return {}

    with open(pickled_file_path, "rb") as pickled_file:
        pickled_dict = pickle.load(pickled_file)
        logging.info("Found %s pickled membership lists.", len(pickled_dict))
        return pickled_dict


def get_membership_lists() -> dict:
    """Return all membership lists, preferring pickled lists for speed."""
    memb_lists = scan_all_membership_lists()
    pickled_lists = get_pickled_dict()

    new_lists = {k: v for k, v in memb_lists.items() if k not in pickled_lists}
    logging.info("Found %s new lists", len(new_lists))
    if new_lists:
        logging.info("Geocoding and cleaning data for new lists.")
        new_lists = {k: data_cleaning(v, k) for k, v in tqdm(new_lists.items(), unit="list")}

    memb_lists = dict(sorted((new_lists | pickled_lists).items(), reverse=True))
    with open(os.path.join(MEMB_LIST_NAME, f"{MEMB_LIST_NAME}.pkl"), "wb") as pickled_file:
        pickle.dump(memb_lists, pickled_file)

    # Cross-reference with branch_zips.csv
    if not Path(BRANCH_ZIPS_FILE).is_file():
        return memb_lists

    branch_zips = pd.read_csv(BRANCH_ZIPS_FILE, dtype={"zip": str}, index_col="zip")
    return {
        k: pd.DataFrame({**v, "branch": v["zip"].astype(str).str[:5].map(lambda zip_code: branch_zips.loc[zip_code, "branch"])}) for k, v in memb_lists.items()
    }
