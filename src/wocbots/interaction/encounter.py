"""W3-03 — the atomic per-encounter processor (plan §3 D1).

Consumes ONE entry of the shape RoundEngine.encounter_log[round] produces:
an (Agent, Agent) pair. Does not iterate the log itself — that's W4-01's
per-sample loop (plan §3 D1 names the ownership boundary explicitly).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wocbots.agents import Agent
    from wocbots.protocols import InteractionPolicy, ScoringPolicy


class Encounter:
    def __init__(
        self, a: Agent, b: Agent, scoring_policy: ScoringPolicy, interaction_policy: InteractionPolicy
    ):
        self._a = a
        self._b = b
        self._scoring_policy = scoring_policy
        self._interaction_policy = interaction_policy

    def process(self) -> None:
        """Both directions, compute-then-apply (spec §6.5 symmetry ruling).

        Both profiles are snapshotted before either update_prediction call, so
        the two update_prediction calls below may run in either order with
        byte-identical results (pinned by test 5, plan §10).
        """
        profile_a = self._a.public_profile()
        profile_b = self._b.public_profile()

        self._scoring_policy.update_prediction(self._a, profile_b)
        self._scoring_policy.update_prediction(self._b, profile_a)

        self._interaction_policy.update_trust(self._a, self._b)
        self._interaction_policy.update_trust(self._b, self._a)
