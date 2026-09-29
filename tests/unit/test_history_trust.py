"""W3-04 test plan (plan §10, exact pins) — interaction history and trust updates.

Maps to the plan's §10 test list:
- Test 1: Ticket Req 1 — No-history encounter -> no trust update (also un-scored records).
- Test 2: Ticket Req 2 — Capped movement & clamp boundaries (both signs, |Δtrust| <= 0.05 at priorPerf=1.0).
- Test 3: Ticket Req 3 — percCorrect over scripted history (hand-computed pin, 1e-9).
- Test 4: Ticket Req 4 — Store completeness & cardinality (scripted arena, 1 encounter -> 2 directed rows).
- Test 5: Ticket Req 4 — Back-fill hook isolation (correctness flips without touching other fields).
- Test 6: Queryable tidy DataFrame export.
- Test 7: Separation of prior_performance vs prior_accuracy (forbidden-shortcut guard).
- Test 8: Degenerate and defensive inputs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from wocbots.agents import HOLLYWOOD_WEIGHTS, Agent
from wocbots.arena import Arena, RandomInitPolicy, RandomMovementPolicy, RoundEngine
from wocbots.interaction import (
    CertaintyFlipScoringPolicy,
    Encounter,
    HistoryRecord,
    HistoryStore,
    ReferenceInteractionPolicy,
)


def make_agent(
    acc: float = 0.5,
    prec: float = 0.5,
    rec: float = 0.5,
    features: tuple[str, ...] = ("f0",),
) -> Agent:
    return Agent(
        features=features,
        eval_accuracy=acc,
        eval_precision=prec,
        eval_recall=rec,
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )


# ---- test 1: ticket req 1 — no-history encounter -> no trust update ----


def test_no_history_encounter_no_trust_update() -> None:
    a = make_agent()
    a.current_prediction = 1
    b = make_agent()
    b.current_prediction = 1
    b.trust_score = 0.78

    store = HistoryStore()
    policy = ReferenceInteractionPolicy(history_store=store)

    # 1a: Empty history store -> no update
    policy.update_trust(a, b)
    assert b.trust_score == 0.78

    # 1b: Unscored history exists (e.g. current sample, partner_correct is None) -> no update
    rec = HistoryRecord(
        sample_id=0,
        round_num=0,
        agent=a,
        partner=b,
        agent_prediction=1,
        partner_prediction=1,
        agreement=True,
        certainty_before=0.6,
        certainty_after=0.7,
        certainty_delta=0.1,
        prediction_flipped=False,
        partner_correct=None,  # unscored
        ground_truth=None,
    )
    store.record(rec)
    policy.update_trust(a, b)
    assert b.trust_score == 0.78


# ---- test 2: ticket req 2 — capped movement & clamp boundaries (both signs) ----


def test_capped_movement_and_clamp_boundaries() -> None:
    a = make_agent()
    a.current_prediction = 1
    b = make_agent()
    b.current_prediction = 1
    b.prior_performance = 1.0

    store = HistoryStore()
    # Record 1 past interaction where b was correct (percCorrect = 1.0)
    store.record(
        HistoryRecord(
            sample_id=0,
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
    policy = ReferenceInteractionPolicy(history_store=store)

    # 2a: Agreement (doAgree = +1): delta = 0.05 * 1.0 * 1.0 * 1 = +0.05
    b.trust_score = 0.50
    policy.update_trust(a, b)
    assert abs(b.trust_score - 0.55) < 1e-9

    # 2b: Disagreement (doAgree = -1): delta = 0.05 * 1.0 * 1.0 * (-1) = -0.05
    b.current_prediction = 0
    b.trust_score = 0.50
    policy.update_trust(a, b)
    assert abs(b.trust_score - 0.45) < 1e-9

    # 2c: Upper clamp saturation: 0.98 + 0.05 = 1.03 -> clamped to 1.0
    b.current_prediction = 1  # agrees
    b.trust_score = 0.98
    policy.update_trust(a, b)
    assert b.trust_score == 1.0

    # 2d: Lower clamp saturation: 0.02 - 0.05 = -0.03 -> clamped to 0.0
    b.current_prediction = 0  # disagrees
    b.trust_score = 0.02
    policy.update_trust(a, b)
    assert b.trust_score == 0.0


# ---- test 3: ticket req 3 — percCorrect over scripted history (hand-computed pin) ----


def test_perc_correct_scripted_history_pin() -> None:
    a = make_agent()
    a.current_prediction = 1
    b = make_agent()
    b.current_prediction = 1
    b.prior_performance = 1.1
    b.trust_score = 0.50

    store = HistoryStore()
    # Scripted history: 4 past scored interactions (3 correct, 1 incorrect) -> percCorrect = 0.75
    scripted_outcomes = [
        (1, 1, True),  # sample 0: b predicted 1, label 1 -> correct
        (0, 1, False),  # sample 1: b predicted 0, label 1 -> incorrect
        (1, 1, True),  # sample 2: b predicted 1, label 1 -> correct
        (0, 0, True),  # sample 3: b predicted 0, label 0 -> correct
    ]
    for s_id, (pred_b, gt, is_correct) in enumerate(scripted_outcomes):
        store.record(
            HistoryRecord(
                sample_id=s_id,
                round_num=0,
                agent=a,
                partner=b,
                agent_prediction=1,
                partner_prediction=pred_b,  # type: ignore[arg-type]
                agreement=(pred_b == 1),
                certainty_before=0.5,
                certainty_after=0.5,
                certainty_delta=0.0,
                prediction_flipped=False,
                partner_correct=is_correct,
                ground_truth=gt,  # type: ignore[arg-type]
            )
        )

    perc_correct = store.get_perc_correct(a, b)
    assert perc_correct is not None
    assert abs(perc_correct - 0.75) < 1e-9

    policy = ReferenceInteractionPolicy(history_store=store)

    # 3a: Agreement -> delta = 0.05 * (0.75 * 1.1) * (+1) = 0.04125 -> new trust = 0.54125
    policy.update_trust(a, b)
    assert abs(b.trust_score - 0.54125) < 1e-9

    # 3b: Disagreement -> delta = -0.04125 -> from 0.50 -> new trust = 0.45875
    b.trust_score = 0.50
    b.current_prediction = 0
    policy.update_trust(a, b)
    assert abs(b.trust_score - 0.45875) < 1e-9


# ---- test 4: ticket req 4 — store completeness and cardinality ----


def test_store_completeness_and_cardinality() -> None:
    rng = np.random.default_rng(42)
    agents = [make_agent() for _ in range(5)]
    for i, ag in enumerate(agents):
        ag.current_prediction = i % 2  # type: ignore[assignment]
        ag.certainty = 0.6

    arena = Arena(len(agents))
    init_policy = RandomInitPolicy()
    for ag in agents:
        cell = init_policy.place(ag, arena, rng)
        arena.place(ag, cell)

    round_engine = RoundEngine(agents, arena, RandomMovementPolicy(), rng)

    scoring_policy = CertaintyFlipScoringPolicy()
    store = HistoryStore()
    interaction_policy = ReferenceInteractionPolicy(history_store=store)

    total_encounters = 0
    # Run 2 rounds
    for r in range(2):
        round_engine.round()
        encounters_in_round = round_engine.encounter_log[r]
        for (mover, other), _ in encounters_in_round:
            total_encounters += 1
            enc = Encounter(
                mover,
                other,
                scoring_policy,
                interaction_policy,
                history_store=store,
                sample_id=0,
                round_num=r,
            )
            enc.process()

    # Cardinality ruling: 1 encounter -> exactly 2 directed rows
    assert len(store) == 2 * total_encounters

    # Verify each logged encounter generated both directed rows
    for r in range(2):
        for (mover, other), _ in round_engine.encounter_log[r]:
            m_view = [
                rec
                for rec in store.get_interactions(agent=mover, partner=other, sample_id=0)
                if rec.round_num == r
            ]
            o_view = [
                rec
                for rec in store.get_interactions(agent=other, partner=mover, sample_id=0)
                if rec.round_num == r
            ]
            assert len(m_view) >= 1
            assert len(o_view) >= 1


# ---- test 5: ticket req 4 — back-fill hook isolation ----


def test_backfill_hook_isolation() -> None:
    a = make_agent()
    a.current_prediction = 1
    a.certainty = 0.6
    b = make_agent()
    b.current_prediction = 0
    b.certainty = 0.8

    store = HistoryStore()
    enc = Encounter(
        a,
        b,
        CertaintyFlipScoringPolicy(),
        ReferenceInteractionPolicy(history_store=store),
        history_store=store,
        sample_id=1,
        round_num=0,
    )
    enc.process()

    records = store.get_interactions(sample_id=1)
    assert len(records) == 2
    for r in records:
        assert r.partner_correct is None
        assert r.ground_truth is None

    # Snapshot pre-backfill fields
    snapshot = [
        (
            r.sample_id,
            r.round_num,
            r.agent,
            r.partner,
            r.agent_prediction,
            r.partner_prediction,
            r.agreement,
            r.certainty_before,
            r.certainty_after,
            r.certainty_delta,
            r.prediction_flipped,
        )
        for r in records
    ]

    # Backfill with ground_truth = 1
    updated_count = store.backfill_correctness(sample_id=1, ground_truth=1)
    assert updated_count == 2

    # Verify ground_truth and correctness updated
    for r, orig in zip(records, snapshot, strict=False):
        assert r.ground_truth == 1
        assert r.partner_correct == (r.partner_prediction == 1)
        # Verify all other fields are unchanged
        current = (
            r.sample_id,
            r.round_num,
            r.agent,
            r.partner,
            r.agent_prediction,
            r.partner_prediction,
            r.agreement,
            r.certainty_before,
            r.certainty_after,
            r.certainty_delta,
            r.prediction_flipped,
        )
        assert current == orig


# ---- test 6: queryable tidy dataframe ----


def test_to_dataframe_schema() -> None:
    a = make_agent()
    a.current_prediction = 1
    b = make_agent()
    b.current_prediction = 0

    store = HistoryStore()
    enc = Encounter(
        a,
        b,
        CertaintyFlipScoringPolicy(),
        ReferenceInteractionPolicy(history_store=store),
        history_store=store,
        sample_id=42,
        round_num=3,
    )
    enc.process()
    store.backfill_correctness(sample_id=42, ground_truth=0)

    df = store.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2

    expected_columns = {
        "sample_id",
        "round",
        "agent",
        "partner",
        "agent_prediction",
        "partner_prediction",
        "agreement",
        "certainty_before",
        "certainty_after",
        "certainty_delta",
        "prediction_flipped",
        "partner_correct",
        "ground_truth",
    }
    assert expected_columns.issubset(set(df.columns))
    assert df["sample_id"].iloc[0] == 42
    assert df["round"].iloc[0] == 3


# ---- test 7: separation of prior_performance vs prior_accuracy ----


def test_separation_of_prior_performance_vs_prior_accuracy() -> None:
    a = make_agent()
    a.current_prediction = 1
    b = make_agent()
    b.current_prediction = 1
    b.trust_score = 0.50
    b.prior_performance = 1.2  # multiplier
    b.prior_accuracy = 0.6  # rate

    store = HistoryStore()
    store.record(
        HistoryRecord(
            sample_id=0,
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
            partner_correct=True,  # percCorrect = 1.0
            ground_truth=1,
        )
    )
    policy = ReferenceInteractionPolicy(history_store=store)
    policy.update_trust(a, b)

    # Correct formula: 0.05 * (1.0 * 1.2) * (+1) = 0.06 -> 0.56
    # Wrong formula (prior_accuracy): 0.05 * (1.0 * 0.6) * (+1) = 0.03 -> 0.53
    assert abs(b.trust_score - 0.56) < 1e-9


# ---- test 8: degenerate and defensive inputs ----


def test_degenerate_and_defensive_inputs() -> None:
    a = make_agent()  # current_prediction is None
    b = make_agent()
    b.current_prediction = 1

    store = HistoryStore()
    store.record(
        HistoryRecord(
            sample_id=0,
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
    policy = ReferenceInteractionPolicy(history_store=store)

    with pytest.raises(ValueError, match="uninitialized predictions"):
        policy.update_trust(a, b)

    # Unknown agent pair -> None
    c = make_agent()
    assert store.get_perc_correct(a, c) is None
