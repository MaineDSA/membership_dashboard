"""Provide pytest fixtures for membership list dataframes from various eras."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from src.utils.scan_lists import data_cleaning, scan_memb_list_from_csv

if TYPE_CHECKING:
    import pandas as pd
    from pytest_mock import MockerFixture


def patch_add_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    return df


def scan_list(path: Path) -> pd.DataFrame:
    with path.open() as memb_list:
        return scan_memb_list_from_csv(memb_list)


@pytest.fixture
def late_2023_list(mocker: MockerFixture) -> pd.DataFrame:
    """Provide an un-cleaned membership list in the format of late 2023."""
    mocker.patch("src.utils.geocoding.add_coordinates", new=patch_add_coordinates)
    return scan_list(Path("tests/utils/assets/fake_membership_list_2023_late.csv"))


@pytest.fixture
def late_2023_list_clean(late_2023_list: pd.DataFrame) -> pd.DataFrame:
    """Provide a cleaned membership list in the format of late 2023."""
    return data_cleaning(late_2023_list)


@pytest.fixture
def late_2022_list(mocker: MockerFixture) -> pd.DataFrame:
    """Provide an un-cleaned membership list in the format of late 2022."""
    mocker.patch("src.utils.geocoding.add_coordinates", new=patch_add_coordinates)
    return scan_list(Path("tests/utils/assets/fake_membership_list_2022_late.csv"))


@pytest.fixture
def late_2022_list_clean(late_2022_list: pd.DataFrame) -> pd.DataFrame:
    """Provide a cleaned membership list in the format of late 2022."""
    return data_cleaning(late_2022_list)


@pytest.fixture
def early_2021_list(mocker: MockerFixture) -> pd.DataFrame:
    """Provide an un-cleaned membership list in the format of early 2021."""
    mocker.patch("src.utils.geocoding.add_coordinates", new=patch_add_coordinates)
    return scan_list(Path("tests/utils/assets/fake_membership_list_2021_early.csv"))


@pytest.fixture
def early_2021_list_clean(early_2021_list: pd.DataFrame) -> pd.DataFrame:
    """Provide a cleaned membership list in the format of early 2021."""
    return data_cleaning(early_2021_list)


@pytest.fixture
def early_2020_list(mocker: MockerFixture) -> pd.DataFrame:
    """Provide an un-cleaned membership list in the format of early 2020."""
    mocker.patch("src.utils.geocoding.add_coordinates", new=patch_add_coordinates)
    return scan_list(Path("tests/utils/assets/fake_membership_list_2020_early.csv"))


@pytest.fixture
def early_2020_list_clean(early_2020_list: pd.DataFrame) -> pd.DataFrame:
    """Provide a cleaned membership list in the format of early 2020."""
    return data_cleaning(early_2020_list)
