"""W3-03 / W3-04 — Atomic per-encounter processor (plan §3 D4).

Consumes one encounter pair (a, b), executes compute-then-apply prediction updates,
evaluates trust updates, and records directed history rows in HistoryStore.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

from wocbots.interaction.history import HistoryRecord

if TYPE_CHECKING:
    from wocbots.agents import Agent
    from wocbots.interaction.history import HistoryStore
    from wocbots.protocols import InteractionPolicy, ScoringPolicy


class Encounter:
    def __init__(
        self,
        a: Agent,
        b: Agent,
        scoring_policy: ScoringPolicy,
        interaction_policy: InteractionPolicy,
        *,
        history_store: HistoryStore | None = None,
        sample_id: int | str = 0,
        round_num: int = 0,
    ) -> None:
        self._a = a
        self._b = b
        self._scoring_policy = scoring_policy
        self._interaction_policy = interaction_policy
        self._history_store = history_store
        self._sample_id = sample_id
        self._round_num = round_num

    def process(self) -> None:
        """Both directions, compute-then-apply (spec §6.5 symmetry ruling)."""
        profile_a = self._a.public_profile()
        profile_b = self._b.public_profile()

        pred_a_before = cast(Literal[0, 1], profile_a["current_prediction"])
        pred_b_before = cast(Literal[0, 1], profile_b["current_prediction"])
        cert_a_before = cast(float, profile_a["certainty"])
        cert_b_before = cast(float, profile_b["certainty"])

        # 1. Update trust, BEFORE scoring. §6.5's doAgree is an encounter-time fact and
        #    step 2 may flip a prediction; reading trust off post-flip predictions inverts
        #    doAgree's sign. Scoring is unaffected by the order because it reads the profile
        #    snapshots taken above, never live partner state. Do not reorder.
        self._interaction_policy.update_trust(self._a, self._b)
        self._interaction_policy.update_trust(self._b, self._a)

        # 2. Update predictions (compute-then-apply)
        self._scoring_policy.update_prediction(self._a, profile_b)
        self._scoring_policy.update_prediction(self._b, profile_a)

        # 3. Record directed history in HistoryStore if present
        if self._history_store is not None:
            pred_a_after = self._a.current_prediction
            pred_b_after = self._b.current_prediction
            cert_a_after = self._a.certainty
            cert_b_after = self._b.certainty

            rec_a = HistoryRecord(
                sample_id=self._sample_id,
                round_num=self._round_num,
                agent=self._a,
                partner=self._b,
                agent_prediction=pred_a_before,
                partner_prediction=pred_b_before,
                agreement=(pred_a_before == pred_b_before),
                certainty_before=cert_a_before,
                certainty_after=cert_a_after,
                certainty_delta=cert_a_after - cert_a_before,
                prediction_flipped=(pred_a_before != pred_a_after),
            )
            rec_b = HistoryRecord(
                sample_id=self._sample_id,
                round_num=self._round_num,
                agent=self._b,
                partner=self._a,
                agent_prediction=pred_b_before,
                partner_prediction=pred_a_before,
                agreement=(pred_b_before == pred_a_before),
                certainty_before=cert_b_before,
                certainty_after=cert_b_after,
                certainty_delta=cert_b_after - cert_b_before,
                prediction_flipped=(pred_b_before != pred_b_after),
            )
            self._history_store.record(rec_a)
            self._history_store.record(rec_b)
