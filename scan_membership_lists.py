"""Parse all membership lists into pandas dataframes for display on dashboard"""

from glob import glob
from pathlib import Path
from zipfile import ZipFile
import logging
import os
import pickle

from functools import lru_cache
from mapbox import Geocoder
from ratelimit import limits, sleep_and_retry
from tqdm import tqdm
import numpy as np
import pandas as pd

MEMB_LIST_NAME = "fake_membership_list"
BRANCH_ZIPS_PATH = Path("branch_zips.csv")
MEMB_LIST_CONFIG_PATH = Path(".list_name")
if MEMB_LIST_CONFIG_PATH.is_file():
    MEMB_LIST_NAME = MEMB_LIST_CONFIG_PATH.read_text(encoding="UTF-8")

logging.basicConfig(level=logging.WARNING, format="%(asctime)s : %(levelname)s : %(message)s")
geocoder = Geocoder()
MAPBOX_TOKEN_PATH = Path(".mapbox_token")
if MAPBOX_TOKEN_PATH.is_file():
    geocoder = Geocoder(access_token=MAPBOX_TOKEN_PATH.read_text(encoding="UTF-8"))


def membership_length(date: str, **kwargs) -> int:
    """Return an integer representing how many years between the supplied dates."""
    return (pd.to_datetime(kwargs["list_date"]) - pd.to_datetime(date)) // pd.Timedelta(days=365)


@sleep_and_retry
@limits(calls=600, period=60)
def mapbox_geocoder(address: str) -> list[float]:
    """Return a list of lat and long coordinates from a supplied address string, using the Mapbox API"""
    response = geocoder.forward(address, country=["us"])

    if "features" not in response.geojson():
        return [0, 0]

    return response.geojson()["features"][0]["center"]


@lru_cache(maxsize=16_384, typed=False)
def get_geocoding(address: str) -> list[float]:
    """Return a list of lat and long coordinates from a supplied address string, either from cache or mapbox_geocoder"""
    if not isinstance(address, str) or not MAPBOX_TOKEN_PATH.is_file():
        return [0, 0]

    return mapbox_geocoder(address)


def format_zip_code(zip_code):
    """Format zip code to 5 characters, zero-pad if necessary"""
    return str(zip_code).zfill(5)


def data_cleaning(df: pd.DataFrame, list_date: str) -> pd.DataFrame:
    """Clean and standardize dataframe according to specified rules."""
    # Ensure column names are lowercase
    df.columns = df.columns.str.lower()

    # Rename the old columns to new names
    for old, new in {
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

    df["zip"] = df["zip"].apply(format_zip_code)

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
    df["membership_type"] = np.where(df["xdate"] == "2099-11-01", "lifetime", df["membership_type"].replace({"annual": "yearly"}).str.lower())

    # Get lat/lon from address
    if "lat" not in df:
        tqdm.pandas(unit="comrades", leave=False, desc="Geocoding")
        df[["lon", "lat"]] = pd.DataFrame(
            (df["address1"] + ", " + df["city"] + ", " + df["state"] + " " + df["zip"]).progress_apply(get_geocoding).tolist(), index=df.index
        )

    return df


def scan_membership_list(filename: str, filepath: str) -> pd.DataFrame:
    """Scan the requested membership list and add data to memb_lists."""
    datetime_from_name = pd.to_datetime(os.path.splitext(filename)[0].split("_")[-1], format="%Y%m%d")
    if not datetime_from_name.date():
        logging.warning("No date detected in name of %s. Skipping file.", filename)
        return pd.DataFrame()
    with ZipFile(filepath) as memb_list_zip:
        with memb_list_zip.open(f"{MEMB_LIST_NAME}.csv") as memb_list:
            logging.debug("Loading data from %s.csv in %s.", MEMB_LIST_NAME, filename)
            return pd.read_csv(memb_list, header=0)


def scan_all_membership_lists() -> dict[str, pd.DataFrame]:
    """Scan all zip files and call scan_membership_list on each."""
    memb_lists = {}
    logging.info("Scanning zipped membership lists in %s/.", MEMB_LIST_NAME)
    files = sorted(glob(os.path.join(MEMB_LIST_NAME, "**/*.zip"), recursive=True), reverse=True)
    for zip_file in files:
        filename = os.path.basename(zip_file)
        try:
            date_from_name = pd.to_datetime(os.path.splitext(filename)[0].split("_")[-1], format="%Y%m%d").date()
            # Save contents of each zip file into dict keyed to date
            memb_lists[date_from_name.isoformat()] = scan_membership_list(filename, os.path.abspath(zip_file))
        except (IndexError, ValueError):
            logging.info("No date detected in name of %s. Skipping file.", filename)
    logging.info("Found %s zipped membership lists.", len(memb_lists))
    return memb_lists


def get_pickled_dict() -> dict[str, pd.DataFrame]:
    """Return the last scanned membership lists."""
    pickled_file_path = os.path.join(MEMB_LIST_NAME, f"{MEMB_LIST_NAME}.pkl")
    if not os.path.exists(pickled_file_path):
        return {}

    with open(pickled_file_path, "rb") as pickled_file:
        pickled_dict = pickle.load(pickled_file)
        logging.info("Found %s pickled membership lists.", len(pickled_dict))
        return pickled_dict


def integrate_new_membership_lists(memb_list_zips: dict[str, pd.DataFrame], pickled_lists: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Use pre-calculated data from pickle, clean data from new membership lists, and combine them into a complete, date-sorted dict"""
    new_lists = {k: v for k, v in memb_list_zips.items() if k not in pickled_lists}
    logging.info("Found %s new lists", len(new_lists))
    if new_lists:
        logging.info("Cleaning data for new lists.")
        new_lists = {k_date: data_cleaning(memb_list, k_date) for k_date, memb_list in tqdm(new_lists.items(), unit="list", desc="Scanning Zip Files")}
    return dict(sorted((new_lists | pickled_lists).items(), reverse=True))


def branch_name_from_zip(zip_code: str, branch_zips: pd.DataFrame) -> str:
    """Check for provided zip_code in provided branch_zips and return relevant branch name if found"""
    cleaned_zip_code = format_zip_code(zip_code).split("-")[0]
    return branch_zips.loc[cleaned_zip_code, "branch"] if cleaned_zip_code in branch_zips.index else ""


def tagged_with_branches(memb_lists: dict[str, pd.DataFrame], branch_zip_path: Path):
    """Add branch column to each membership list, filling with data cross-referenced from a provided csv via branch_name_from_zip()"""
    branch_zips = pd.read_csv(branch_zip_path, dtype={"zip": str}, index_col="zip")
    for _, memb_list in memb_lists.items():
        memb_list["branch"] = memb_list["zip"].apply(branch_name_from_zip, branch_zips=branch_zips)
    return memb_lists


def get_membership_lists() -> dict[str, pd.DataFrame]:
    """Return all membership lists, preferring pickled lists for speed."""
    memb_list_zips = scan_all_membership_lists()
    pickled_lists = get_pickled_dict()
    memb_lists = integrate_new_membership_lists(memb_list_zips, pickled_lists)

    with open(os.path.join(MEMB_LIST_NAME, f"{MEMB_LIST_NAME}.pkl"), "wb") as pickled_file:
        pickle.dump(memb_lists, pickled_file)

    # Cross-reference with branch_zips.csv
    if BRANCH_ZIPS_PATH.is_file():
        return tagged_with_branches(memb_lists, BRANCH_ZIPS_PATH)

    return memb_lists
