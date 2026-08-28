"""W4-01 arena integration — W3-02 round engine with W3-03/04 encounter kernel."""

from __future__ import annotations

from typing import Literal

import numpy as np

from wocbots.agents import HOLLYWOOD_WEIGHTS, Agent
from wocbots.experiments.arena_interaction import ArenaRoundInteractionRunner
from wocbots.experiments.lifecycle import (
    LifecycleRunState,
    SampleFeatures,
    interaction_round_count,
    run_sample,
)


def make_agent(*features: str) -> Agent:
    return Agent(
        features=features or ("budget",),
        eval_accuracy=0.8,
        eval_precision=0.7,
        eval_recall=0.6,
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )


def test_arena_runner_completes_expected_rounds() -> None:
    agents = [make_agent("budget") for _ in range(6)]
    preds: dict[int, Literal[0, 1]] = {id(agent): 1 for agent in agents}
    runner = ArenaRoundInteractionRunner()
    rng = np.random.default_rng(0)
    run_sample(
        agents,
        SampleFeatures(values={"budget": 1.0}),
        preds,
        rng=rng,
        interaction=runner,
        label=1,
    )
    assert runner.last_rounds_completed == interaction_round_count(len(agents))
    assert runner.last_encounter_count >= 0


def test_arena_encounters_update_certainty_and_backfill_history() -> None:
    agents = [make_agent("budget") for _ in range(8)]
    for index, agent in enumerate(agents):
        agent.current_prediction = 1 if index % 2 == 0 else 0

    runner = ArenaRoundInteractionRunner()
    state = LifecycleRunState()
    rng = np.random.default_rng(42)
    before = agents[0].certainty
    preds: dict[int, Literal[0, 1]] = {
        id(agent): agent.current_prediction for agent in agents  # type: ignore[misc]
    }

    run_sample(
        agents,
        SampleFeatures(values={"budget": 1.0}),
        preds,
        rng=rng,
        interaction=runner,
        label=1,
        state=state,
    )

    assert runner.last_encounter_count > 0
    assert len(runner.history_store) == 2 * runner.last_encounter_count
    if before != agents[0].certainty:
        assert agents[0].certainty != before

    records = runner.history_store.get_interactions(sample_id=0)
    assert records
    assert all(record.ground_truth == 1 for record in records)
    assert all(record.partner_correct is not None for record in records)
