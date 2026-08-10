from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from zipfile import ZipFile

import pandas as pd

from src.utils.scan_lists import _scan_all_membership_lists, _scan_memb_list_from_zip

from .conftest import patch_add_coordinates

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

MEMBERSHIP_LIST_NAME = "test_membership_list"


def test_scan_from_zip(mocker: MockerFixture, tmp_path: Path) -> None:
    mocker.patch("src.utils.geocoding.add_coordinates", new=patch_add_coordinates)
    new_zip = tmp_path / f"{MEMBERSHIP_LIST_NAME}.zip"
    with ZipFile(new_zip, mode="x") as z_f:
        z_f.write(filename=Path("tests/utils/assets/fake_membership_list_2023_late.csv"), arcname=f"{MEMBERSHIP_LIST_NAME}.csv")

    membership_list = _scan_memb_list_from_zip(str(new_zip), MEMBERSHIP_LIST_NAME)
    assert isinstance(membership_list, pd.DataFrame)

    membership_list.set_index("actionkit_id", inplace=True)
    person = membership_list.loc[222251]
    assert str(person["address1"]) == "PO Box 13"
    assert str(person["city"]) == "Turner"
    assert str(person["state"]) == "ME"
    assert str(person["zip"]) == "04282-0013"


def test_all_zip_lists(mocker: MockerFixture, tmp_path: Path) -> None:
    mocker.patch("src.utils.geocoding.add_coordinates", new=patch_add_coordinates)
    csv_files = {
        "2023_09_03": Path("tests/utils/assets/fake_membership_list_2023_late.csv"),
        "2023-09-02": Path("tests/utils/assets/fake_membership_list_2023_late.csv"),
        "20230901": Path("tests/utils/assets/fake_membership_list_2023_late.csv"),
        "20220901": Path("tests/utils/assets/fake_membership_list_2022_late.csv"),
        "20210101": Path("tests/utils/assets/fake_membership_list_2021_early.csv"),
        "20200101": Path("tests/utils/assets/fake_membership_list_2020_early.csv"),
    }
    lists_dir = tmp_path / MEMBERSHIP_LIST_NAME
    lists_dir.mkdir()
    for date, csv_file in csv_files.items():
        new_zip = lists_dir / f"{MEMBERSHIP_LIST_NAME}_{date}.zip"
        with ZipFile(new_zip, mode="x") as z_f:
            z_f.write(filename=csv_file, arcname=f"{MEMBERSHIP_LIST_NAME}.csv")

    membership_lists = _scan_all_membership_lists(MEMBERSHIP_LIST_NAME, tmp_path)
    assert len(membership_lists) == 6
    for membership_list in membership_lists.values():
        assert isinstance(membership_list, pd.DataFrame)
