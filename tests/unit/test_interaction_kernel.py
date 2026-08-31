"""W3-03 test plan (plan §10, exact pins) — the certainty/flip kernel.

Maps to the plan's §10 test list: 5 ticket-mandatory tests (1-5) + 3 tests
added beyond the ticket for discipline (6-8). Test numbers/labels below
mirror the plan exactly so a reviewer can match each function back to its
§10 entry.

Local-helper convention (no shared conftest exists in this repo — plan §10):
a module-level `make_agent(...)` mirroring `test_w2_01_agent_state.py`'s,
plus a `make_partner_profile(...)` builder for a bare `Mapping[str, object]`
that isolates the math from `public_profile()`/`Encounter` plumbing.
"""

from __future__ import annotations

import pytest

from wocbots.agents import HOLLYWOOD_WEIGHTS, Agent
from wocbots.interaction import CertaintyFlipScoringPolicy, Encounter, ReferenceInteractionPolicy

# ---- shared helpers ----


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


def make_partner_profile(
    *,
    current_prediction: object = 0,
    certainty: object = 0.5,
    confidence: object = 0.5,
    trust_score: object = 0.5,
    prior_performance: object = 1.0,
    features: object = (),
) -> dict[str, object]:
    """A bare Mapping[str, object], not a real Agent's public_profile().

    Defaults are all individually valid so a test overriding a single field
    to a degenerate value isolates exactly that field's validation.
    """
    return {
        "current_prediction": current_prediction,
        "certainty": certainty,
        "confidence": confidence,
        "trust_score": trust_score,
        "prior_performance": prior_performance,
        "features": features,
    }


# ---- test 1: ticket-mandatory — the §6.5 worked-example pin (exact, 1e-9) ----


def test_worked_example_pin() -> None:
    a = make_agent()
    a.certainty = 0.62
    a.current_prediction = 1

    b_profile = make_partner_profile(
        current_prediction=0,
        certainty=0.80,
        confidence=0.71,
        trust_score=0.78,
        prior_performance=1.1,
    )

    CertaintyFlipScoringPolicy().update_prediction(a, b_profile)

    # Read into a widened local: mypy strict keeps the pre-call `Literal[1]` narrowing
    # on `a.current_prediction` across the update_prediction() call (it has no visibility
    # into the mutation), so comparing the narrowed attribute directly against `0` is
    # flagged as a non-overlapping literal comparison even though it's correct at runtime.
    final_prediction: int | None = a.current_prediction
    assert final_prediction == 0
    assert abs(a.certainty - 0.56519072) < 1e-9


# ---- test 2: ticket-mandatory — agreement mirror (exact, 1e-9) ----


def test_agreement_mirror_no_flip() -> None:
    a = make_agent()
    a.certainty = 0.62
    a.current_prediction = 1

    b_profile = make_partner_profile(
        current_prediction=1,  # agrees with a, unlike test 1
        certainty=0.80,
        confidence=0.71,
        trust_score=0.78,
        prior_performance=1.1,
    )

    CertaintyFlipScoringPolicy().update_prediction(a, b_profile)

    assert a.current_prediction == 1  # unchanged
    assert abs(a.certainty - 0.80519072) < 1e-9


# ---- test 3: ticket-mandatory — flip boundary, both sides (exact, 1e-9) ----


def test_flip_boundary_3a_flips() -> None:
    """Pre-clamp certainty = 0.6 - (0.4 * 1.0 * (1.0 * 0.2525) * 1.0) = 0.499 < 0.50 -> flips."""
    a = make_agent()
    a.certainty = 0.6
    a.current_prediction = 1

    b_profile = make_partner_profile(
        current_prediction=0,  # disagrees
        certainty=0.2525,
        confidence=1.0,
        trust_score=1.0,
        prior_performance=1.0,
    )

    CertaintyFlipScoringPolicy().update_prediction(a, b_profile)

    # See test_worked_example_pin's comment: widened local sidesteps mypy strict's
    # stale pre-call literal narrowing on the attribute.
    final_prediction: int | None = a.current_prediction
    assert final_prediction == 0
    assert abs(a.certainty - 0.501) < 1e-9


def test_flip_boundary_3b_no_flip() -> None:
    """Pre-clamp certainty = 0.6 - (0.4 * 1.0 * (1.0 * 0.2475) * 1.0) = 0.501, not < 0.50 -> no flip."""
    a = make_agent()
    a.certainty = 0.6
    a.current_prediction = 1

    b_profile = make_partner_profile(
        current_prediction=0,  # disagrees
        certainty=0.2475,
        confidence=1.0,
        trust_score=1.0,
        prior_performance=1.0,
    )

    CertaintyFlipScoringPolicy().update_prediction(a, b_profile)

    assert a.current_prediction == 1  # unchanged
    assert abs(a.certainty - 0.501) < 1e-9


