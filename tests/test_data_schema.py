"""Validate schema of imported lists using pandera"""

from glob import glob
from pathlib import Path, PurePath

from ..src.utils.scan_lists import data_cleaning, scan_memb_list_from_csv
from ..src.utils.schema import schema


def test_schema():
    """Check whether imported lists match defined pandera schema"""
    for membership_list_file in glob(str(Path(PurePath(__file__).parent, "tests/test_harness_assets/fake_membership_list_*.csv"))):
        with open(membership_list_file) as membership_csv_data:
            scanned_list = scan_memb_list_from_csv(membership_csv_data)
            cleaned_list = data_cleaning(scanned_list)
            assert schema(cleaned_list)
