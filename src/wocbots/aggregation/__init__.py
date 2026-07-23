"""Aggregation mechanisms (voting §7, swarm §8). CORE stream — W4-03 lands voting; W6 lands swarm."""

from wocbots.aggregation.voting import (
    TrustWeightedAggregator,
    UWMAggregator,
    VoteOutcome,
    WVMAggregator,
    certainty_weighted_vote,
    tally_majority,
)

__all__ = [
    "TrustWeightedAggregator",
    "UWMAggregator",
    "VoteOutcome",
    "WVMAggregator",
    "certainty_weighted_vote",
    "tally_majority",
]
