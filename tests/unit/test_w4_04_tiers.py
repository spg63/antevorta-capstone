"""W4-04 tier boundary pins (spec §7)."""

from __future__ import annotations

import pytest

from wocbots.aggregation.tiers import tier_from_margin, vote_margin


@pytest.mark.parametrize(
    ("votes_0", "votes_1", "expected_margin"),
    [
        (949, 51, 0.949),
        (951, 49, 0.951),
        (899, 101, 0.899),
        (901, 99, 0.901),
        (749, 251, 0.749),
        (751, 249, 0.751),
        (649, 351, 0.649),
        (651, 349, 0.651),
        (519, 481, 0.519),
        (521, 479, 0.521),
    ],
)
def test_vote_margin_boundaries(votes_0: int, votes_1: int, expected_margin: float) -> None:
    assert vote_margin(votes_0, votes_1) == pytest.approx(expected_margin)


@pytest.mark.parametrize(
    ("margin", "expected_tier"),
    [
        (0.949, "very-high"),
        (0.951, "near-certain"),
        (0.899, "high"),
        (0.901, "very-high"),
        (0.749, "medium"),
        (0.751, "high"),
        (0.649, "low"),
        (0.651, "medium"),
        (0.519, "coin-flip"),
        (0.521, "low"),
    ],
)
def test_tier_boundaries_both_sides(margin: float, expected_tier: str) -> None:
    assert tier_from_margin(margin) == expected_tier
