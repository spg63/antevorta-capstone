"""W4-04 mechanism comparison — integration + manifest pins."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from wocbots.agents.classifier import LabeledData
from wocbots.agents.crowd import CrowdConfig, build_crowd
from wocbots.experiments.evaluation import run_mechanism_comparison
from wocbots.experiments.harness import run_experiment
from wocbots.experiments.manifest import read_manifest


def _blobs(rng: np.random.Generator, *, n: int = 400, n_features: int = 5) -> LabeledData:
    x = rng.standard_normal((n, n_features))
    y = (x[:, 0] + rng.standard_normal(n) * 0.3 > 0).astype(np.int_)
    x[y == 1, 0] += 3.0
    x[y == 0, 0] -= 3.0
    names = tuple(f"f{i}" for i in range(n_features))
    return LabeledData(features=names, X=x, y=y)


def test_mechanism_comparison_manifest_smoke(tmp_path: Path) -> None:
    """Fast smoke: one run produces a manifest with stable tier metric keys."""
    from wocbots.experiments.config import ExperimentConfig

    cfg = ExperimentConfig.from_yaml(Path("configs/mechanism_comparison.yaml"))
    fast = cfg.model_copy(update={"n_runs": 1, "name": "mechanism_comparison_smoke"})
    path = run_experiment(fast, manifest_dir=tmp_path)
    manifest = read_manifest(path)
    assert manifest.config.kind == "mechanism_comparison"
    assert len(manifest.runs) == 1
    assert "trust_accuracy" in manifest.runs[0].metrics
    assert "trust_tier_high_accuracy" in manifest.runs[0].metrics
    assert "trust_tier_coin_flip_accuracy" in manifest.runs[0].metrics
    assert "participant_count_s000" in manifest.runs[0].metrics
    assert "uwm_accuracy" in manifest.aggregate


@pytest.mark.slow
def test_mechanism_comparison_manifest_from_one_config(tmp_path: Path) -> None:
    """W4-04 test req 3: full 10-run comparison regenerates from one config."""
    path = run_experiment(Path("configs/mechanism_comparison.yaml"), manifest_dir=tmp_path)
    manifest = read_manifest(path)
    assert manifest.config.kind == "mechanism_comparison"
    assert len(manifest.runs) == 10
    assert "trust_accuracy" in manifest.runs[0].metrics
    assert "trust_tier_high_accuracy" in manifest.runs[0].metrics
    assert "uwm_accuracy" in manifest.aggregate


@pytest.mark.slow
def test_mechanism_ordering_trust_ge_wvm_ge_uwm() -> None:
    """Hollywood-style integration: mechanism 3 ≥ 2 ≥ 1 on 10-run means (W4-04 test req 2)."""
    config = CrowdConfig.from_yaml(Path("configs/crowd_smoke.yaml"))
    trust_means: list[float] = []
    wvm_means: list[float] = []
    uwm_means: list[float] = []

    for run_seed in range(10):
        rng = np.random.default_rng(run_seed)
        train = _blobs(rng)
        ev = _blobs(rng)
        test = _blobs(rng, n=200)
        built = build_crowd(config=config, train_data=train, eval_data=ev, rng=rng)
        summary = run_mechanism_comparison(built.agents, test, rng=rng)
        trust_means.append(summary.metrics["trust"].accuracy)
        wvm_means.append(summary.metrics["wvm"].accuracy)
        uwm_means.append(summary.metrics["uwm"].accuracy)

    assert float(np.mean(trust_means)) >= float(np.mean(wvm_means))
    assert float(np.mean(wvm_means)) >= float(np.mean(uwm_means))
