"""Parse all membership lists into pandas dataframes for display on dashboard"""

import functools
import logging
import pickle
from glob import glob
from pathlib import Path, PurePath
from zipfile import ZipFile

import dotenv
import mapbox
import pandas as pd
import ratelimit
from tqdm import tqdm

config = dotenv.dotenv_values(Path(PurePath(__file__).parents[2], ".env"))
geocoder = mapbox.Geocoder(access_token=config.get("MAPBOX"))
BRANCH_ZIPS_PATH = Path(PurePath(__file__).parents[2], "branch_zips.csv")
MEMBER_LIST_NAME = config.get("LIST", "fake_membership_list")

logging.basicConfig(level=logging.WARNING, format="%(asctime)s : %(levelname)s : %(message)s")


class ListColumnRules:
    """Define rules for cleaning and standardizing the columns of a membership list"""

    FIELD_DROP = [
        "organization",
        "dsa_id",
        "family_first_name",
        "family_last_name",
    ]
    FIELD_UPGRADE_PATHS = {
        "accommodations": ["accomodations"],
        "actionkit_id": ["akid", "ak_id"],
        "address1": [
            "billing_address1",
            "billing_address_line_1",
            "mailing_address1",
            "address_line_1",
        ],
        "address2": [
            "billing_address2",
            "billing_address_line_2",
            "mailing_address2",
            "address_line_2",
        ],
        "city": ["billing_city", "mailing_city"],
        "dsa_chapter": ["chapter"],
        "state": ["billing_state", "mailing_state"],
        "union_local": ["union_name_local"],
        "ydsa_chapter": ["ydsa chapter"],
        "yearly_dues_status": ["annual_recurring_dues_status"],
        "zip": ["billing_zip", "mailing_zip"],
    }
    FIELD_UPGRADE_PAIRS = {old: new for new, old_names in FIELD_UPGRADE_PATHS.items() for old in old_names}


def membership_length_months(join_date: pd.Series, xdate: pd.Series):
    """Calculate how many months are between the supplied dates, with a third date limiting the end date."""
    return 12 * (xdate.dt.year - join_date.dt.year) + (xdate.dt.month - join_date.dt.month)


def membership_length_years(join_date: pd.Series, xdate: pd.Series) -> pd.Series:
    """Calculate how many years are between the supplied dates, with a third date limiting the end date."""
    return membership_length_months(join_date, xdate) // 12


@ratelimit.sleep_and_retry
@ratelimit.limits(calls=600, period=60)
def mapbox_geocoder(address: str) -> list[float]:
    """Return a list of lat and long coordinates from a supplied address string, using the Mapbox API"""
    response = geocoder.forward(address, country=["us"])
    if "features" not in response.geojson():
        return [0, 0]
    return response.geojson()["features"][0]["center"]


@functools.lru_cache(maxsize=32_768, typed=False)
def get_geocoding(address: str) -> list[float]:
    """Return a list of lat and long coordinates from a supplied address string, either from cache or mapbox_geocoder"""
    if not isinstance(address, str) or "MAPBOX" not in config:
        return [0, 0]
    return mapbox_geocoder(address)


def format_zip_code(zip_code):
    """Format zip code to 5 characters, zero-pad if necessary"""
    return str(zip_code).zfill(5)


