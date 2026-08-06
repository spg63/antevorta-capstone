from collections import defaultdict

import numpy as np

from wocbots.agents import Agent
from wocbots.arena import Arena
from wocbots.protocols import MovementPolicy
from wocbots.types import Cell


class RoundEngine:
    def __init__(
        self,
        agents: list[Agent],
        arena: Arena,
        movement_policy: MovementPolicy,
        rng: np.random.Generator,
    ) -> None:
        n: int = len(agents)
        self._agents: list[Agent] = agents
        self._agent_indices: list[int] = list(range(n))
        self._cur_round: int = 0
        self._max_rounds: int = max(10, round(0.1 * n))
        self._arena: Arena = arena
        self._movement_policy: MovementPolicy = movement_policy
        self._rng: np.random.Generator = rng
        self._encounter_log: dict[int, list[tuple[tuple[Agent, Agent], Cell]]] = defaultdict(list)

    def round(self) -> None:
        if self._cur_round >= self._max_rounds:
            raise RuntimeError(f"max number of rounds reached: {self._max_rounds}")
        self._rng.shuffle(self._agent_indices)
        for i in self._agent_indices:
            cell = self._movement_policy.move(self._agents[i], self._arena, self._rng)
            occupants = self._arena.agents_at(cell)
            if len(occupants) == 2:
                other = occupants[0] if occupants[1] == self._agents[i] else occupants[1]
                self._encounter_log[self._cur_round].append(((self._agents[i], other), cell))
        self._cur_round += 1

    def finished(self) -> bool:
        return self._cur_round >= self._max_rounds

    @property
    def encounter_log(self) -> dict[int, list[tuple[tuple[Agent, Agent], Cell]]]:
        return self._encounter_log
