"""Perform testing to ensure members are being tagged with a branch based on their zip code"""

from pathlib import Path

import pandas as pd

from src.utils.scan_lists import tagged_with_branches, branch_name_from_zip_code

TEST_BRANCH_ZIP_CSV = Path("tests/test_harness_assets/fake_branch_zips.csv")


def test_branch_name_from_zip_code():
    """Ensure branch_name_from_zip_code provides the correct zip using known test data"""
    branch_zips = pd.read_csv(TEST_BRANCH_ZIP_CSV, dtype={"zip": str}, index_col="zip")
    assert branch_name_from_zip_code("04102", branch_zips) == "Portland"
    assert branch_name_from_zip_code("04011", branch_zips) == "Midcoast"


def test_branch_zip_tagging(late_2023_list_clean: pd.DataFrame):
    """Load a branch_zips file and attempt to apply it to test data, including for members whose zips are +4"""
    tagged_list = tagged_with_branches({"2024-01-01": late_2023_list_clean}, TEST_BRANCH_ZIP_CSV)
    assert tagged_list["2024-01-01"].loc[222251]["branch"] == "Central"
    assert tagged_list["2024-01-01"].loc[522481]["branch"] == "Portland"


# leading zero padding check is done in test_data_cleaning.py
