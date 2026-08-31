"""W4-01 arena integration — W3-02 round engine with W3-03/04 encounter kernel."""

from __future__ import annotations

from typing import Literal

import numpy as np
import pytest

from wocbots.agents import HOLLYWOOD_WEIGHTS, Agent
from wocbots.experiments.arena_interaction import ArenaRoundInteractionRunner
from wocbots.experiments.lifecycle import (
    LifecycleRunState,
    SampleFeatures,
    interaction_round_count,
    run_sample,
)
from wocbots.interaction import (
    CertaintyFlipScoringPolicy,
    Encounter,
    HistoryStore,
    ReferenceInteractionPolicy,
)
from wocbots.interaction.history import HistoryRecord

# Training-time certainty is (eval_accuracy + eval_precision) / 2 for these agents, and
# `infer_participants` resets every participant to it at the top of each sample (§6.6).
_TRAIN_CERTAINTY = 0.75


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
    # A round period that produces no encounters would silently make the whole W3 layer
    # a no-op, which is exactly the regression this integration exists to prevent.
    assert runner.last_encounter_count > 0
    # Every encounter records BOTH directions (spec §6.5 symmetry).
    assert len(runner.history_store) == 2 * runner.last_encounter_count


def test_arena_encounters_update_certainty_and_backfill_history() -> None:
    agents = [make_agent("budget") for _ in range(8)]
    preds: dict[int, Literal[0, 1]] = {
        id(agent): (1 if index % 2 == 0 else 0) for index, agent in enumerate(agents)
    }

    runner = ArenaRoundInteractionRunner()
    state = LifecycleRunState()
    rng = np.random.default_rng(42)

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
    # The kernel ran for real: interaction moved certainty off the training-time reset value.
    assert any(agent.certainty != _TRAIN_CERTAINTY for agent in agents)

    records = runner.history_store.get_interactions(sample_id=0)
    assert records
    assert all(record.ground_truth == 1 for record in records)
    assert all(record.partner_correct == (record.partner_prediction == 1) for record in records)


def test_trust_update_uses_encounter_time_predictions() -> None:
    """§6.5 doAgree is an encounter-time fact — scoring's flip must not invert its sign.

    Pins the kernel ordering the arena runner depends on: `a` disagrees with `b` when they
    meet, then flips to `b`'s label under scoring. Trust must move by -0.05 (disagreement),
    not +0.05 (the post-flip agreement the wrong ordering would see).
    """
    a = make_agent("budget")
    b = make_agent("budget")
    a.current_prediction, b.current_prediction = 1, 0
    a.certainty, b.certainty = 0.02, 0.99

    history = HistoryStore()
    # One scored prior interaction in the a→b direction only: b_percCorrect = 1.0 for `a`,
    # and None for `b` (no prior history ⇒ no update at all, spec §6.5).
    history.record(
        HistoryRecord(
            sample_id="prior",
            round_num=0,
            agent=a,
            partner=b,
            agent_prediction=1,
            partner_prediction=1,
            agreement=True,
            certainty_before=0.5,
            certainty_after=0.5,
            certainty_delta=0.0,
            prediction_flipped=False,
            partner_correct=True,
            ground_truth=1,
        )
    )

    Encounter(
        a,
        b,
        CertaintyFlipScoringPolicy(),
        ReferenceInteractionPolicy(history_store=history),
        history_store=history,
        sample_id=1,
        round_num=0,
    ).process()

    # Scoring did flip `a` onto `b`'s label — without the flip the pin below proves nothing.
    flipped_prediction: int | None = a.current_prediction
    assert flipped_prediction == 0
    # 0.7 + 0.05 * (1.0 * 1.0) * (-1)
    assert b.trust_score == pytest.approx(0.65)
    # No prior b→a history ⇒ `a`'s trust is untouched.
    assert a.trust_score == pytest.approx(0.7)


def test_reusing_a_scored_sample_id_is_refused_not_silently_relabelled() -> None:
    """A runner outliving its `LifecycleRunState` must not rewrite the earlier pass.

    `run_sample` derives `sample_id` from `len(run_state.sample_results)`, which is unique
    only inside one state. Two stateless calls on one runner would both be sample 0: the
    second files its rows into the first's bucket and back-fills the whole bucket with the
    second label, so `b_percCorrect` (§6.5) reads correctness that never happened.
    """
    agents = [make_agent("budget") for _ in range(6)]
    preds: dict[int, Literal[0, 1]] = {id(agent): 1 for agent in agents}
    sample = SampleFeatures(values={"budget": 1.0})
    runner = ArenaRoundInteractionRunner()
    rng = np.random.default_rng(7)

    run_sample(agents, sample, preds, rng=rng, interaction=runner, label=1, state=None)
    scored = runner.history_store.get_interactions(sample_id=0)
    assert scored
    assert all(record.ground_truth == 1 for record in scored)
    record_count = len(runner.history_store)

    with pytest.raises(ValueError, match="already been scored"):
        run_sample(agents, sample, preds, rng=rng, interaction=runner, label=0, state=None)

    # Refused before any of the second pass's rows landed, so sample 0 is untouched.
    assert len(runner.history_store) == record_count
    assert all(record.ground_truth == 1 for record in scored)


def test_one_run_state_gives_each_sample_its_own_history_bucket() -> None:
    agents = [make_agent("budget") for _ in range(6)]
    preds: dict[int, Literal[0, 1]] = {id(agent): 1 for agent in agents}
    sample = SampleFeatures(values={"budget": 1.0})
    runner = ArenaRoundInteractionRunner()
    state = LifecycleRunState()
    rng = np.random.default_rng(7)

    run_sample(agents, sample, preds, rng=rng, interaction=runner, label=1, state=state)
    run_sample(agents, sample, preds, rng=rng, interaction=runner, label=0, state=state)

    first = runner.history_store.get_interactions(sample_id=0)
    second = runner.history_store.get_interactions(sample_id=1)
    assert first and second
    assert all(record.ground_truth == 1 for record in first)
    assert all(record.ground_truth == 0 for record in second)
    assert len(first) + len(second) == len(runner.history_store)
