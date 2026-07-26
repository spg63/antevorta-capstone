"""W4-03 — voting aggregators (spec §7 mechanisms 1–3).

UWM, WVM, and trust-weighted majority vote over a frozen participant snapshot.
Ties go to class 1 (spec §7). `prior_accuracy` and `trust_score` are rates in [0, 1]
for vote allocation; never use `prior_performance` here (spec §10 pitfall 2 / §10.4).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np

from wocbots.agents import Agent
from wocbots.types import Prediction


@dataclass(frozen=True)
class VoteOutcome:
    """Result of a vote tally (internal; tests pin the arithmetic)."""

    class_label: Literal[0, 1]
    was_tie: bool
    votes_0: int
    votes_1: int

    def to_prediction(self) -> Prediction:
        """Public output for the Aggregator seam (tier/margin filled by W4-04)."""
        return Prediction(class_label=self.class_label, tier=None, margin=None)


def tally_majority(votes_0: int, votes_1: int) -> VoteOutcome:
    """Majority of vote totals; exact ties → class 1 (spec §7 tie rule)."""
    if votes_0 > votes_1:
        return VoteOutcome(class_label=0, was_tie=False, votes_0=votes_0, votes_1=votes_1)
    if votes_1 > votes_0:
        return VoteOutcome(class_label=1, was_tie=False, votes_0=votes_0, votes_1=votes_1)
    return VoteOutcome(class_label=1, was_tie=True, votes_0=votes_0, votes_1=votes_1)


def certainty_weighted_vote(participants: Sequence[Agent]) -> VoteOutcome:
    """Degenerate-crowd rule (spec §3, §8.2 Low fallback): score_c = Σ certainty for class c."""
    _require_predictions(participants)
    score_0 = sum(a.certainty for a in participants if a.current_prediction == 0)
    score_1 = sum(a.certainty for a in participants if a.current_prediction == 1)
    if score_0 > score_1:
        return VoteOutcome(
            class_label=0,
            was_tie=False,
            votes_0=int(round(score_0 * 100)),
            votes_1=int(round(score_1 * 100)),
        )
    if score_1 > score_0:
        return VoteOutcome(
            class_label=1,
            was_tie=False,
            votes_0=int(round(score_0 * 100)),
            votes_1=int(round(score_1 * 100)),
        )
    return VoteOutcome(
        class_label=1,
        was_tie=True,
        votes_0=int(round(score_0 * 100)),
        votes_1=int(round(score_1 * 100)),
    )


def _require_predictions(participants: Sequence[Agent]) -> None:
    if len(participants) == 0:
        raise ValueError("aggregation requires at least one participant")
    for agent in participants:
        if agent.current_prediction is None:
            raise ValueError("every participant must have a current_prediction before aggregation")


def _allocate_votes(participants: Sequence[Agent], votes_per_agent: Sequence[int]) -> VoteOutcome:
    votes_0 = 0
    votes_1 = 0
    for agent, weight in zip(participants, votes_per_agent, strict=True):
        if agent.current_prediction == 0:
            votes_0 += weight
        else:
            votes_1 += weight
    return tally_majority(votes_0, votes_1)


class UWMAggregator:
    """Unweighted Mean Model: 100 votes per participant for its predicted class (spec §7.1)."""

    def aggregate(self, participants: Sequence[Agent], rng: np.random.Generator) -> Prediction:
        del rng  # voting is deterministic; rng satisfies the Aggregator seam for W6 parity
        _require_predictions(participants)
        weights = [100] * len(participants)
        return _allocate_votes(participants, weights).to_prediction()


class WVMAggregator:
    """Weighted Voter Model: round(100 × prior_accuracy) per participant (spec §7.2)."""

    def aggregate(self, participants: Sequence[Agent], rng: np.random.Generator) -> Prediction:
        del rng
        _require_predictions(participants)
        weights = [round(100 * a.prior_accuracy) for a in participants]
        return _allocate_votes(participants, weights).to_prediction()


class TrustWeightedAggregator:
    """Trust-weighted: round(((prior_accuracy + trust_score) / 2) × 100) (spec §7.3)."""

    def aggregate(self, participants: Sequence[Agent], rng: np.random.Generator) -> Prediction:
        del rng
        _require_predictions(participants)
        weights = [round(((a.prior_accuracy + a.trust_score) / 2) * 100) for a in participants]
        return _allocate_votes(participants, weights).to_prediction()
