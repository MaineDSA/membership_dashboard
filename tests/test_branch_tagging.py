"""Perform testing to ensure members are being tagged with a branch based on their zip code"""

from pathlib import Path

from src.utils.scan_lists import data_cleaning, tagged_with_branches, scan_memb_list_from_csv

TEST_BRANCH_ZIP_CSV = Path("tests/test_harness_assets/fake_branch_zips.csv")


def test_branch_zip_tagging():
    """Load a branch_zips file and attempt to apply it to test data"""
    with open("tests/test_harness_assets/fake_membership_list_2023_late.csv") as memb_list:
        memb_list = data_cleaning(scan_memb_list_from_csv(memb_list))
        tagged_list = tagged_with_branches({"2024-01-01": memb_list}, TEST_BRANCH_ZIP_CSV)
        assert tagged_list["2024-01-01"].loc[222251]["branch"] == "Central"


def test_branch_zip_plus_four_tagging():
    """Load a branch_zips file and attempt to apply it to test data"""
    with open("tests/test_harness_assets/fake_membership_list_2023_late.csv") as memb_list:
        memb_list = data_cleaning(scan_memb_list_from_csv(memb_list))
        tagged_list = tagged_with_branches({"2024-01-01": memb_list}, TEST_BRANCH_ZIP_CSV)
        assert tagged_list["2024-01-01"].loc[522481]["branch"] == "Portland"
