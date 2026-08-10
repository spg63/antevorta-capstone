"""Built-in runner kinds.

Importing this module registers its kinds as a side effect — kinds are code,
registered at import (W0-03 S2 / W0-04 S2). `harness.py` imports this module
so that the harness always has at least `"dummy"` available.

Ships exactly one kind: `"dummy"`, deliberately trivial. It exists so the
harness is testable before any real experiment lands: it draws
`params["n"]` (default 1000) standard-normal samples from ITS OWN rng
argument and reports their mean/std.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from wocbots.agents import HOLLYWOOD_WEIGHTS, Agent
from wocbots.arena import Arena, RandomInitPolicy, RandomMovementPolicy, RoundEngine
from wocbots.experiments.config import ExperimentConfig
from wocbots.experiments.registry import register_kind


def _dummy_runner(config: ExperimentConfig, rng: np.random.Generator) -> Mapping[str, float]:
    n_param = config.params.get("n", 1000)
    n = int(n_param) if isinstance(n_param, (int, float, str)) else 1000
    samples = rng.standard_normal(n)
    return {"mean": float(samples.mean()), "std": float(samples.std())}


register_kind("dummy", _dummy_runner)


def _make_agent() -> Agent:
    return Agent(
        features=("f0",),
        eval_accuracy=0.5,
        eval_precision=0.5,
        eval_recall=0.5,
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )


def _movement_smoke_runner(config: ExperimentConfig, rng: np.random.Generator) -> Mapping[str, float]:
    n_agents_raw = config.params.get("n_agents", 20)
    n_agents = int(n_agents_raw) if isinstance(n_agents_raw, (int, float, str)) else 20

    teleport_rate_raw = config.params.get("teleport_rate", 0.05)
    teleport_rate = float(teleport_rate_raw) if isinstance(teleport_rate_raw, (int, float, str)) else 0.05

    agents = [_make_agent() for _ in range(n_agents)]
    arena = Arena(n_agents)
    init_policy = RandomInitPolicy()
    for agent in agents:
        init_policy.place(agent, arena, rng)

    movement_policy = RandomMovementPolicy(teleport_rate=teleport_rate)
    engine = RoundEngine(agents, arena, movement_policy, rng)

    while not engine.finished():
        engine.round()

    total_rounds = engine.rounds_completed
    total_encounters = sum(len(round_log) for round_log in engine.encounter_log.values())

    return {
        "total_rounds": float(total_rounds),
        "total_encounters": float(total_encounters),
        "encounters_per_agent_round": total_encounters / (n_agents * total_rounds),
    }


register_kind("w3_02_movement_smoke", _movement_smoke_runner)
