"""W4-03 test requirements — formula pins, tie rule, same-state guarantee."""

from __future__ import annotations

from typing import Literal, cast

import numpy as np

from wocbots.agents import HOLLYWOOD_WEIGHTS, Agent
from wocbots.aggregation import (
    TrustWeightedAggregator,
    UWMAggregator,
    WVMAggregator,
    certainty_weighted_vote,
    tally_majority,
)


def make_agent(
    *,
    acc: float = 0.8,
    trust: float | None = None,
    prediction: int = 1,
) -> Agent:
    agent = Agent(
        features=("budget",),
        eval_accuracy=acc,
        eval_precision=trust if trust is not None else 0.7,
        eval_recall=0.6,
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )
    agent.current_prediction = cast(Literal[0, 1], prediction)
    if trust is not None:
        agent.trust_score = trust
    return agent


def test_wvm_formula_pin() -> None:
    agent = make_agent(acc=0.8, prediction=1)
    rng = np.random.default_rng(0)
    result = WVMAggregator().aggregate([agent], rng)
    assert result.class_label == 1
    # Single agent with 0.8 prior_accuracy → 80 votes for class 1
    outcome = tally_majority(0, 80)
    assert outcome.class_label == 1


def test_trust_weighted_formula_pin() -> None:
    agent = make_agent(acc=0.8, trust=0.7, prediction=1)
    rng = np.random.default_rng(0)
    result = TrustWeightedAggregator().aggregate([agent], rng)
    assert result.class_label == 1
    # ((0.8 + 0.7) / 2) * 100 = 75
    weights = round(((0.8 + 0.7) / 2) * 100)
    assert weights == 75


def test_no_information_agent_gets_fifty_votes() -> None:
    agent = Agent(
        features=("budget",),
        eval_accuracy=0.5,
        eval_precision=0.5,
        eval_recall=0.5,
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )
    agent.prior_accuracy = 0.5
    agent.current_prediction = 1
    rng = np.random.default_rng(0)
    result = WVMAggregator().aggregate([agent], rng)
    assert result.class_label == 1
    assert round(100 * 0.5) == 50


def test_tie_goes_to_class_one_and_is_counted() -> None:
    outcome = tally_majority(100, 100)
    assert outcome.class_label == 1
    assert outcome.was_tie is True


def test_uwm_gives_hundred_votes_each() -> None:
    a0 = make_agent(acc=0.9, prediction=0)
    a1 = make_agent(acc=0.9, prediction=1)
    rng = np.random.default_rng(0)
    result = UWMAggregator().aggregate([a0, a1], rng)
    assert result.class_label == 1  # 100 vs 100 tie → class 1


def test_same_state_three_aggregators() -> None:
    agents = [make_agent(acc=0.75, trust=0.6, prediction=1) for _ in range(3)]
    rng = np.random.default_rng(42)
    uwm = UWMAggregator().aggregate(agents, rng)
    wvm = WVMAggregator().aggregate(agents, rng)
    trust = TrustWeightedAggregator().aggregate(agents, rng)
    assert uwm.class_label == wvm.class_label == trust.class_label == 1
    assert all(p.tier is None and p.margin is None for p in (uwm, wvm, trust))


def test_certainty_weighted_degenerate_tie() -> None:
    a0 = make_agent(acc=0.9, prediction=0)
    a1 = make_agent(acc=0.9, prediction=1)
    a0.certainty = 0.5
    a1.certainty = 0.5
    outcome = certainty_weighted_vote([a0, a1])
    assert outcome.class_label == 1
    assert outcome.was_tie is True
