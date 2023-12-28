"""Check known edge cases and possible regressions"""

from ..scan_membership_lists import membership_length


def test_membership_length():
	assert membership_length("1982-06-01", list_date="2023-01-01") == 40
