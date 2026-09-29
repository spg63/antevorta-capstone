from __future__ import annotations

import numpy as np

from wocbots.agents import HOLLYWOOD_WEIGHTS, Agent
from wocbots.arena import Arena, RandomInitPolicy, RandomMovementPolicy
from wocbots.types import Cell


def make_agent() -> Agent:
    return Agent(
        features=("f0",),
        eval_accuracy=0.5,
        eval_precision=0.5,
        eval_recall=0.5,
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )


def arena_with_agents(n_agents: int, rng: np.random.Generator) -> tuple[Arena, list[Agent]]:
    agents = [make_agent() for _ in range(n_agents)]
    arena = Arena(n_agents)
    init_policy = RandomInitPolicy()
    for agent in agents:
        init_policy.place(agent, arena, rng)

    return (arena, agents)


def manhattan(c1: Cell, c2: Cell) -> int:
    row_diff = abs(c1[0] - c2[0])
    col_diff = abs(c1[1] - c2[1])
    return row_diff + col_diff


def test_movement_policy_stays_within_bounds() -> None:
    # arrange
    rng = np.random.default_rng(0)
    n = 10
    arena, agents = arena_with_agents(n, rng)
    policy = RandomMovementPolicy()

    # act
    # assert
    for agent in agents:
        for _ in range(15):
            cell = policy.move(agent, arena, rng)
            row, col = cell
            assert 0 <= row < arena.rows
            assert 0 <= col < arena.cols


def test_random_movement_policy_never_teleports_at_zero_percent() -> None:
    # arrange
    rng = np.random.default_rng(42)
    n = 10
    arena, agents = arena_with_agents(n, rng)
    policy = RandomMovementPolicy(teleport_rate=0.0)
    agent = agents[0]
    old_cell = arena.cell(agent)

    # act
    new_cell = policy.move(agent, arena, rng)

    # assert
    manhattan_dist = manhattan(old_cell, new_cell)
    assert manhattan_dist == 1


def test_random_movement_policy_always_teleports_at_hundred_percent() -> None:
    rng = np.random.default_rng(42)
    n = 20
    arena, agents = arena_with_agents(n, rng)
    policy = RandomMovementPolicy(teleport_rate=1.0)
    agent = agents[0]

    # act
    non_adjacent_found = False
    for _ in range(5):
        old_cell = arena.cell(agent)
        new_cell = policy.move(agent, arena, rng)
        manhattan_dist = manhattan(old_cell, new_cell)
        if manhattan_dist > 1:
            non_adjacent_found = True
            break

    # assert
    assert non_adjacent_found


def test_blocked_agent_teleports_to_empty_cell() -> None:
    # arrange
    rng = np.random.default_rng(0)
    n = 20
    arena = Arena(n)
    target = make_agent()
    target_cell = (1, 1)
    arena.place(target, target_cell)

    blocked_neighbors = [(2, 1), (0, 1), (1, 2), (1, 0)]
    for cell in blocked_neighbors:
        for _ in range(2):
            arena.place(make_agent(), cell)

    policy = RandomMovementPolicy(teleport_rate=0.0)

    # act
    new_cell = policy.move(target, arena, rng)

    # assert
    manhattan_dist = manhattan(target_cell, new_cell)
    assert manhattan_dist > 1
    assert new_cell not in blocked_neighbors
    assert new_cell != target_cell
    assert len(arena.agents_at(new_cell)) == 1


def test_anti_clique_forced_geometry_blocks_repeat_and_third_meeting() -> None:
    # arrange
    rng = np.random.default_rng(0)
    n = 20
    arena = Arena(n)
    a = make_agent()
    b = make_agent()
    arena.place(a, (2, 2))
    arena.place(b, (2, 3))

    for cell in [(2, 1), (3, 2), (3, 3), (2, 4), (1, 3), (1, 2)]:
        for _ in range(2):
            arena.place(make_agent(), cell)

    policy = RandomMovementPolicy(teleport_rate=0.0)

    def met_b(before: Cell, after: Cell) -> bool:
        return after != before and b in arena.agents_at(after)

    # act
    before0 = arena.cell(a)
    after0 = policy.move(a, arena, rng)
    round0_met = met_b(before0, after0)

    before1 = arena.cell(a)
    after1 = policy.move(a, arena, rng)
    round1_met = met_b(before1, after1)

    before2 = arena.cell(a)
    after2 = policy.move(a, arena, rng)
    round2_met = met_b(before2, after2)

    after3 = policy.move(a, arena, rng)

    before4 = arena.cell(a)
    after4 = policy.move(a, arena, rng)
    round4_met = met_b(before4, after4)
    round4_teleported = manhattan(before4, after4) > 1

    # assert
    assert round0_met is True
    assert round1_met is False
    assert round2_met is True
    assert round4_met is False
    assert round4_teleported is True
    assert after3 == before0
