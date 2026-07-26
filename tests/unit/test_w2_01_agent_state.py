"""W2-01 test requirements — agent state, init pins, the profile boundary.

Maps to the approved mini-plan §5 (tests 1–11) and the ticket's three requirements:
init pins exact at 1e-12; profile immutable with exactly the six §6.5 fields; mypy
strict on the tightened seam types (suite-level gate, not a test body here).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from wocbots.agents import HOLLYWOOD_WEIGHTS, Agent, ConfidenceWeights

# The exact §6.5 surface (mini-plan Q1: spec wins over the ticket's "prediction").
PROFILE_FIELDS = {
    "current_prediction",
    "certainty",
    "confidence",
    "trust_score",
    "prior_performance",
    "features",
}


def make_agent(
    acc: float = 0.8,
    prec: float = 0.7,
    rec: float = 0.6,
    features: tuple[str, ...] = ("budget", "vote_count"),
) -> Agent:
    return Agent(
        features=features,
        eval_accuracy=acc,
        eval_precision=prec,
        eval_recall=rec,
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )


# ---- test 1: the ticket pin (exact, 1e-12) ----


def test_init_pins_ticket_case() -> None:
    """Ticket test req 1: metrics (0.8, 0.7, 0.6) + Hollywood weights."""
    agent = make_agent(0.8, 0.7, 0.6)
    assert abs(agent.certainty - 0.75) < 1e-12
    assert abs(agent.trust_score - 0.7) < 1e-12
    assert abs(agent.confidence - 0.71) < 1e-12
    assert agent.prior_performance == 1.0
    assert agent.prior_accuracy == 0.8
    assert agent.current_prediction is None


# ---- test 2: second hand-computed case (recomputed, not pinned as rounded literals) ----


def test_init_second_case_recomputed() -> None:
    """Guards against hard-coding pin 1 (v1.2 lesson: never pin rounded intermediates)."""
    acc, prec, rec = 0.62, 0.71, 0.58
    agent = make_agent(acc, prec, rec)
    assert agent.certainty == (acc + prec) / 2
    assert agent.trust_score == prec
    assert agent.confidence == 0.3 * acc + 0.5 * prec + 0.2 * rec
    assert agent.prior_performance == 1.0
    assert agent.prior_accuracy == acc


# ---- test 3: weights validation, both sides ----


def test_weights_sum_rejected_both_sides() -> None:
    with pytest.raises(ValidationError):
        ConfidenceWeights(w_acc=0.3, w_prec=0.5, w_rec=0.19999)
    with pytest.raises(ValidationError):
        ConfidenceWeights(w_acc=0.3, w_prec=0.5, w_rec=0.20001)
    ConfidenceWeights(w_acc=0.3, w_prec=0.5, w_rec=0.2)  # exact 1.0 accepted


def test_weights_negative_rejected() -> None:
    with pytest.raises(ValidationError):
        ConfidenceWeights(w_acc=-0.1, w_prec=0.6, w_rec=0.5)


def test_weights_frozen_and_extra_forbidden() -> None:
    with pytest.raises(ValidationError):
        HOLLYWOOD_WEIGHTS.w_acc = 0.4  # type: ignore[misc]
    with pytest.raises(ValidationError):
        ConfidenceWeights(w_acc=0.3, w_prec=0.5, w_rec=0.2, w_f1=0.0)  # type: ignore[call-arg]


# ---- test 4: eval-metric bounds, both sides ----


@pytest.mark.parametrize("bad", [-0.01, 1.01])
def test_eval_metric_out_of_bounds_raises(bad: float) -> None:
    for kwarg in ("eval_accuracy", "eval_precision", "eval_recall"):
        kwargs = {"eval_accuracy": 0.8, "eval_precision": 0.7, "eval_recall": 0.6, kwarg: bad}
        with pytest.raises(ValueError, match=kwarg):
            Agent(features=("budget",), confidence_weights=HOLLYWOOD_WEIGHTS, **kwargs)


def test_eval_metric_bounds_inclusive() -> None:
    agent = make_agent(0.0, 1.0, 0.0)
    assert agent.certainty == 0.5
    agent = make_agent(1.0, 1.0, 1.0)
    assert abs(agent.confidence - 1.0) < 1e-12


# ---- tests 5–8: the §6.5 profile boundary ----


def test_profile_exactly_six_fields() -> None:
    assert set(make_agent().public_profile().keys()) == PROFILE_FIELDS


def test_profile_immutable_and_features_tuple() -> None:
    profile = make_agent().public_profile()
    with pytest.raises(TypeError):
        profile["certainty"] = 1.0  # type: ignore[index]
    with pytest.raises(TypeError):
        del profile["certainty"]  # type: ignore[attr-defined]
    assert isinstance(profile["features"], tuple)


def test_profile_privacy_boundary() -> None:
    """No classifier / data / history / eval metrics / prior_accuracy (W8-03 audit)."""
    profile = make_agent().public_profile()
    for private in (
        "classifier",
        "data",
        "history",
        "eval_accuracy",
        "eval_precision",
        "eval_recall",
        "prior_accuracy",
    ):
        assert private not in profile


def test_profile_snapshot_freshness() -> None:
    """Snapshot-per-call: a later mutation (simulating W3-03) shows in a new snapshot."""
    agent = make_agent()
    stale = agent.public_profile()
    agent.certainty = 0.9
    agent.current_prediction = 1
    fresh = agent.public_profile()
    assert fresh["certainty"] == 0.9
    assert fresh["current_prediction"] == 1
    assert stale["certainty"] == 0.75  # the old snapshot does not mutate


# ---- test 9: the §6.6 reset split ----


def test_reset_certainty_restores_training_value_only() -> None:
    agent = make_agent(0.8, 0.7, 0.6)
    agent.certainty = 0.2
    agent.trust_score = 0.55
    agent.prior_performance = 1.1
    agent.prior_accuracy = 0.66
    agent.reset_certainty()
    assert agent.certainty == 0.75  # back to training-time value
    assert agent.trust_score == 0.55  # long-term social memory persists
    assert agent.prior_performance == 1.1
    assert agent.prior_accuracy == 0.66


# ---- test 10: degenerate input ----


def test_empty_features_rejected() -> None:
    with pytest.raises(ValueError, match="feature"):
        make_agent(features=())


# ---- test 11: seam compatibility ----


def test_seam_import_path_unchanged() -> None:
    """The W0-02 TYPE_CHECKING import path still resolves to this Agent."""
    from wocbots.agents import Agent as SeamAgent

    assert SeamAgent is Agent
    assert make_agent().features == ("budget", "vote_count")
