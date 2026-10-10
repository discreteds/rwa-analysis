"""Comparator owns rejection of metadata drift and incomplete schemas."""

import pytest


@pytest.mark.parametrize(
    ("actual", "expected", "path"),
    [
        (
            {"bands": [{"upper_inclusive": True}]},
            {"bands": [{"upper_inclusive": False}]},
            "bands[0].upper_inclusive",
        ),
        ({"row": {}}, {"row": {"ead": "1"}}, "row.ead"),
        ({"row": {"ead": "1", "unknown": 2}}, {"row": {"ead": "1"}}, "row.unknown"),
    ],
)
def test_complete_comparison_rejects_drift(actual, expected, path):
    from tests.support.golden import assert_golden

    with pytest.raises(AssertionError) as error:
        assert_golden(actual, expected)
    assert path in str(error.value)
