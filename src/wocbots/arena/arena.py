from __future__ import annotations

from math import ceil, floor, sqrt
from typing import TYPE_CHECKING

from wocbots.types import Cell

if TYPE_CHECKING:
    from wocbots.agents import Agent


class CellFullError(RuntimeError):
    """Raised when placement is attempted on an already full cell."""


class _GridCell:
    """Private per-cell occupancy bookkeeping. Never exposed outside Arena"""

    def __init__(self) -> None:
        self._agents: list[Agent] = []

    def place(self, agent: Agent) -> None:
        if len(self._agents) >= 2:
            raise CellFullError("cell already holds 2 agents.")
        self._agents.append(agent)

    def empty(self) -> bool:
        return not self._agents

    def full(self) -> bool:
        return len(self._agents) == 2

    def remove(self, agent: Agent) -> None:
        self._agents.remove(agent)

    @property
    def agents(self) -> list[Agent]:
        return self._agents


class Arena:
    def __init__(self, n_participants: int) -> None:
        if n_participants < 1:
            raise ValueError(f"arena requires at least 1 participants, got {n_participants}")
        self._rows: int = floor(sqrt(2 * n_participants))
        self._cols: int = ceil(2 * n_participants / self._rows)
        self._grid: list[_GridCell] = [_GridCell() for _ in range(self._rows * self._cols)]
        self._agents_cell: dict[Agent, Cell] = {}

    def _index(self, cell: Cell) -> int:
        row, col = cell
        return row * self._cols + col

    def is_empty(self, cell: Cell) -> bool:
        return self._grid[self._index(cell)].empty()

    def is_full(self, cell: Cell) -> bool:
        return self._grid[self._index(cell)].full()

    def place(self, agent: Agent, cell: Cell) -> None:
        self._grid[self._index(cell)].place(agent)
        self._agents_cell[agent] = cell

    def move_to(self, agent: Agent, cell: Cell) -> None:
        if self.is_full(cell):
            raise ValueError(f"arena at cell {cell} already has two agents")
        cur_cell = self._agents_cell[agent]
        self._grid[self._index(cur_cell)].remove(agent)
        self._grid[self._index(cell)].place(agent)
        self._agents_cell[agent] = cell

    def cell(self, agent: Agent) -> Cell:
        return self._agents_cell[agent]

    def agents_at(self, cell: Cell) -> list[Agent]:
        return self._grid[self._index(cell)].agents

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols
