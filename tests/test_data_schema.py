"""Validate schema of imported lists using pandera"""

import os
from glob import glob
from ..utils.list_schema import schema
from ..utils.scan_membership_lists import data_cleaning, scan_memb_list_from_csv


def test_schema():
    """Check whether imported lists match defined pandera schema"""
    files = glob(os.path.join("tests/test/harness_assets", "fake_membership_list_*.csv"))
    for membership_list_file in files:
        with open(membership_list_file) as membership_csv:
            cleaned_list = data_cleaning(scan_memb_list_from_csv(membership_csv), "2024-01-01")
            schema(cleaned_list)
