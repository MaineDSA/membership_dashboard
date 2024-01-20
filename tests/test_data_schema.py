"""Validate schema of imported lists using pandera"""

from glob import glob
from pathlib import Path, PurePath

from src.utils.scan_lists import data_cleaning
from src.utils.schema import schema
from tests.conftest import scan_list


def test_schema():
    """Check whether imported lists match defined pandera schema"""
    for membership_list_file in glob(str(Path(PurePath(__file__).parent, "tests/test_harness_assets/fake_membership_list_*.csv"))):
        cleaned_list = data_cleaning(scan_list(membership_list_file))
        assert schema(cleaned_list)
