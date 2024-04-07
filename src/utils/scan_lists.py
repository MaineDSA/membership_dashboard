"""Parse all membership lists into pandas dataframes for display on dashboard"""

import logging
from glob import glob
from pathlib import Path, PurePath
from zipfile import ZipFile

import dotenv
import pandas as pd
from tqdm import tqdm

from src.utils.action_network import add_action_network_identifier
from src.utils.geocoding import add_coordinates

config = dotenv.dotenv_values(Path(PurePath(__file__).parents[2], ".env"))
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
    """Calculate how many months are between the supplied dates"""
    return 12 * (xdate.dt.year - join_date.dt.year) + (xdate.dt.month - join_date.dt.month)


def membership_length_years(join_date: pd.Series, xdate: pd.Series) -> pd.Series:
    """Calculate how many years are between the supplied dates."""
    return membership_length_months(join_date, xdate) // 12


def format_zip_code(zip_code):
    """Format zip code to 5 characters, zero-pad if necessary"""
    return str(zip_code).zfill(5)


def add_family_members(df: pd.DataFrame) -> pd.DataFrame:
    """Add 'family members' column to the dataframe, concatenating 'family_first_name' and 'family_last_name' with a space in between"""
    if "family_first_name" not in df.columns:
        return df

    df["family_members"] = df.family_first_name.str.cat(df.family_last_name, sep=" ")
    return df


def update_fields(df: pd.DataFrame, field_upgrade_pairs: dict[str, str], field_drop: list[str]) -> pd.DataFrame:
    """Update dataframe fields by renaming columns, and dropping specified columns."""
    for old_name, new_name in field_upgrade_pairs.items():
        if new_name not in df.columns and old_name in df.columns:
            df[new_name] = df[old_name]
        df.drop(columns=old_name, inplace=True, errors="ignore")
    for field_name in field_drop:
        df.drop(columns=field_name, inplace=True, errors="ignore")
    return df


def format_address_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Ensures standard formatting of ZIP code length and city capitalization"""
    df["zip"] = df.zip.apply(format_zip_code)
    df["city"] = df.city.str.title()
    return df


def handle_union_member(df: pd.DataFrame) -> pd.DataFrame:
    """Replace old numeric values in column union_member with string mappings used in current lists"""
    if "union_member" not in df.columns:
        return df

    df["union_member"] = df.union_member.replace(
        {0: "No", 1: "Yes, current union member", 2: "Yes, retired union member"},
    )
    return df


def process_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Convert join_date and xdate to datetime and add join_year and join_quarter columns"""
    df["join_date"] = pd.to_datetime(df.join_date, format="mixed")
    df["join_year"] = pd.PeriodIndex(df.join_date, freq="Y").to_timestamp()
    df["join_quarter"] = pd.PeriodIndex(df.join_date, freq="Q").to_timestamp()
    df["xdate"] = pd.to_datetime(df.xdate, format="mixed")
    return df


def calculate_membership_length(df: pd.DataFrame) -> pd.DataFrame:
    """Adds membership length in both months and years"""
    df["membership_length_months"] = membership_length_months(df.join_date, df.xdate)
    df["membership_length_years"] = df.membership_length_months // 12
    return df


def format_membership_status(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize the membership status fields"""
    df["membership_status"] = df.membership_status.replace("expired", "lapsed").str.lower()
    df["memb_status_letter"] = df.membership_status.replace({"member in good standing": "M", "member": "M", "lapsed": "L"})
    return df


def format_membership_type(df: pd.DataFrame) -> pd.DataFrame:
    """Update membership_type with current standard values and create lifetime category"""
    df["membership_type"] = df.membership_type.replace("annual", "yearly").str.lower()
    df["membership_type"] = df.membership_type.where(df.xdate != "2099-11-01", "lifetime")
    return df


def data_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.lower()
    df = add_family_members(df)
    df = update_fields(df, ListColumnRules.FIELD_UPGRADE_PAIRS, ListColumnRules.FIELD_DROP)
    df = format_address_fields(df)
    df = handle_union_member(df)
    df = process_dates(df)
    df = calculate_membership_length(df)
    df = format_membership_status(df)
    df = format_membership_type(df)
    df = add_coordinates(df)
    df = add_action_network_identifier(df)
    df.set_index("actionkit_id", inplace=True)
    return df


def scan_memb_list_from_csv(csv_file_data) -> pd.DataFrame:
    """Convert the provided csv data into a pandas dataframe"""
    return pd.read_csv(csv_file_data, dtype={"zip": str}, header=0)


def scan_memb_list_from_zip(zip_path: str, list_name: str) -> pd.DataFrame:
    """Scan a zip file containing a csv and return the output of scan_memb_list_from_csv from the csv if the zip file name contains a date"""
    with ZipFile(zip_path) as memb_list_zip:
        with memb_list_zip.open(f"{list_name}.csv", "r") as memb_list_csv:
            return scan_memb_list_from_csv(memb_list_csv)


def scan_all_membership_lists(list_name: str) -> dict[str, pd.DataFrame]:
    """Scan all zip files and call scan_memb_list_from_zip on each, returning the results"""
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


def branch_name_from_zip_code(zip_code: str, branch_zips: pd.DataFrame) -> str:
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
        memb_list["branch"] = memb_list["zip"].apply(branch_name_from_zip_code, branch_zips=branch_zips)
    return memb_lists


def get_membership_lists(list_name: str, branch_lookup_path: Path) -> dict[str, pd.DataFrame]:
    """Return all membership lists, preferring pickled lists for speed"""
    scanned_lists = scan_all_membership_lists(list_name)
    logging.info("Cleaning and standardizing data for %s lists.", len(scanned_lists))
    memb_lists = {k_date: data_cleaning(memb_list) for k_date, memb_list in tqdm(scanned_lists.items(), unit="list", desc="Scanning Zip Files")}
    if BRANCH_ZIPS_PATH.is_file():
        logging.info("Tagging each membership list based on current branch zip code assignments.")
        memb_lists = tagged_with_branches(memb_lists, branch_lookup_path)
    return memb_lists


MEMB_LISTS = get_membership_lists(MEMBER_LIST_NAME, BRANCH_ZIPS_PATH)
