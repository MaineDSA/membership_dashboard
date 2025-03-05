"""Provide pytest fixtures for membership list dataframes from various eras."""

from pathlib import Path

import pandas as pd
import pytest

from src.utils.scan_lists import data_cleaning, scan_memb_list_from_csv


def scan_list(path: Path) -> pd.DataFrame:
    with path.open() as memb_list:
        return scan_memb_list_from_csv(memb_list)


@pytest.fixture
def late_2023_list() -> pd.DataFrame:
    """Provide an un-cleaned membership list in the format of late 2023."""
    return scan_list(Path("tests/utils/assets/fake_membership_list_2023_late.csv"))


@pytest.fixture
def late_2023_list_clean(late_2023_list: pd.DataFrame) -> pd.DataFrame:
    """Provide a cleaned membership list in the format of late 2023."""
    return data_cleaning(late_2023_list)


@pytest.fixture
def late_2022_list() -> pd.DataFrame:
    """Provide an un-cleaned membership list in the format of late 2022."""
    return scan_list(Path("tests/utils/assets/fake_membership_list_2022_late.csv"))


@pytest.fixture
def late_2022_list_clean(late_2022_list: pd.DataFrame) -> pd.DataFrame:
    """Provide a cleaned membership list in the format of late 2022."""
    return data_cleaning(late_2022_list)


@pytest.fixture
def early_2021_list() -> pd.DataFrame:
    """Provide an un-cleaned membership list in the format of early 2021."""
    return scan_list(Path("tests/utils/assets/fake_membership_list_2021_early.csv"))


@pytest.fixture
def early_2021_list_clean(early_2021_list: pd.DataFrame) -> pd.DataFrame:
    """Provide a cleaned membership list in the format of early 2021."""
    return data_cleaning(early_2021_list)


@pytest.fixture
def early_2020_list() -> pd.DataFrame:
    """Provide an un-cleaned membership list in the format of early 2020."""
    return scan_list(Path("tests/utils/assets/fake_membership_list_2020_early.csv"))


@pytest.fixture
def early_2020_list_clean(early_2020_list: pd.DataFrame) -> pd.DataFrame:
    """Provide a cleaned membership list in the format of early 2020."""
    return data_cleaning(early_2020_list)
