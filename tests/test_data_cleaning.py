"""Perform testing to ensure the data cleaning functions work as expected so that membership lists of different ages can be compared"""

import pandas as pd

from ..scan_membership_lists import data_cleaning


def test_mailing_to_unified_address_conversion():
    """Check whether mailing address is converted to single unified address"""
    with open("tests/test_harness_assets/fake_membership_list_2022_late.csv") as memb_list:
        person = data_cleaning(pd.read_csv(memb_list, header=0), "2024-01-01").loc[55222]
        assert person["address1"] == "255 Westbrook St"
        assert person["address2"] == "Unit 2"
        assert person["city"] == "Brunswick"
        assert person["state"] == "ME"
        assert person["zip"] == "04011"


def test_zip_code_leading_zero_padding():
    """Check whether mailing address is converted to single unified address"""
    with open("tests/test_harness_assets/fake_membership_list_2020_early.csv") as memb_list:
        person = data_cleaning(pd.read_csv(memb_list, header=0), "2024-01-01").loc[55222]
        assert person["zip"] == "04011"


def test_old_address_column_name_conversion():
    """Check whether old address column name (2020 era) is converted to new address column name"""
    with open("tests/test_harness_assets/fake_membership_list_2020_early.csv") as memb_list:
        person = data_cleaning(pd.read_csv(memb_list, header=0), "2024-01-01").loc[55222]
        assert person["address1"] == "255 Westbrook St"
        assert person["address2"] == "Unit 2"


def test_annual_to_yearly_dues_conversion():
    """Check whether annual dues status of pre-2023 lists is converted to yearly dues status"""
    with open("tests/test_harness_assets/fake_membership_list_2022_late.csv") as memb_list:
        person = data_cleaning(pd.read_csv(memb_list, header=0), "2024-01-01").loc[55222]
        assert person["yearly_dues_status"] == "canceled"


def test_add_accomodations_column():
    """Esure all members have an accomodations column"""
    with open("tests/test_harness_assets/fake_membership_list_2020_early.csv") as memb_list:
        person = data_cleaning(pd.read_csv(memb_list, header=0), "2024-01-01").loc[55222]
        assert person["accommodations"] is None


def test_expired_status_conversion():
    """Ensure members with expired status have this changed to lapsed"""
    with open("tests/test_harness_assets/fake_membership_list_2021_early.csv") as memb_list:
        person = data_cleaning(pd.read_csv(memb_list, header=0), "2024-01-01").loc[55222]
        assert person["membership_status"] == "lapsed"


def test_lifetime_type_conversion():
    """Ensure members with expiration date of 2099 have membership_type set to lifetime"""
    with open("tests/test_harness_assets/fake_membership_list_2023_late.csv") as memb_list:
        person = data_cleaning(pd.read_csv(memb_list, header=0), "2024-01-01").loc[155222]
        assert person["membership_type"] == "lifetime"