def data_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize dataframe according to specified rules."""
    df.columns = df.columns.str.lower()
    if "family_first_name" in df.columns:
        df["family_members"] = df.family_first_name.str.cat(df.family_last_name, sep=" ")

    for old_name, new_name in ListColumnRules.FIELD_UPGRADE_PAIRS.items():
        if new_name not in df.columns and old_name in df.columns:
            df[new_name] = df[old_name]
        df.drop(columns=old_name, inplace=True, errors="ignore")
    for field_name in ListColumnRules.FIELD_DROP:
        df.drop(columns=field_name, inplace=True, errors="ignore")

    df.set_index("actionkit_id", inplace=True)

    df["zip"] = df.zip.apply(format_zip_code)
    df["city"] = df.city.str.title()

    if "union_member" in df.columns:
        df["union_member"].replace(
            {0: "No", 1: "Yes, current union member", 2: "Yes, retired union member"},
            inplace=True,
        )

    df["join_date"] = pd.to_datetime(df["join_date"], format="mixed")
    df["join_year"] = pd.PeriodIndex(df["join_date"], freq="Y").to_timestamp()
    df["join_quarter"] = pd.PeriodIndex(df["join_date"], freq="Q").to_timestamp()
    df["xdate"] = pd.to_datetime(df["xdate"], format="mixed")

    df["membership_length_months"] = membership_length_months(df["join_date"], df["xdate"])
    df["membership_length_years"] = df.membership_length_months // 12

    df["membership_status"] = df.membership_status.replace("expired", "lapsed").str.lower()
    df["memb_status_letter"] = df["membership_status"].replace({"member in good standing": "M", "member": "M", "lapsed": "L"})

    df["membership_type"] = df.membership_type.replace("annual", "yearly").str.lower()
    df["membership_type"].where(df.xdate != "2099-11-01", "lifetime", inplace=True)

    if "lat" not in df:
        tqdm.pandas(unit="comrades", leave=False, desc="Geocoding")
        df[["lon", "lat"]] = pd.DataFrame(
            (df["address1"] + ", " + df["city"] + ", " + df["state"] + " " + df["zip"]).progress_apply(get_geocoding).tolist(),
            index=df.index,
        )

    return df


def scan_memb_list_from_csv(csv_file_data) -> pd.DataFrame:
    """Convert the provided csv data into a pandas dataframe."""
    return pd.read_csv(csv_file_data, dtype={"zip": str}, header=0)


def scan_memb_list_from_zip(zip_path: str, list_name: str) -> pd.DataFrame:
    """Scan a zip file containing a csv and return the output of scan_memb_list_from_csv from the csv if the zip file name contains a date."""
    with ZipFile(zip_path) as memb_list_zip:
        with memb_list_zip.open(f"{list_name}.csv", "r") as memb_list_csv:
            return scan_memb_list_from_csv(memb_list_csv)


def scan_all_membership_lists(list_name: str) -> dict[str, pd.DataFrame]:
    """Scan all zip files and call scan_memb_list_from_zip on each, returning the results."""
    memb_lists = {}
    logging.info("Scanning zipped membership lists in %s/.", list_name)
    files = sorted(glob(str(Path(PurePath(__file__).parents[2], list_name, "**/*.zip")), recursive=True), reverse=True)
    for zip_file in files:
        filename = Path(zip_file).name
        try:
            date_from_filename = str(PurePath(filename).stem).split("_")[-1]
            list_date_iso = pd.to_datetime(date_from_filename, format="%Y%m%d").date().isoformat()
            memb_lists[list_date_iso] = scan_memb_list_from_zip(str(Path(zip_file).absolute()), list_name)
        except (IndexError, ValueError):
            logging.warning("Could not extract list from %s. Skipping file.", filename)
    logging.info("Found %s zipped membership lists.", len(memb_lists))
    return memb_lists


def get_pickled_dict(list_name: str) -> dict[str, pd.DataFrame]:
    """Return the last scanned membership lists."""
    pickled_file_path = Path(PurePath(__file__).parents[2], list_name, f"{list_name}.pkl")
    if not pickled_file_path.is_file():
        return {}
    with open(pickled_file_path, "rb") as pickled_file:
        pickled_dict = pickle.load(pickled_file)
        logging.info("Found %s pickled membership lists.", len(pickled_dict))
        return pickled_dict


def integrate_new_membership_lists(memb_list_zips: dict[str, pd.DataFrame], pickled_lists: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Use pre-calculated data from pickle, clean data from new membership lists, and combine them into a complete, date-sorted dict"""
    new_lists = {k: v for k, v in memb_list_zips.items() if k not in pickled_lists}
    if new_lists:
        logging.info("Cleaning data for %s new lists.", len(new_lists))
        new_lists = {k_date: data_cleaning(memb_list) for k_date, memb_list in tqdm(new_lists.items(), unit="list", desc="Scanning Zip Files")}
    return dict(sorted((new_lists | pickled_lists).items(), reverse=True))


def branch_name_from_zip(zip_code: str, branch_zips: pd.DataFrame) -> str:
    """Check for provided zip_code in provided branch_zips and return relevant branch name if found"""
    cleaned_zip_code = format_zip_code(zip_code).split("-")[0]
    return branch_zips.loc[cleaned_zip_code, "branch"] if cleaned_zip_code in branch_zips.index else ""


def tagged_with_branches(memb_lists: dict[str, pd.DataFrame], branch_zip_path: Path) -> dict[str, pd.DataFrame]:
    """Add branch column to each membership list, filling with data cross-referenced from a provided csv via branch_name_from_zip_code()"""
    branch_zips = pd.read_csv(branch_zip_path, dtype={"zip": str}, index_col="zip")
    for date, memb_list in memb_lists.items():
        logging.debug(
            "Tagging %s membership list with branches based on current zip code assignments.",
            date,
        )
        memb_list["branch"] = memb_list["zip"].apply(branch_name_from_zip, branch_zips=branch_zips)
    return memb_lists


def get_membership_lists(list_name: str, branch_lookup_path: Path) -> dict[str, pd.DataFrame]:
    """Return all membership lists, preferring pickled lists for speed."""
    memb_list_zips = scan_all_membership_lists(list_name)
    pickled_lists = get_pickled_dict(list_name)
    memb_lists = integrate_new_membership_lists(memb_list_zips, pickled_lists)
    with open(Path(PurePath(__file__).parents[2], list_name, f"{list_name}.pkl"), "wb") as pickled_file:
        logging.info("Saving all lists into pickle for quicker access next time.")
        pickle.dump(memb_lists, pickled_file)
    if BRANCH_ZIPS_PATH.is_file():
        logging.info("Tagging each membership list based on current branch zip code assignments.")
        memb_lists = tagged_with_branches(memb_lists, branch_lookup_path)
    return memb_lists


MEMB_LISTS = get_membership_lists(MEMBER_LIST_NAME, BRANCH_ZIPS_PATH)
