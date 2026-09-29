"""W4-01 synthetic e2e anchor — full loop ~100% on separable data (spec §11)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from wocbots.agents.classifier import LabeledData
from wocbots.agents.crowd import CrowdConfig, build_crowd
from wocbots.experiments.evaluation import run_test_set


def _blobs(rng: np.random.Generator, *, n: int = 400, n_features: int = 5) -> LabeledData:
    x = rng.standard_normal((n, n_features))
    y = (x[:, 0] + rng.standard_normal(n) * 0.3 > 0).astype(np.int_)
    x[y == 1, 0] += 3.0
    x[y == 0, 0] -= 3.0
    names = tuple(f"f{i}" for i in range(n_features))
    return LabeledData(features=names, X=x, y=y)


@pytest.mark.slow
def test_synthetic_anchor_reaches_near_perfect_accuracy() -> None:
    """Permanent canary: seeded full loop ~100% test accuracy, stable across 10 runs."""
    config = CrowdConfig.from_yaml(Path("configs/crowd_smoke.yaml"))
    accuracies: list[float] = []

    for run_seed in range(10):
        rng = np.random.default_rng(run_seed)
        train = _blobs(rng)
        ev = _blobs(rng)
        test = _blobs(rng, n=200)
        built = build_crowd(config=config, train_data=train, eval_data=ev, rng=rng)
        summary = run_test_set(built.agents, test, rng=rng)
        accuracies.append(summary.metrics.accuracy)
        assert summary.metrics.accuracy >= 0.99

    assert float(np.mean(accuracies)) >= 0.99
