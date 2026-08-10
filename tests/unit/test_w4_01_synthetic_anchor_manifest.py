"""W4-01 synthetic anchor manifest + participation accounting."""

from __future__ import annotations

from pathlib import Path

from wocbots.experiments.config import ExperimentConfig
from wocbots.experiments.harness import run_experiment
from wocbots.experiments.manifest import read_manifest


def test_synthetic_anchor_manifest_records_participation(tmp_path: Path) -> None:
    cfg = ExperimentConfig.from_yaml(Path("configs/synthetic_anchor.yaml"))
    fast = cfg.model_copy(update={"n_runs": 1, "name": "synthetic_anchor_smoke"})
    path = run_experiment(fast, manifest_dir=tmp_path)
    manifest = read_manifest(path)
    metrics = manifest.runs[0].metrics
    assert metrics["accuracy"] >= 0.99
    assert "participant_count_s000" in metrics
    assert "participant_count_s199" in metrics
    assert metrics["n_test_samples"] == 200.0
    assert "accuracy" in manifest.aggregate
