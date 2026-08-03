"""Built-in runner kinds.

Importing this module registers its kinds as a side effect — kinds are code,
registered at import (W0-03 S2 / W0-04 S2). `harness.py` imports this module
so that the harness always has at least `"dummy"` available.

Ships exactly one kind of its own: `"dummy"`, deliberately trivial. It
exists so the harness is testable before any real experiment lands: it
draws `params["n"]` (default 1000) standard-normal samples from ITS OWN rng
argument and reports their mean/std.

Experiment kinds owned by other tickets register themselves in their own
module and are imported here for that side effect, so `harness.py`'s CLI can
resolve every shipped kind by name (the registry is the only side door, and
this is how a module gets through it). Currently: W2-04's `"agent_table"`.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from wocbots.experiments import agent_table as _agent_table  # noqa: F401  (registers "agent_table")
from wocbots.experiments.config import ExperimentConfig
from wocbots.experiments.registry import register_kind


def _dummy_runner(config: ExperimentConfig, rng: np.random.Generator) -> Mapping[str, float]:
    n_param = config.params.get("n", 1000)
    n = int(n_param) if isinstance(n_param, (int, float, str)) else 1000
    samples = rng.standard_normal(n)
    return {"mean": float(samples.mean()), "std": float(samples.std())}


register_kind("dummy", _dummy_runner)
