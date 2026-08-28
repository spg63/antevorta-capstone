"""W4-01 × W3 — arena interaction in the lifecycle loop."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np

from wocbots.agents import Agent
from wocbots.arena import Arena, RandomInitPolicy, RandomMovementPolicy, RoundEngine
from wocbots.interaction import (
    CertaintyFlipScoringPolicy,
    Encounter,
    HistoryStore,
    ReferenceInteractionPolicy,
)


@dataclass
class ArenaRoundInteractionRunner:
    """Run W3-01 init + W3-02 rounds with W3-03/04 encounter processing per sample."""

    teleport_rate: float = 0.05
    sample_id: int | str = 0
    history_store: HistoryStore = field(default_factory=HistoryStore)
    last_rounds_completed: int = field(default=0, init=False)
    last_encounter_count: int = field(default=0, init=False)

    def run(self, participants: Sequence[Agent], *, rng: np.random.Generator) -> None:
        roster = list(participants)
        if len(roster) < 1:
            raise ValueError("arena interaction requires at least one participant")

        arena = Arena(len(roster))
        init_policy = RandomInitPolicy()
        for agent in roster:
            init_policy.place(agent, arena, rng)

        movement_policy = RandomMovementPolicy(teleport_rate=self.teleport_rate)
        engine = RoundEngine(roster, arena, movement_policy, rng)
        scoring_policy = CertaintyFlipScoringPolicy()
        interaction_policy = ReferenceInteractionPolicy(history_store=self.history_store)

        processed = 0
        while not engine.finished():
            engine.round()
            round_num = engine.rounds_completed - 1
            for mover, other in (pair for pair, _cell in engine.encounter_log[round_num]):
                Encounter(
                    mover,
                    other,
                    scoring_policy,
                    interaction_policy,
                    history_store=self.history_store,
                    sample_id=self.sample_id,
                    round_num=round_num,
                ).process()
                processed += 1

        self.last_rounds_completed = engine.rounds_completed
        self.last_encounter_count = processed
