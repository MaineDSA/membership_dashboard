"""Validate schema of imported lists using pandera"""

from glob import glob
from ..utils.list_schema import schema
from ..utils.scan_membership_lists import data_cleaning, scan_memb_list_from_csv


def test_schema():
    """Check whether imported lists match defined pandera schema"""
    for membership_list_file in glob("tests/test/harness_assets/fake_membership_list_*.csv"):
        with open(membership_list_file) as membership_csv_data:
            scanned_list = scan_memb_list_from_csv(membership_csv_data)
            cleaned_list = data_cleaning(scanned_list, "2024-01-01")
            assert schema(cleaned_list)
