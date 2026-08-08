"""Perform testing to ensure the data cleaning functions work as expected so that membership lists of different ages can be compared."""

from __future__ import annotations

import importlib.metadata
from typing import TYPE_CHECKING

import geopy.geocoders
import pytest
from geopy.location import Location, Point

from src.utils.geocoding import add_coordinates, get_geocoding

if TYPE_CHECKING:
    import pandas as pd
    from pytest_mock import MockerFixture


TEST_ADDRESSES = {
    "389 Congress St, Portland, ME 04101": Point(43.6592404, -70.2573592),
    "PO Box 13, Turner, ME 04282-0013": Point(44.164922, -70.233281),
    "746 Forest Ave, Portland, ME 04102": Point(43.673720, -70.285727),
}


def patched_geocoder(address: str) -> Location:
    """Return a Location object containing the correct lat/lon if correct test address is provided."""
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

    assert "lat" in late_2023_list.columns
    assert "lon" in late_2023_list.columns

    for member_data in geocoded_df.itertuples():
        address = str(member_data.address1) + ", " + str(member_data.city) + ", " + str(member_data.state) + " " + str(member_data.zip)
        assert address in TEST_ADDRESSES
        assert Point(member_data.lat, member_data.lon) == TEST_ADDRESSES[address]


def test_add_coordinates_disabled_does_nothing(mocker: MockerFixture, late_2023_list: pd.DataFrame) -> None:
    """Check that get_geocoding results in call to geolocator.geocode."""
    mocker.patch("src.utils.geocoding.geolocator", new=None)
    assert add_coordinates(late_2023_list) is late_2023_list


def test_user_agent_creation(mocker: MockerFixture) -> None:
    """Check that get_geocoding results in call to geolocator.geocode."""
    mocker.patch.dict("src.utils.geocoding.config", {"GEOCODER": "nominatim"})
    metadata = importlib.metadata.metadata("membership_dashboard")
    project_urls = dict(item.split(", ", 1) for item in metadata.get_all("Project-URL", []))
    source_url = project_urls.get("source", "No Project URL Defined")

    user_agent = f"{metadata.get('name')}/{metadata.get('version')}; +{source_url}"

    assert geopy.geocoders.options.default_user_agent == user_agent
