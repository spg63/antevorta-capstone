from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from wocbots.types import Cell

if TYPE_CHECKING:
    from wocbots.agents import Agent
    from wocbots.arena import Arena


class RandomInitPolicy:
    """Arena placement at the start of a sample's interaction period (spec §6.2; W3-01).

    Reference implementation: uniformly random empty cell. Clustering / maximal-spread
    are documented open experiments — hence the seam.
    """

    def place(self, agent: Agent, arena: Arena, rng: np.random.Generator) -> Cell:
        while True:
            col = int(rng.integers(0, arena.cols))
            row = int(rng.integers(0, arena.rows))
            cell: Cell = (row, col)
            if arena.is_empty(cell):
                break
        arena.place(agent, cell)
        return cell
