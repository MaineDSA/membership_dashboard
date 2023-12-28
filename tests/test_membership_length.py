"""Perform testing to ensure membership length calculation is correct"""

from ..scan_membership_lists import membership_length


def test_membership_length():
    """Ensure membership length calculation is correct"""
    assert membership_length("1982-06-01", list_date="2023-01-01") == 40
