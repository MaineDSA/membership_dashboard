"""Perform testing to ensure members are being tagged with a branch based on their zip code"""

from pathlib import Path
import pandas as pd

from ..scan_membership_lists import data_cleaning, tag_branch_zips


def test_branch_zip_tagging():
    """Load a branch_zips file and attempt to apply it to test data"""
    with open("tests/test_harness_assets/fake_membership_list_2023_late.csv") as memb_list:
        memb_list = data_cleaning(pd.read_csv(memb_list, header=0), "2024-01-01")
        tagged_list = tag_branch_zips({"2024-01-01": memb_list}, Path("tests/test_harness_assets/fake_branch_zips.csv"))
        assert tagged_list["2024-01-01"].loc[55222]["branch"] == "Midcoast"
