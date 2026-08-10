"""W4-04 — mechanism-comparison experiment kind (spec §9.1)."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import numpy as np

from wocbots.agents.classifier import LabeledData
from wocbots.agents.crowd import CrowdConfig, build_crowd
from wocbots.experiments.config import ExperimentConfig
from wocbots.experiments.evaluation import metrics_to_dict, run_mechanism_comparison
from wocbots.experiments.registry import register_kind


def _separable_blobs(
    rng: np.random.Generator,
    *,
    n: int = 400,
    n_features: int = 5,
    sep: float = 3.0,
) -> LabeledData:
    """Linearly separable synthetic set: f0 carries the signal (spec §11 anchor)."""
    x = rng.standard_normal((n, n_features))
    y = (x[:, 0] + rng.standard_normal(n) * 0.3 > 0).astype(np.int_)
    x[y == 1, 0] += sep
    x[y == 0, 0] -= sep
    names = tuple(f"f{i}" for i in range(n_features))
    return LabeledData(features=names, X=x, y=y)


def _resolve_crowd_config(config: ExperimentConfig) -> CrowdConfig:
    crowd_path = config.params.get("crowd_config", "configs/crowd_smoke.yaml")
    if not isinstance(crowd_path, str):
        raise ValueError("params.crowd_config must be a YAML path string")
    return CrowdConfig.from_yaml(Path(crowd_path))


def _resolve_int_param(config: ExperimentConfig, key: str, default: int) -> int:
    raw = config.params.get(key, default)
    if isinstance(raw, bool) or not isinstance(raw, (int, float, str)):
        raise ValueError(f"params.{key} must be numeric")
    return int(raw)


def _mechanism_comparison_runner(
    config: ExperimentConfig,
    rng: np.random.Generator,
) -> Mapping[str, float]:
    crowd_config = _resolve_crowd_config(config)
    n_train = _resolve_int_param(config, "n_train", 400)
    n_test = _resolve_int_param(config, "n_test", 200)

    train = _separable_blobs(rng, n=n_train)
    eval_data = _separable_blobs(rng, n=n_train)
    test = _separable_blobs(rng, n=n_test)

    built = build_crowd(
        config=crowd_config,
        train_data=train,
        eval_data=eval_data,
        rng=rng,
    )
    summary = run_mechanism_comparison(built.agents, test, rng=rng)
    return metrics_to_dict(summary)


register_kind("mechanism_comparison", _mechanism_comparison_runner)
