from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from zipfile import ZipFile

import pandas as pd

from src.utils.scan_lists import _scan_memb_list_from_zip

from .conftest import patch_add_coordinates

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_scan_from_zip(mocker: MockerFixture, tmp_path: Path) -> None:
    mocker.patch("src.utils.geocoding.add_coordinates", new=patch_add_coordinates)
    new_zip = tmp_path / "test_membership_list.zip"
    with ZipFile(new_zip, mode="x") as z_f:
        z_f.write(filename=Path("tests/utils/assets/fake_membership_list_2023_late.csv"), arcname="test_membership_list.csv")

    membership_list = _scan_memb_list_from_zip(str(new_zip), "test_membership_list")
    assert isinstance(membership_list, pd.DataFrame)

    membership_list.set_index("actionkit_id", inplace=True)
    person = membership_list.loc[222251]
    assert str(person["address1"]) == "PO Box 13"
    assert str(person["city"]) == "Turner"
    assert str(person["state"]) == "ME"
    assert str(person["zip"]) == "04282-0013"
