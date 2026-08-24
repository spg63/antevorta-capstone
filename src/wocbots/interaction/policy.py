"""W3-03 — reference InteractionPolicy (spec §6.5): always-willing,
always-truthful. `update_trust` is an explicit no-op stub — W3-04 replaces
its body per that ticket's S2 ("Replaces W3-03's no-op stub"); the class
and its call sites do not change.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wocbots.agents import Agent


class ReferenceInteractionPolicy:
    def should_interact(self, a: Agent, b: Agent) -> bool:
        return True

    def truth(self, a: Agent, b: Agent) -> bool:
        return True

    def update_trust(self, a: Agent, b: Agent) -> None:
        """No-op stub (ticket S3). W3-04 owns the real §6.5 trust math."""
        return None
