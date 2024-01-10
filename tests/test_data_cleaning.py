"""Perform testing to ensure the data cleaning functions work as expected so that membership lists of different ages can be compared"""

from src.utils.scan_lists import data_cleaning, scan_memb_list_from_csv


def test_mailing_to_unified_address_conversion():
    """Check whether mailing address (late 2022 format) is converted to single unified address"""
    with open("tests/test_harness_assets/fake_membership_list_2022_late.csv") as memb_list:
        person = data_cleaning(scan_memb_list_from_csv(memb_list)).loc[222251]
        assert person["address1"] == "PO Box 13"
        assert person["city"] == "Turner"
        assert person["state"] == "ME"
        assert person["zip"] == "04282-0013"


def test_zip_code_leading_zero_padding():
    """Check whether zip codes with <4 digits are padded with leading zeros"""
    with open("tests/test_harness_assets/fake_membership_list_2022_late.csv") as memb_list:
        person = data_cleaning(scan_memb_list_from_csv(memb_list)).loc[178705]
        assert person["zip"] == "04103"


def test_old_address_column_name_renaming():
    """Check whether old address column name (2020 era) is converted to new address column name"""
    with open("tests/test_harness_assets/fake_membership_list_2020_early.csv") as memb_list:
        person = data_cleaning(scan_memb_list_from_csv(memb_list)).loc[222251]
        assert person["address1"] == "PO Box 13"
        assert person["address2"] == "Apt3"


def test_annual_to_yearly_dues_renaming():
    """Check whether annual dues status of pre-2023 lists is converted to yearly dues status"""
    with open("tests/test_harness_assets/fake_membership_list_2022_late.csv") as memb_list:
        person = data_cleaning(scan_memb_list_from_csv(memb_list)).loc[178705]
        assert person["yearly_dues_status"] == "never"


def test_expired_status_conversion():
    """Ensure members with expired status have this changed to lapsed"""
    with open("tests/test_harness_assets/fake_membership_list_2021_early.csv") as memb_list:
        person = data_cleaning(scan_memb_list_from_csv(memb_list)).loc[222251]
        assert person["membership_status"] == "lapsed"


def test_lifetime_type_conversion():
    """Ensure members with expiration date of 2099 have membership_type set to lifetime"""
    with open("tests/test_harness_assets/fake_membership_list_2021_early.csv") as memb_list:
        person = data_cleaning(scan_memb_list_from_csv(memb_list)).loc[28855]
        assert person["membership_type"] == "lifetime"


def test_membership_status_column_lowercasing():
    """Ensure membership lists with uppercase membership_status values are lowercased"""
    with open("tests/test_harness_assets/fake_membership_list_2021_early.csv") as memb_list:
        person = data_cleaning(scan_memb_list_from_csv(memb_list)).loc[28855]
        assert person["membership_status"] == "member in good standing"


def test_membership_length_years():
    """Ensure membership length calculation is correct in years"""
    with open("tests/test_harness_assets/fake_membership_list_2022_late.csv") as memb_list:
        person = data_cleaning(scan_memb_list_from_csv(memb_list)).loc[178705]
        assert person["membership_length_years"] == 1


def test_membership_length_months():
    """Ensure membership length calculation is correct in months"""
    with open("tests/test_harness_assets/fake_membership_list_2022_late.csv") as memb_list:
        person = data_cleaning(scan_memb_list_from_csv(memb_list)).loc[178705]
        assert person["membership_length_months"] == 14
