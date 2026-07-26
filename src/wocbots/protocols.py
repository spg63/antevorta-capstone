"""W0-02 §7-S2 — the five policy seams (spec §11: policies are seams).

These interfaces exist BEFORE the things they connect so W2/W3/W4/W6 grow into them
instead of getting refactored apart later. Reference implementations are configs, not
hard-coding. Later tickets may TIGHTEN types behind a seam; renaming or loosening a seam
is a cross-ticket contract change routed through the index.

The TYPE_CHECKING forward references (W0-02 plan D1) break the wocbots.agents/arena ↔
protocols import cycle: at runtime these names are never imported here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import numpy as np

from wocbots.types import Cell, Prediction

if TYPE_CHECKING:
    from wocbots.agents import Agent
    from wocbots.arena import Arena


@runtime_checkable
class InitPolicy(Protocol):
    """Arena placement at the start of a sample's interaction period (spec §6.2; W3-01).

    Reference implementation: uniformly random empty cell. Clustering / maximal-spread
    are documented open experiments — hence the seam.
    """

    def place(self, agent: Agent, arena: Arena, rng: np.random.Generator) -> Cell: ...


@runtime_checkable
class MovementPolicy(Protocol):
    """Per-round movement (spec §6.3; W3-02): random cardinal step, anti-clique, stirring."""

    def move(self, agent: Agent, arena: Arena, rng: np.random.Generator) -> Cell: ...


@runtime_checkable
class InteractionPolicy(Protocol):
    """Willingness, truthfulness, and trust updates (spec §6.5; W3-04).

    Reference implementation: always-willing, always-truthful, trust update per §6.5.
    Deceptive/selective agents are a documented future experiment behind this seam.
    """

    def should_interact(self, a: Agent, b: Agent) -> bool: ...

    def truth(self, a: Agent, b: Agent) -> bool: ...

    def update_trust(self, a: Agent, b: Agent) -> None: ...


@runtime_checkable
class ScoringPolicy(Protocol):
    """The certainty/flip kernel (spec §6.5; W3-03).

    `partner_profile` is a read-only Mapping — the §6.5 public-profile privacy boundary.
    Typing it as `Agent` is the exact hole the boundary closes (W8's meta-swarm audit
    leans on this): a scoring policy sees what a partner PUBLISHES, never the partner.
    """

    def update_prediction(self, agent: Agent, partner_profile: Mapping[str, object]) -> None: ...


@runtime_checkable
class Aggregator(Protocol):
    """Collective prediction from the participant set (spec §7 voting / §8 swarm; W4-03/W6-02)."""

    def aggregate(self, participants: Sequence[Agent], rng: np.random.Generator) -> Prediction: ...
