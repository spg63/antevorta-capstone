from __future__ import annotations

import numpy as np

from wocbots.agents import HOLLYWOOD_WEIGHTS, Agent
from wocbots.arena import Arena, RandomInitPolicy


def make_agent() -> Agent:
    return Agent(
        features=("f0",),
        eval_accuracy=0.5,
        eval_precision=0.5,
        eval_recall=0.5,
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )


def test_random_init_places_all_agents_in_separate_cells() -> None:
    # arrange
    n = 10
    agents = [make_agent() for _ in range(n)]
    arena = Arena(n)
    rand_policy = RandomInitPolicy()
    rng = np.random.default_rng(42)

    # act
    for i in range(n):
        rand_policy.place(agents[i], arena, rng)

    # assert
    for i in range(arena.rows):
        for j in range(arena.cols):
            cell = (i, j)
            if not arena.is_empty(cell):
                assert not arena.is_full(cell)


def test_random_init_places_all_agents_within_arena() -> None:
    # arrange
    n = 10
    agents = [make_agent() for _ in range(n)]
    arena = Arena(n)
    rand_policy = RandomInitPolicy()
    rng = np.random.default_rng(42)
    positions = []

    # act
    for i in range(n):
        cell = rand_policy.place(agents[i], arena, rng)
        positions.append(cell)

    # assert
    for row, col in positions:
        assert row >= 0
        assert row < arena.rows
        assert col >= 0
        assert col < arena.cols


def test_random_init_deterministic_with_seed() -> None:
    # arrange
    n = 10
    agents1 = [make_agent() for _ in range(n)]
    agents2 = [make_agent() for _ in range(n)]
    arena1 = Arena(n)
    arena2 = Arena(n)
    rand_policy = RandomInitPolicy()
    rng1 = np.random.default_rng(42)
    rng2 = np.random.default_rng(42)
    positions1 = []
    positions2 = []

    # act
    for i in range(n):
        cell1 = rand_policy.place(agents1[i], arena1, rng1)
        positions1.append(cell1)

        cell2 = rand_policy.place(agents2[i], arena2, rng2)
        positions2.append(cell2)

    # assert
    for i in range(len(positions1)):
        row1, col1 = positions1[i]
        row2, col2 = positions2[i]
        assert row1 == row2
        assert col1 == col2
