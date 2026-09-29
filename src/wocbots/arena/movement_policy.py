from __future__ import annotations

from collections import defaultdict, deque

import numpy as np

from wocbots.agents import Agent
from wocbots.arena import Arena
from wocbots.types import Cell


class RandomMovementPolicy:
    def __init__(self, teleport_rate: float = 0.05) -> None:
        self._moves: list[tuple[int, int]] = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        self._teleport_rate: float = teleport_rate
        self._cur_round = 0
        self._moved_this_round: set[Agent] = set()
        self._pair_history: dict[frozenset[Agent], deque[int]] = defaultdict(deque)

    def move(self, agent: Agent, arena: Arena, rng: np.random.Generator) -> Cell:
        if agent in self._moved_this_round:
            self._cur_round += 1
            self._moved_this_round = set()
        self._moved_this_round.add(agent)

        cur_cell = arena.cell(agent)
        if rng.random() < self._teleport_rate:
            while True:
                col = int(rng.integers(0, arena.cols))
                row = int(rng.integers(0, arena.rows))
                cell: Cell = (row, col)
                if cur_cell != cell and self._can_move_to(agent, arena, cell):
                    break
            agents = arena.agents_at(cell)
            if agents:
                other_agent = arena.agents_at(cell)[0]
                self._encounter(agent, other_agent)
            arena.move_to(agent, cell)
            return cell

        if not self._has_moves(agent, arena):
            while True:
                col = int(rng.integers(0, arena.cols))
                row = int(rng.integers(0, arena.rows))
                cell = (row, col)
                if arena.is_empty(cell):
                    break
            arena.move_to(agent, cell)
            return cell

        while True:
            i = int(rng.integers(0, len(self._moves)))
            dir = self._moves[i]
            next_cell = (cur_cell[0] + dir[0], cur_cell[1] + dir[1])
            if self._can_move_to(agent, arena, next_cell):
                break

        agents = arena.agents_at(next_cell)
        if agents:
            other_agent = agents[0]
            self._encounter(agent, other_agent)
        arena.move_to(agent, next_cell)
        return next_cell

    def _can_move_to(self, agent: Agent, arena: Arena, cell: Cell) -> bool:
        row, col = cell
        if row < 0 or row >= arena.rows or col < 0 or col >= arena.cols:
            return False
        if arena.is_empty(cell):
            return True
        if not arena.is_full(cell):
            other_agent = arena.agents_at(cell)[0]
            if self._can_encounter(agent, other_agent):
                return True
        return False

    def _has_moves(self, agent: Agent, arena: Arena) -> bool:
        cur_cell = arena.cell(agent)
        for dir in self._moves:
            next_cell = (cur_cell[0] + dir[0], cur_cell[1] + dir[1])
            if self._can_move_to(agent, arena, next_cell):
                return True
        return False

    def _can_encounter(self, a: Agent, b: Agent) -> bool:
        key = frozenset((a, b))
        if len(self._pair_history[key]) > 0 and self._pair_history[key][-1] == self._cur_round - 1:
            return False
        count = 0
        for round in self._pair_history[key]:
            if round > self._cur_round - 5:
                count += 1
        return not count >= 2

    def _encounter(self, a: Agent, b: Agent) -> None:
        key = frozenset((a, b))
        self._pair_history[key].append(self._cur_round)

        if (len(self._pair_history[key]) >= 2) and (
            self._pair_history[key][-1] - self._pair_history[key][0] >= 5
        ):
            self._pair_history[key].popleft()
