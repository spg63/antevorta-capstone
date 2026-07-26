"""W4-01 + W4-02 tests — reset semantics, sit-out, feedback pins, degenerate path."""

from __future__ import annotations

from typing import Literal

import numpy as np

from wocbots.agents import HOLLYWOOD_WEIGHTS, Agent
from wocbots.experiments.feedback import FeedbackState, apply_ground_truth, prior_performance_from_running_acc
from wocbots.experiments.lifecycle import (
    LifecycleRunState,
    NoOpInteractionRunner,
    SampleFeatures,
    arena_cell_count,
    interaction_round_count,
    run_sample,
    select_participants,
)


def make_agent(*features: str, acc: float = 0.8) -> Agent:
    agent = Agent(
        features=features or ("budget",),
        eval_accuracy=acc,
        eval_precision=0.7,
        eval_recall=0.6,
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )
    return agent


def test_reset_semantics_certainty_reinits_trust_persists() -> None:
    agents = [make_agent("budget"), make_agent("vote_count")]
    state = LifecycleRunState()
    rng = np.random.default_rng(0)

    for label in (0, 1, 0):
        preds: dict[int, Literal[0, 1]] = {id(agents[0]): 0, id(agents[1]): 1}
        train_certainty = agents[0].certainty
        agents[0].trust_score = 0.55
        agents[0].certainty = 0.99
        run_sample(
            agents,
            SampleFeatures(values={"budget": 1.0, "vote_count": 2.0}),
            preds,
            rng=rng,
            interaction=NoOpInteractionRunner(),
            label=label,
            state=state,
        )
        assert agents[0].certainty == train_certainty
        assert agents[0].trust_score == 0.55


def test_sit_out_excludes_feature_dependent_agents() -> None:
    a_budget = make_agent("budget")
    a_vote = make_agent("budget", "vote_count")
    sample = SampleFeatures(values={"budget": 1.0})
    selected, skipped = select_participants([a_budget, a_vote], sample)
    assert selected == [a_budget]
    assert skipped == 1
    assert arena_cell_count(len(selected)) == 2
    assert interaction_round_count(len(selected)) == 10


def test_degenerate_two_participants_skips_arena() -> None:
    agents = [make_agent("budget"), make_agent("budget")]
    state = LifecycleRunState()
    rng = np.random.default_rng(0)
    preds: dict[int, Literal[0, 1]] = {id(agents[0]): 0, id(agents[1]): 1}
    result = run_sample(
        agents,
        SampleFeatures(values={"budget": 1.0}),
        preds,
        rng=rng,
        label=0,
        state=state,
    )
    assert result.used_degenerate_path is True
    assert result.participant_count == 2
    assert result.prediction.tier == "low"
    assert state.feedback.degenerate_crowd_count == 1


def test_prior_performance_cold_start_then_engages() -> None:
    assert prior_performance_from_running_acc(1.0, scored_count=4) == 1.0
    assert prior_performance_from_running_acc(1.0, scored_count=5) == 1.3
    assert prior_performance_from_running_acc(0.5, scored_count=5) == 1.0
    assert prior_performance_from_running_acc(0.0, scored_count=5) == 0.7


def test_prior_accuracy_replaced_at_fifth_scored() -> None:
    agent = make_agent("budget", acc=0.8)
    state = FeedbackState()
    for correct in (True, True, True, True):
        agent.current_prediction = 1
        apply_ground_truth([agent], 1 if correct else 0, state)
        assert agent.prior_accuracy == 0.8
    agent.current_prediction = 1
    apply_ground_truth([agent], 1, state)
    assert agent.prior_accuracy == 1.0


def test_label_free_leaves_track_records_untouched() -> None:
    agent = make_agent("budget", acc=0.8)
    before_acc = agent.prior_accuracy
    before_perf = agent.prior_performance
    apply_ground_truth([agent], None, FeedbackState())
    assert agent.prior_accuracy == before_acc
    assert agent.prior_performance == before_perf
