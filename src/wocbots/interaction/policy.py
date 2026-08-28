"""W3-03 / W3-04 — Reference InteractionPolicy (spec §6.5).

Implements the InteractionPolicy seam: always-willing, always-truthful,
and the spec §6.5 trust update math backed by HistoryStore.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from wocbots.agents import Agent
from wocbots.interaction._util import clamp

if TYPE_CHECKING:
    from wocbots.agents import Agent
    from wocbots.interaction.history import HistoryStore


class ReferenceInteractionPolicy:
    """Reference InteractionPolicy: always-willing, always-truthful, §6.5 trust updates."""

    def __init__(self, history_store: HistoryStore | None = None) -> None:
        self._history_store = history_store

    def should_interact(self, a: Agent, b: Agent) -> bool:
        return True

    def truth(self, a: Agent, b: Agent) -> bool:
        return True

    def update_trust(
        self,
        a: Agent,
        b: Agent,
        *,
        a_prediction: int | None = None,
        b_prediction: int | None = None,
    ) -> None:
        """Update b's trust score from a's perspective per spec §6.5.

        b_trust += 0.05 * (b_percCorrect * b_priorPerf) * doAgree
        NO update if a has no prior scored history with b.
        Clamped to [0.0, 1.0].
        """
        if self._history_store is None:
            return

        perc_correct = self._history_store.get_perc_correct(a, b)
        if perc_correct is None:
            # Spec §6.5: NO update if a has no prior history with b
            return

        # Encounter-time predictions (fall back to current_prediction if not explicitly supplied)
        pred_a = a.current_prediction if a_prediction is None else a_prediction
        pred_b = b.current_prediction if b_prediction is None else b_prediction

        if pred_a is None or pred_b is None:
            raise ValueError("update_trust called on agents with uninitialized predictions")

        do_agree = 1 if pred_a == pred_b else -1
        delta = 0.05 * (perc_correct * b.prior_performance) * do_agree
        b.trust_score = clamp(b.trust_score + delta, 0.0, 1.0)
