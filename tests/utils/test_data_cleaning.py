"""Perform testing to ensure the data cleaning functions work as expected so that membership lists of different ages can be compared."""

import pandas as pd

from src.utils.scan_lists import data_cleaning, format_zip_code


def test_mailing_to_unified_address_conversion(late_2023_list: pd.DataFrame) -> None:
    """Check whether mailing address (late 2022 format) is converted to single unified address."""
    person = data_cleaning(late_2023_list).loc[222251]
    assert person["address1"] == "PO Box 13"
    assert person["city"] == "Turner"
    assert person["state"] == "ME"
    assert person["zip"] == "04282-0013"


def test_zip_code_leading_zero_padding(late_2022_list: pd.DataFrame) -> None:
    """Check whether zip codes with <4 digits are padded with leading zeros."""
    person = data_cleaning(late_2022_list).loc[178705]
    assert person["zip"] == "04103"


def test_old_address_column_name_renaming(early_2020_list: pd.DataFrame) -> None:
    """Check whether old address column name (2020 era) is converted to new address column name."""
    person = data_cleaning(early_2020_list).loc[222251]
    assert person["address1"] == "PO Box 13"
    assert person["address2"] == "Apt3"


def test_annual_to_yearly_dues_renaming(late_2022_list: pd.DataFrame) -> None:
    """Check whether annual dues status of pre-2023 lists is converted to yearly dues status."""
    person = data_cleaning(late_2022_list).loc[178705]
    assert person["yearly_dues_status"] == "never"


def test_expired_status_conversion(early_2021_list: pd.DataFrame) -> None:
    """Ensure members with expired status have this changed to lapsed."""
    person = data_cleaning(early_2021_list).loc[222251]
    assert person["membership_status"] == "lapsed"


def test_lifetime_type_conversion(early_2021_list: pd.DataFrame) -> None:
    """Ensure members with expiration date of 2099 have membership_type set to lifetime."""
    person = data_cleaning(early_2021_list).loc[28855]
    assert person["membership_type"] == "lifetime"


def test_membership_status_column_lowercasing(early_2021_list: pd.DataFrame) -> None:
    """Ensure membership lists with uppercase membership_status values are lowercased."""
    person = data_cleaning(early_2021_list).loc[28855]
    assert person["membership_status"] == "member in good standing"


def test_membership_length_years(late_2022_list: pd.DataFrame) -> None:
    """Ensure membership length calculation is correct in years."""
    person = data_cleaning(late_2022_list).loc[178705]
    assert person["membership_length_years"] == 1


def test_membership_length_months(late_2022_list: pd.DataFrame) -> None:
    """Ensure membership length calculation is correct in months."""
    person = data_cleaning(late_2022_list).loc[178705]
    assert person["membership_length_months"] == 14


def test_format_zip_code() -> None:
    """Check whether format_zip_code pads zip codes with <4 digits with leading zeros."""
    assert format_zip_code(4011) == "04011"
