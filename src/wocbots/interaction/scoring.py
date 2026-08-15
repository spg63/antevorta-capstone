"""W3-03 — the certainty/flip kernel (spec §6.5, receiving side).

Implements the ScoringPolicy seam (protocols.py). Every equation under its
spec name (acceptance, influence, corrected), pinned by the worked example
in the ticket and re-derived independently in the plan (§4).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, cast

from wocbots.agents import Agent
from wocbots.interaction._util import clamp


class CertaintyFlipScoringPolicy:
    """Reference ScoringPolicy: spec §6.5's receiving-side equations, exact.

    Consumes a read-only partner_profile (the §6.5 privacy boundary) — never
    reaches into the partner Agent. Trust is untouched here (W3-04's seam).
    """

    CERTAINTY_LO = 0.01
    CERTAINTY_HI = 0.99
    FLIP_THRESHOLD = 0.50

    def update_prediction(self, agent: Agent, partner_profile: Mapping[str, object]) -> None:
        if agent.current_prediction is None:
            raise ValueError(
                "update_prediction called on an agent with no current_prediction "
                "set — an arena-round invariant violation (spec §3 Phase 2 must "
                "run first)"
            )

        b_prediction = self._require_prediction(partner_profile, "current_prediction")
        b_certainty = self._require_float(partner_profile, "certainty")
        b_confidence = self._require_float(partner_profile, "confidence")
        b_trust_score = self._require_float(partner_profile, "trust_score")
        b_prior_performance = self._require_float(partner_profile, "prior_performance")

        acceptance = 1.0 - agent.certainty
        influence = b_confidence * acceptance * (b_trust_score * b_certainty)
        corrected = influence * b_prior_performance
        if agent.current_prediction != b_prediction:
            corrected = -corrected

        new_certainty = clamp(agent.certainty + corrected, self.CERTAINTY_LO, self.CERTAINTY_HI)
        if new_certainty < self.FLIP_THRESHOLD:
            agent.current_prediction = cast(Literal[0, 1], 1 - agent.current_prediction)
            new_certainty = 1.0 - new_certainty
        agent.certainty = new_certainty

    def _require_float(self, profile: Mapping[str, object], key: str) -> float:
        value = profile[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"public_profile()[{key!r}] must be a float, got {type(value).__name__}")
        return float(value)

    def _require_prediction(self, profile: Mapping[str, object], key: str) -> Literal[0, 1]:
        value = profile[key]
        if value not in (0, 1):
            raise ValueError(
                f"public_profile()[{key!r}] must be 0 or 1 for an interaction "
                f"partner (never None — partner must have inferred already), "
                f"got {value!r}"
            )
        return value
