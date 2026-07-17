from __future__ import annotations

from pathlib import Path
from typing import Any

from wocbots.experiments.config import ExperimentConfig
from wocbots.experiments.harness import run_experiment
from wocbots.experiments.manifest import read_manifest


def _cfg(**overrides: Any) -> ExperimentConfig:
    base: dict[str, Any] = dict(
        name="harness_test", kind="dummy", seed=42, n_runs=3, params={"n": 100}
    )
    base.update(overrides)
    return ExperimentConfig(**base)


def test_round_trip(tmp_path: Path) -> None:
    path = run_experiment(_cfg(), manifest_dir=tmp_path)
    manifest = read_manifest(path)
    assert len(manifest.runs) == 3
    assert set(manifest.aggregate) == {"mean", "std"}
    assert path.name.startswith("harness_test_")


def test_dummy_smoke_yaml_end_to_end(tmp_path: Path) -> None:
    path = run_experiment(Path("configs/dummy_smoke.yaml"), manifest_dir=tmp_path)
    manifest = read_manifest(path)
    assert manifest.config.name == "dummy_smoke"
    assert manifest.config.kind == "dummy"
    assert len(manifest.runs) == 3
    assert manifest.schema_version == 1


def test_determinism_same_config_twice_byte_equal(tmp_path: Path) -> None:
    cfg = _cfg()
    m1 = read_manifest(run_experiment(cfg, manifest_dir=tmp_path / "a"))
    m2 = read_manifest(run_experiment(cfg, manifest_dir=tmp_path / "b"))
    assert m1.model_dump(exclude={"provenance"}) == m2.model_dump(exclude={"provenance"})


def test_determinism_spawn_order_not_run_count(tmp_path: Path) -> None:
    m3 = read_manifest(run_experiment(_cfg(n_runs=3), manifest_dir=tmp_path / "three"))
    m5 = read_manifest(run_experiment(_cfg(n_runs=5), manifest_dir=tmp_path / "five"))
    assert [r.metrics for r in m3.runs] == [r.metrics for r in m5.runs[:3]]


def test_per_run_metrics_pairwise_distinct(tmp_path: Path) -> None:
    manifest = read_manifest(run_experiment(_cfg(), manifest_dir=tmp_path))
    means = [r.metrics["mean"] for r in manifest.runs]
    assert len(set(means)) == len(means)


def test_no_side_door_unregistered_kind_errors(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(KeyError, match="unknown experiment kind"):
        run_experiment(_cfg(kind="not-a-real-kind"), manifest_dir=tmp_path)
