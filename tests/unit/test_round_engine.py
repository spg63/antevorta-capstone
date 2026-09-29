from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path

import numpy as np

from wocbots.agents import HOLLYWOOD_WEIGHTS, Agent
from wocbots.arena import Arena, RandomInitPolicy, RandomMovementPolicy, RoundEngine
from wocbots.experiments.config import ExperimentConfig
from wocbots.experiments.harness import run_experiment
from wocbots.experiments.manifest import read_manifest
from wocbots.protocols import MovementPolicy
from wocbots.types import Cell


class SpiedMovementPolicy:
    """Spy wrapper to record the agent processing order by index per round."""

    def __init__(self, real_policy: MovementPolicy, agents: list[Agent]) -> None:
        self.real_policy = real_policy
        self._agents = agents
        self.history: list[list[int]] = []
        self._current_round_indices: list[int] = []

    def move(self, agent: Agent, arena: Arena, rng: np.random.Generator) -> Cell:
        cell = self.real_policy.move(agent, arena, rng)
        agent_idx = self._agents.index(agent)
        self._current_round_indices.append(agent_idx)

        if len(self._current_round_indices) == len(self._agents):
            self.history.append(list(self._current_round_indices))
            self._current_round_indices = []
        return cell


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


def test_run_has_only_two_agents_encounters() -> None:
    # arrange
    rng = np.random.default_rng(0)
    n = 3
    arena, agents = arena_with_agents(n, rng)
    mov_policy = RandomMovementPolicy()
    rdeng = RoundEngine(agents, arena, mov_policy, rng)

    # act
    # assert
    while not rdeng.finished():
        rdeng.round()
        for row in range(arena.rows):
            for col in range(arena.cols):
                assert len(arena.agents_at((row, col))) <= 2


def test_run_agents_max_interactions() -> None:
    # arrange
    rng = np.random.default_rng(0)
    n = 3
    arena, agents = arena_with_agents(n, rng)
    mov_policy = RandomMovementPolicy()
    rde = RoundEngine(agents, arena, mov_policy, rng)
    a_hist: dict[Agent, deque[Agent]] = defaultdict(deque)

    # act
    while not rde.finished():
        rde.round()

    # assert
    log = rde.encounter_log

    for _round, interactions in log.items():
        enc = set()
        for (agent1, agent2), _ in interactions:
            pair = frozenset((agent1, agent2))
            assert pair not in enc
            enc.add(pair)

            if len(a_hist[agent1]) >= 5:
                a_hist[agent1].popleft()
            if len(a_hist[agent2]) >= 5:
                a_hist[agent2].popleft()

            assert a_hist[agent1].count(agent2) <= 2
            assert a_hist[agent2].count(agent1) <= 2
            a_hist[agent1].append(agent2)
            a_hist[agent2].append(agent1)


def test_5_agents_10_rounds() -> None:
    # arrange
    rng = np.random.default_rng(0)
    n = 5
    arena, agents = arena_with_agents(n, rng)
    mov_policy = RandomMovementPolicy()
    rde = RoundEngine(agents, arena, mov_policy, rng)
    counter = 0

    # act
    while not rde.finished():
        rde.round()
        counter += 1

    # assert
    assert counter == 10


def test_105_agents_10_rounds() -> None:
    # arrange
    rng = np.random.default_rng(0)
    n = 105
    arena, agents = arena_with_agents(n, rng)
    mov_policy = RandomMovementPolicy()
    rde = RoundEngine(agents, arena, mov_policy, rng)
    counter = 0

    # act
    while not rde.finished():
        rde.round()
        counter += 1

    # assert
    assert counter == 10


def test_120_agents_12_rounds() -> None:
    # arrange
    rng = np.random.default_rng(0)
    n = 120
    arena, agents = arena_with_agents(n, rng)
    mov_policy = RandomMovementPolicy()
    rde = RoundEngine(agents, arena, mov_policy, rng)
    counter = 0

    # act
    while not rde.finished():
        rde.round()
        counter += 1

    # assert
    assert counter == 12


def test_agent_processsing_order_different_accross_rounds() -> None:
    # arrange
    rng = np.random.default_rng(42)
    n = 10
    arena, agents = arena_with_agents(n, rng)

    real_policy = RandomMovementPolicy()
    spied_policy = SpiedMovementPolicy(real_policy, agents)
    rdeng = RoundEngine(agents, arena, spied_policy, rng)

    # act
    rdeng.round()
    rdeng.round()

    # assert
    assert len(spied_policy.history) >= 2
    assert spied_policy.history[0] != spied_policy.history[1]


def test_agent_processsing_order_same_with_equal_seed() -> None:
    # arrange
    seed = 42
    n = 10
    rng1 = np.random.default_rng(seed)
    arena1, agents1 = arena_with_agents(n, rng1)
    policy1 = SpiedMovementPolicy(RandomMovementPolicy(), agents1)
    rdeng1 = RoundEngine(agents1, arena1, policy1, rng1)
    rng2 = np.random.default_rng(seed)
    arena2, agents2 = arena_with_agents(n, rng2)
    policy2 = SpiedMovementPolicy(RandomMovementPolicy(), agents2)
    rdeng2 = RoundEngine(agents2, arena2, policy2, rng2)

    # act
    while not rdeng1.finished():
        rdeng1.round()
    while not rdeng2.finished():
        rdeng2.round()

    # assert
    assert policy1.history == policy2.history


def test_round_engine_encounter_log_reflects_true_encounters() -> None:
    # arrange
    rng = np.random.default_rng(0)
    n = 10
    arena, agents = arena_with_agents(n, rng)
    mov_policy = RandomMovementPolicy()
    rde = RoundEngine(agents, arena, mov_policy, rng)

    # act
    while not rde.finished():
        rde.round()

    # assert
    for _round_num, encounters in rde.encounter_log.items():
        for pair, cell in encounters:
            agent1, agent2 = pair
            assert agent1 != agent2
            assert agent1 in agents
            assert agent2 in agents
            row, col = cell
            assert 0 <= row < arena.rows
            assert 0 <= col < arena.cols


def test_generate_encounter_statistics_manifest(tmp_path: Path) -> None:
    # arrange

    config = ExperimentConfig(
        name="w3_02_movement_smoke",
        kind="w3_02_movement_smoke",
        seed=42,
        n_runs=5,
        params={"n_agents": 20, "teleport_rate": 0.05},
    )

    # act
    manifest_path = run_experiment(config, manifest_dir=tmp_path)

    # assert
    assert manifest_path.exists()
    manifest = read_manifest(manifest_path)
    assert manifest.config.kind == "w3_02_movement_smoke"
    assert len(manifest.runs) == 5
    assert "encounters_per_agent_round" in manifest.aggregate
    assert manifest.aggregate["encounters_per_agent_round"].mean >= 0
