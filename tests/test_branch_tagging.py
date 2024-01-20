"""Perform testing to ensure members are being tagged with a branch based on their zip code"""

from pathlib import Path

import pandas as pd

from src.utils.scan_lists import data_cleaning, tagged_with_branches

TEST_BRANCH_ZIP_CSV = Path("tests/test_harness_assets/fake_branch_zips.csv")


def test_branch_zip_tagging(late_2023_list: pd.DataFrame):
    """Load a branch_zips file and attempt to apply it to test data"""
    memb_list = data_cleaning(late_2023_list)
    tagged_list = tagged_with_branches({"2024-01-01": memb_list}, TEST_BRANCH_ZIP_CSV)
    assert tagged_list["2024-01-01"].loc[222251]["branch"] == "Central"


def test_branch_zip_plus_four_tagging(late_2023_list: pd.DataFrame):
    """Load a branch_zips file and attempt to apply it to test data to ensure matches when membership list has zip codes formatted with +4"""
    memb_list = data_cleaning(late_2023_list)
    tagged_list = tagged_with_branches({"2024-01-01": memb_list}, TEST_BRANCH_ZIP_CSV)
    assert tagged_list["2024-01-01"].loc[522481]["branch"] == "Portland"


# leading zero padding check is done in test_data_cleaning.py
