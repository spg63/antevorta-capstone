"""W0-02 test requirements — types, seams, stubs.

1. A trivial fake per seam passes `isinstance` (runtime_checkable); mypy strict covers
   the static half by type-checking the fakes against the Protocols.
2. Stub methods raise NotImplementedError naming the owning ticket.
3. `Prediction`: class_label outside {0,1} rejected; frozen; unknown keys rejected.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pytest
from pydantic import ValidationError

from wocbots.agents import Agent
from wocbots.arena import Arena
from wocbots.protocols import (
    Aggregator,
    InitPolicy,
    InteractionPolicy,
    MovementPolicy,
    ScoringPolicy,
)
from wocbots.types import Cell, Prediction

# ---- trivial fakes: one per seam (structural conformance, not behavior) ----
# Bodies are deliberately inert; W3/W4/W6 own real behavior. mypy strict checks these
# signatures against the Protocols — a drifting seam fails the type gate, not just runtime.


class FakeInit:
    def place(self, agent: Agent, arena: Arena, rng: np.random.Generator) -> Cell:
        return (0, 0)


class FakeMovement:
    def move(self, agent: Agent, arena: Arena, rng: np.random.Generator) -> Cell:
        return (0, 0)


class FakeInteraction:
    def should_interact(self, a: Agent, b: Agent) -> bool:
        return True

    def truth(self, a: Agent, b: Agent) -> bool:
        return True

    def update_trust(self, a: Agent, b: Agent) -> None:
        return None


class FakeScoring:
    def update_prediction(self, agent: Agent, partner_profile: Mapping[str, object]) -> None:
        return None


class FakeAggregator:
    def aggregate(self, participants: Sequence[Agent], rng: np.random.Generator) -> Prediction:
        return Prediction(class_label=0)


@pytest.mark.parametrize(
    ("fake", "protocol"),
    [
        (FakeInit(), InitPolicy),
        (FakeMovement(), MovementPolicy),
        (FakeInteraction(), InteractionPolicy),
        (FakeScoring(), ScoringPolicy),
        (FakeAggregator(), Aggregator),
    ],
)
def test_fake_satisfies_seam(fake: object, protocol: type) -> None:
    """W0-02 test 1 — each seam is runtime-checkable and structurally satisfiable."""
    assert isinstance(fake, protocol)


def test_agent_stub_names_owner() -> None:
    """W0-02 test 2 — the stub fails loud and says who owns the real thing."""
    with pytest.raises(NotImplementedError, match="W2-01 owns Agent"):
        Agent()


def test_arena_stub_names_owner() -> None:
    with pytest.raises(NotImplementedError, match="W3-01 owns Arena"):
        Arena()


def test_prediction_rejects_bad_label() -> None:
    """W0-02 test 3 — class_label is Literal[0, 1]; 2 is a validation ERROR."""
    with pytest.raises(ValidationError):
        Prediction(class_label=2)  # type: ignore[arg-type]


def test_prediction_frozen() -> None:
    p = Prediction(class_label=1)
    with pytest.raises(ValidationError):
        p.class_label = 0  # type: ignore[misc]


def test_prediction_rejects_unknown_keys() -> None:
    """O3 ruling: extra="forbid" — a typo'd field is an error, not a silent no-op."""
    with pytest.raises(ValidationError):
        Prediction(class_label=0, confidence_tier="High")  # type: ignore[call-arg]


def test_prediction_optional_fields_default_none() -> None:
    """tier/margin stay empty until W4-04/W6-02 fill them."""
    p = Prediction(class_label=0)
    assert p.tier is None
    assert p.margin is None
