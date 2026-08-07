"""Perform testing to ensure the data cleaning functions work as expected so that membership lists of different ages can be compared."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from geopy.location import Location, Point

from src.utils.geocoding import get_geocoding

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def patched_geocoder(address: str) -> Location:
    """Return a Location object containing the correct lat/lon if correct test address is provided."""
    if address != "389 Congress St, Portland, ME 04101":
        pytest.fail("geolocator.geocode did not receive the expected address")
    return Location(address=address, point=Point(45.523063, -122.676483), raw={})


def test_get_geocoding(mocker: MockerFixture) -> None:
    """Check whether get_geocoding calls gets the expected lat/lon coordinates."""
    mocker.patch("src.utils.geocoding.geolocator.geocode", new=patched_geocoder)
    assert get_geocoding.__wrapped__("389 Congress St, Portland, ME 04101") == (45.523063, -122.676483)  # pyright: ignore[reportFunctionMemberAccess]