# ---- test 4: ticket-mandatory — clamp saturation (ten consecutive agreements) ----


def test_clamp_saturation_ten_agreements() -> None:
    a = make_agent()
    a.certainty = 0.62
    a.current_prediction = 1

    b_profile = make_partner_profile(
        current_prediction=1,  # agrees every time
        certainty=0.99,
        confidence=1.0,
        trust_score=1.0,
        prior_performance=1.3,  # spec §2 table's upper bound
    )

    scoring_policy = CertaintyFlipScoringPolicy()
    for _ in range(10):
        scoring_policy.update_prediction(a, b_profile)
        # acceptance (1 - certainty) must never reach 0, checked every iteration,
        # not just at the end.
        assert 1.0 - a.certainty >= 0.01

    # clamp is an exact min(), no floating drift possible.
    assert a.certainty == 0.99


# ---- test 5: ticket-mandatory — symmetry under swapped processing order (byte-identical) ----


def _build_symmetry_pair() -> tuple[Agent, Agent]:
    """Fresh (a, b) Agents reusing test 1's worked-example numbers.

    Full Agents, not profile stubs, since this test exercises Encounter.process(),
    not update_prediction directly. eval metrics for `b` are chosen so its derived
    certainty/trust_score/confidence land exactly on test 1's b_profile values
    ((0.82+0.78)/2 = 0.80 certainty, eval_precision 0.78 = trust_score,
    0.3*0.82 + 0.5*0.78 + 0.2*0.37 = 0.71 confidence).
    """
    a = make_agent(acc=0.5, prec=0.55, rec=0.5)
    a.certainty = 0.62
    a.current_prediction = 1

    b = make_agent(acc=0.82, prec=0.78, rec=0.37)
    b.prior_performance = 1.1
    b.current_prediction = 0

    return a, b


def test_symmetry_under_swapped_processing_order() -> None:
    a1, b1 = _build_symmetry_pair()
    a2, b2 = _build_symmetry_pair()

    # Run A: natural order.
    Encounter(a1, b1, CertaintyFlipScoringPolicy(), ReferenceInteractionPolicy()).process()
    # Run B: constructor argument order swapped — this is exactly "swap the two
    # update_prediction call sites", since Encounter's constructor argument order
    # only determines label order; both snapshots are always captured, inside
    # process(), before either mutation.
    Encounter(b2, a2, CertaintyFlipScoringPolicy(), ReferenceInteractionPolicy()).process()

    assert (a1.certainty, a1.current_prediction, b1.certainty, b1.current_prediction) == (
        a2.certainty,
        a2.current_prediction,
        b2.certainty,
        b2.current_prediction,
    )


# ---- test 6: added, beyond the ticket — degenerate input, agent side (preamble §4-(c)) ----


def test_agent_with_no_prediction_raises_value_error() -> None:
    a = make_agent()  # current_prediction is None, the construction-time default
    assert a.current_prediction is None

    valid_profile = make_partner_profile()

    with pytest.raises(ValueError):
        CertaintyFlipScoringPolicy().update_prediction(a, valid_profile)


# ---- test 7: added, beyond the ticket — degenerate input, partner-profile side ----


def test_partner_profile_bad_prediction_raises_value_error_naming_key() -> None:
    a = make_agent()
    a.certainty = 0.5
    a.current_prediction = 1

    bad_profile = make_partner_profile(current_prediction=2)  # stray value, not 0/1

    with pytest.raises(ValueError, match="current_prediction"):
        CertaintyFlipScoringPolicy().update_prediction(a, bad_profile)


def test_partner_profile_non_numeric_certainty_raises_type_error_naming_key() -> None:
    a = make_agent()
    a.certainty = 0.5
    a.current_prediction = 1

    bad_profile = make_partner_profile(current_prediction=0, certainty="not-a-number")

    with pytest.raises(TypeError, match="certainty"):
        CertaintyFlipScoringPolicy().update_prediction(a, bad_profile)


# ---- test 8: added, beyond the ticket — ReferenceInteractionPolicy reference behavior ----


def test_reference_interaction_policy_behavior() -> None:
    a = make_agent()
    b = make_agent()
    policy = ReferenceInteractionPolicy()

    assert policy.should_interact(a, b) is True
    assert policy.truth(a, b) is True

    a_trust_before, b_trust_before = a.trust_score, b.trust_score
    # mypy strict's func-returns-value check refuses to let a `-> None`-typed call's
    # result be captured at all, even just to assert it — the single narrow ignore
    # below is the only way to write the plan's §10 test-8 assertion ("returns None")
    # as an actual runtime check rather than relying solely on the static signature.
    result = policy.update_trust(a, b)  # type: ignore[func-returns-value]

    assert result is None
    assert a.trust_score == a_trust_before
    assert b.trust_score == b_trust_before
