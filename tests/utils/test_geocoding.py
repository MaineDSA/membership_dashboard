"""Perform testing to ensure the data cleaning functions work as expected so that membership lists of different ages can be compared."""

from __future__ import annotations

import importlib.metadata
from typing import TYPE_CHECKING

import pytest
from geopy.geocoders.base import Geocoder
from geopy.location import Location, Point

from src.utils.geocoding import METADATA, add_coordinates, get_geocoding

if TYPE_CHECKING:
    from pathlib import Path

    import pandas as pd
    from pytest_mock import MockerFixture


TEST_ADDRESSES = {
    "389 Congress St, Portland, ME 04101": Point(43.6592404, -70.2573592),
    "PO Box 13, Turner, ME 04282-0013": Point(44.164922, -70.233281),
    "746 Forest Ave, Portland, ME 04102": Point(43.673720, -70.285727),
}


def patched_geocoder(address: str) -> Location:
    """Construct a Location object containing the correct lat/lon if known test address is provided."""
    location: Location | None = None
    if address in TEST_ADDRESSES:
        location = Location(address=address, point=TEST_ADDRESSES[address], raw={})
    else:
        pytest.fail("geolocator.geocode did not receive an expected address")
    return location


@pytest.mark.parametrize(("address", "point"), TEST_ADDRESSES.items())
def test_get_geocoding(mocker: MockerFixture, address: str, point: Point) -> None:
    """Check that get_geocoding results in call to geolocator.geocode."""
    mocker.patch("src.utils.geocoding.geolocator")
    mocker.patch("src.utils.geocoding.geolocator.geocode", new=patched_geocoder)
    assert get_geocoding.__wrapped__(address) == (point.latitude, point.longitude)  # pyright: ignore[reportFunctionMemberAccess]


def test_get_geocoding_cache(mocker: MockerFixture, tmp_path: Path) -> None:
    """Check that identical src.utils.geocoding.get_geocoding calls only result in one call to geolocator.geocode."""
    address = "389 Congress St, Portland, ME 04101"
    point = Point(43.6592404, -70.2573592)

    import src.utils.geocoding as gc  # noqa: PLC0415 import-outside-top-level

    importlib.reload(gc)

    mocker.patch("src.utils.geocoding.DB_DIR", tmp_path)
    mocker.patch("src.utils.geocoding.geolocator")
    spy = mocker.patch("src.utils.geocoding.geolocator.geocode", side_effect=patched_geocoder)

    assert gc.get_geocoding(address) == (point.latitude, point.longitude)
    assert spy.call_count == 1
    assert gc.get_geocoding(address) == (point.latitude, point.longitude)
    assert spy.call_count == 1


@pytest.mark.parametrize("address", TEST_ADDRESSES.keys())
def test_get_geocoding_disabled_returns_0_0(mocker: MockerFixture, address: str) -> None:
    """Check that get_geocoding returns ``(0, 0)`` when geolocator is disabled."""
    mocker.patch("src.utils.geocoding.geolocator", new=None)
    assert get_geocoding.__wrapped__(address) == (0, 0)  # pyright: ignore[reportFunctionMemberAccess]


def test_add_coordinates_calls_get_geocoding_on_each(mocker: MockerFixture, late_2023_list: pd.DataFrame) -> None:
    """Check that get_geocoding results in call to geolocator.geocode."""
    mocker.patch("src.utils.geocoding.geolocator")
    mocker.patch("src.utils.geocoding.geolocator.geocode", new=patched_geocoder)

    assert "lat" not in late_2023_list.columns
    assert "lon" not in late_2023_list.columns

    geocoded_df = add_coordinates(late_2023_list)

    assert "lat" in geocoded_df.columns
    assert "lon" in geocoded_df.columns

    for member_data in geocoded_df.itertuples():
        address = str(member_data.address1) + ", " + str(member_data.city) + ", " + str(member_data.state) + " " + str(member_data.zip)
        assert address in TEST_ADDRESSES
        assert Point(member_data.lat, member_data.lon) == TEST_ADDRESSES[address]


def test_add_coordinates_disabled_does_nothing(mocker: MockerFixture, late_2023_list: pd.DataFrame) -> None:
    """Check that get_geocoding results in call to geolocator.geocode."""
    mocker.patch("src.utils.geocoding.geolocator", new=None)
    assert add_coordinates(late_2023_list) is late_2023_list


def test_user_agent_creation() -> None:
    """Check that user agent is created and set correctly."""
    project_urls = dict(item.split(", ", 1) for item in METADATA.get_all("Project-URL", []))
    source_url = project_urls.get("source", "No Repo URL Defined")
    user_agent = f"{METADATA.get('name')}/{METADATA.get('version')}; +{source_url}"

    geolocator = Geocoder()
    assert geolocator.headers["User-Agent"] == user_agent
