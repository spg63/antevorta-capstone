"""W4-04 — vote-margin confidence tiers (spec §7).

Boundary ownership (lower bound inclusive, upper exclusive except the top bucket):
  >= 0.95  near-certain
  >= 0.90  very-high
  >= 0.75  high
  >= 0.65  medium
  >= 0.52  low
  <  0.52  coin-flip
"""

from __future__ import annotations

from typing import Literal

from wocbots.types import Prediction


def vote_margin(votes_0: int, votes_1: int) -> float:
    """Winning vote share in [0, 1]: max(votes_0, votes_1) / total."""
    total = votes_0 + votes_1
    if total <= 0:
        return 0.0
    return max(votes_0, votes_1) / total


def tier_from_margin(margin: float) -> str:
    """Map a vote margin to its confidence bucket (spec §7)."""
    if margin >= 0.95:
        return "near-certain"
    if margin >= 0.90:
        return "very-high"
    if margin >= 0.75:
        return "high"
    if margin >= 0.65:
        return "medium"
    if margin >= 0.52:
        return "low"
    return "coin-flip"


def prediction_with_margin(
    *,
    class_label: Literal[0, 1],
    votes_0: int,
    votes_1: int,
) -> Prediction:
    """Build a `Prediction` with tier/margin filled from vote totals."""
    margin = vote_margin(votes_0, votes_1)
    return Prediction(
        class_label=class_label,
        tier=tier_from_margin(margin),
        margin=margin,
    )
