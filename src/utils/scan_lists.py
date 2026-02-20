"""Parse all membership lists into pandas dataframes for display on dashboard."""

import logging
from io import TextIOWrapper
from pathlib import Path, PurePath
from typing import IO, ClassVar
from zipfile import ZipFile

import dotenv
import pandas as pd
from tqdm import tqdm

from src.utils.geocoding import add_coordinates

config = dotenv.dotenv_values(Path(PurePath(__file__).parents[2], ".env"))
BRANCH_ZIPS_PATH = Path(PurePath(__file__).parents[2], "branch_zips.csv")
MEMBER_LIST_NAME: str = config.get("LIST") or "fake_membership_list"

logging.basicConfig(level=logging.WARNING, format="%(asctime)s : %(levelname)s : %(message)s")
logger = logging.getLogger(__name__)


class ListColumnRules:
    """Define rules for cleaning and standardizing the columns of a membership list."""

    FIELD_DROP: ClassVar[list[str]] = [
        "organization",
        "dsa_id",
        "family_first_name",
        "family_last_name",
    ]
    FIELD_UPGRADE_PATHS: ClassVar[dict[str, list[str]]] = {
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
    FIELD_UPGRADE_PAIRS: ClassVar[dict[str, str]] = {old: new for new, old_names in FIELD_UPGRADE_PATHS.items() for old in old_names}


def membership_length_months(join_date: pd.Series, xdate: pd.Series) -> pd.Series:
    """Calculate how many months are between the supplied dates."""
    return 12 * (xdate.dt.year - join_date.dt.year) + (xdate.dt.month - join_date.dt.month)


def membership_length_years(join_date: pd.Series, xdate: pd.Series) -> pd.Series:
    """Calculate how many years are between the supplied dates, with a third date limiting the end date."""
    return membership_length_months(join_date, xdate) // 12


def format_zip_code(zip_code: str | int) -> str:
    """Format zip code to 5 characters, zero-pad if necessary."""
    return str(zip_code).zfill(5)


def add_family_members(df: pd.DataFrame) -> pd.DataFrame:
    if "family_first_name" not in df.columns:
        return df

    df["family_members"] = df.family_first_name.str.cat(df.family_last_name, sep=" ")
    return df


def update_fields(df: pd.DataFrame, field_upgrade_pairs: dict[str, str], field_drop: list[str]) -> pd.DataFrame:
    for old_name, new_name in field_upgrade_pairs.items():
        if new_name not in df.columns and old_name in df.columns:
            df[new_name] = df[old_name]
        df.drop(columns=old_name, inplace=True, errors="ignore")
    for field_name in field_drop:
        df.drop(columns=field_name, inplace=True, errors="ignore")
    return df


def format_fields(df: pd.DataFrame) -> pd.DataFrame:
    df["zip"] = df.zip.apply(format_zip_code)
    df["city"] = df.city.str.title()
    return df


def handle_union_member(df: pd.DataFrame) -> pd.DataFrame:
    if "union_member" not in df.columns:
        return df

    df["union_member"] = df.union_member.replace(
        {0: "No", 1: "Yes, current union member", 2: "Yes, retired union member"},
    )
    return df


def process_dates(df: pd.DataFrame) -> pd.DataFrame:
    df["join_date"] = pd.to_datetime(df.join_date, format="mixed")
    df["join_year"] = pd.PeriodIndex(df.join_date, freq="Y").to_timestamp()
    df["join_quarter"] = pd.PeriodIndex(df.join_date, freq="Q").to_timestamp()
    df["xdate"] = pd.to_datetime(df.xdate, format="mixed")
    return df


def calculate_membership_length(df: pd.DataFrame) -> pd.DataFrame:
    df["membership_length_months"] = membership_length_months(df.join_date, df.xdate)
    df["membership_length_years"] = df.membership_length_months // 12
    return df


def format_membership_status(df: pd.DataFrame) -> pd.DataFrame:
    df["membership_status"] = df.membership_status.replace("expired", "lapsed").str.lower()
    df["memb_status_letter"] = df.membership_status.replace({"member in good standing": "M", "member": "M", "lapsed": "L"})
    return df


def format_membership_type(df: pd.DataFrame) -> pd.DataFrame:
    df["membership_type"] = df.membership_type.replace("annual", "yearly").str.lower()
    df["membership_type"] = df.membership_type.where(df.xdate != "2099-11-01", "lifetime")
    return df


def data_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.lower()
    df = add_family_members(df)
    df = update_fields(df, ListColumnRules.FIELD_UPGRADE_PAIRS, ListColumnRules.FIELD_DROP)
    df = format_fields(df)
    df = handle_union_member(df)
    df = process_dates(df)
    df = calculate_membership_length(df)
    df = format_membership_status(df)
    df = format_membership_type(df)
    df = add_coordinates(df)
    df.set_index("actionkit_id", inplace=True)
    return df


def scan_memb_list_from_csv(csv_file_data: Path | TextIOWrapper | IO[bytes]) -> pd.DataFrame:
    """Convert the provided csv data into a pandas dataframe."""
    return pd.read_csv(csv_file_data, dtype={"zip": str}, header=0)


def scan_memb_list_from_zip(zip_path: str, list_name: str) -> pd.DataFrame:
    """Scan a zip file containing a csv and return the output of scan_memb_list_from_csv from the csv if the zip file name contains a date."""
    with ZipFile(zip_path) as memb_list_zip, memb_list_zip.open(f"{list_name}.csv", "r") as memb_list_csv:
        return scan_memb_list_from_csv(memb_list_csv)


def date_from_stem(stem: str) -> str:
    """Extract an ISO date string from a filename stem by trying each underscore-separated segment."""
    parts = stem.split("_")
    candidates = parts[1:-1] if stem.startswith("AllMembers") else parts
    for part in reversed(candidates):
        try:
            return pd.to_datetime(part, format="mixed").date().isoformat()
        except ValueError:
            continue

    e = f"No parseable date found in filename stem: {stem}"
    raise ValueError(e)


def scan_all_zip_membership_lists(list_name: str) -> dict[str, pd.DataFrame]:
    """Scan all zip files and call scan_memb_list_from_zip on each, returning the results."""
    memb_lists = {}
    logger.info("Scanning zipped membership lists in %s/.", list_name)
    files = sorted((Path(__file__).parents[2] / list_name).glob("**/*.zip"), reverse=True)
    for zip_file in files:
        filename = Path(zip_file).name
        try:
            list_date_iso = date_from_stem(PurePath(filename).stem)
            memb_lists[list_date_iso] = scan_memb_list_from_zip(str(Path(zip_file).absolute()), list_name)
        except (IndexError, ValueError):
            logger.warning("Could not extract list from %s. Skipping file.", filename)
    logger.info("Found %s zipped membership lists.", len(memb_lists))
    return memb_lists


def scan_all_csv_membership_lists(list_name: str) -> dict[str, pd.DataFrame]:
    """Scan all csv files and call scan_memb_list_from_csv on each, return results."""
    memb_lists = {}
    logger.info("Scanning csv membership lists in %s/.", list_name)
    files = sorted((Path(__file__).parents[2] / list_name).glob("**/*.csv"), reverse=True)
    for csv in files:
        filename = Path(csv).name
        try:
            list_date_iso = date_from_stem(PurePath(filename).stem)
            memb_lists[list_date_iso] = scan_memb_list_from_csv(csv)
        except (IndexError, ValueError):
            logger.warning("Could not extract list from %s. Skipping file.", filename)
    logger.info("Found %s csv membership lists.", len(memb_lists))
    return memb_lists


def scan_all_membership_lists(list_name: str) -> dict[str, pd.DataFrame]:
    return scan_all_zip_membership_lists(list_name) | scan_all_csv_membership_lists(list_name)


def branch_name_from_zip_code(zip_code: str, branch_zips: pd.DataFrame) -> str:
    """Check for provided zip_code in provided branch_zips and return relevant branch name if found."""
    cleaned_zip_code = format_zip_code(zip_code).split("-")[0]
    return str(branch_zips.loc[cleaned_zip_code, "branch"]) if cleaned_zip_code in branch_zips.index else ""


def tagged_with_branches(memb_lists: dict[str, pd.DataFrame], branch_zip_path: Path) -> dict[str, pd.DataFrame]:
    """Add branch column to each membership list, filling with data cross-referenced from a provided csv via branch_name_from_zip_code()."""
    branch_zips = pd.read_csv(branch_zip_path, dtype={"zip": str}, index_col="zip")
    for date, memb_list in memb_lists.items():
        logger.debug(
            "Tagging %s membership list with branches based on current zip code assignments.",
            date,
        )
        memb_list["branch"] = memb_list["zip"].apply(branch_name_from_zip_code, branch_zips=branch_zips)
    return memb_lists


def get_membership_lists(list_name: str, branch_lookup_path: Path) -> dict[str, pd.DataFrame]:
    """Return all membership lists, preferring pickled lists for speed."""
    scanned_lists = scan_all_membership_lists(list_name)
    logger.info("Cleaning and standardizing data for %s lists.", len(scanned_lists))
    memb_lists = {k_date: data_cleaning(memb_list) for k_date, memb_list in tqdm(scanned_lists.items(), unit="list", desc="Scanning Zip Files")}
    if BRANCH_ZIPS_PATH.is_file():
        logger.info("Tagging each membership list based on current branch zip code assignments.")
        memb_lists = tagged_with_branches(memb_lists, branch_lookup_path)
    return memb_lists


MEMB_LISTS = get_membership_lists(MEMBER_LIST_NAME, BRANCH_ZIPS_PATH)
