"""Provide pytest fixtures for membership list dataframes from various ages"""
import pandas as pd
import pytest

from src.utils.scan_lists import scan_memb_list_from_csv


def scan_list(path: str) -> pd.DataFrame:
    with open(path) as memb_list:
        return scan_memb_list_from_csv(memb_list)


@pytest.fixture
def late_2023_list() -> pd.DataFrame:
    return scan_list("tests/test_harness_assets/fake_membership_list_2023_late.csv")


@pytest.fixture
def late_2022_list() -> pd.DataFrame:
    return scan_list("tests/test_harness_assets/fake_membership_list_2022_late.csv")


@pytest.fixture
def early_2021_list() -> pd.DataFrame:
    return scan_list("tests/test_harness_assets/fake_membership_list_2021_early.csv")


@pytest.fixture
def early_2020_list() -> pd.DataFrame:
    return scan_list("tests/test_harness_assets/fake_membership_list_2020_early.csv")
