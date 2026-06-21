"""Unit tests for the pure arithmetic functions."""

import pytest

from app.calc import add, is_even


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (2, 3, 5),
        (0, 0, 0),
        (-1, 1, 0),
        (-5, -7, -12),
        (1_000_000_000, 1_000_000_000, 2_000_000_000),
    ],
)
def test_add(a: int, b: int, expected: int) -> None:
    assert add(a, b) == expected


@pytest.mark.parametrize(
    ("n", "expected"),
    [(0, True), (2, True), (-2, True), (1, False), (-1, False), (1_000_000_001, False)],
)
def test_is_even(n: int, expected: bool) -> None:
    assert is_even(n) is expected
