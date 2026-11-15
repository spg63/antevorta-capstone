"""Artifact identity must survive real runner → harness → persisted result boundaries."""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from wocbots.data.ground_truth import load_labeled_sqlite
from wocbots.data.splits import DEFAULT_FEATURE_COLUMNS, make_split, write_split_artifact
from wocbots.experiments import agent_table, harness
from wocbots.experiments.config import ExperimentConfig
from wocbots.experiments.manifest import Manifest, RunnerOutput, read_manifest


@pytest.mark.parametrize("kind", ["w2_03_hollywood_crowd", "w2_04_agent_table"])
def test_runners_persist_consumed_artifact_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    rng = np.random.default_rng(5)
    frame = pd.DataFrame({col: rng.random(120) for col in DEFAULT_FEATURE_COLUMNS})
    frame["revenue"] = rng.random(120)
    frame["label"] = np.tile([0, 1], 60)
    sqlite_path = tmp_path / "movies.sqlite"
    with sqlite3.connect(sqlite_path) as connection:
        frame.to_sql("movies", connection, index=False)
    labeled = load_labeled_sqlite(sqlite_path)
    artifact = make_split(labeled, "label", np.random.default_rng(42), root_seed=42)
    artifact_path = write_split_artifact(artifact, tmp_path, "test")
    # Training accuracy is irrelevant to provenance; exercise the actual table runner
    # and materializer without paying for twenty classifiers in this plumbing test.
    monkeypatch.setattr(agent_table, "_accuracy_for_row", lambda *args: 0.5)
    config = ExperimentConfig(
        name="identity-test",
        kind=kind,
        seed=7,
        n_runs=2,
        params={
            "labeled_sqlite": str(sqlite_path),
            "split_artifact": str(artifact_path),
            "crowd_config": "configs/crowd_hollywood_5agent.yaml",
        },
    )
    first = read_manifest(harness.run_experiment(config, manifest_dir=tmp_path / "first"))
    assert all(
        run.input_artifacts
        == {
            "split_artifact": artifact.content_digest,
            "labeled_source": artifact.source_fingerprint,
        }
        for run in first.runs
    )
    assert "split_artifact" not in first.aggregate

    # Same config/path/source, different memberships: the saved experiment must
    # distinguish these conditions even when numerical metrics happen to agree.
    other = make_split(labeled, "label", np.random.default_rng(43), root_seed=43)
    write_split_artifact(other, tmp_path, "test")
    second = read_manifest(harness.run_experiment(config, manifest_dir=tmp_path / "second"))
    assert second.config == first.config
    assert second.runs[0].input_artifacts["labeled_source"] == artifact.source_fingerprint
    assert second.runs[0].input_artifacts["split_artifact"] == other.content_digest
    assert second.runs[0].input_artifacts != first.runs[0].input_artifacts


def test_harness_refuses_to_average_different_input_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    outputs = iter(
        [
            RunnerOutput({"accuracy": 0.5}, {"split_artifact": "first"}),
            RunnerOutput({"accuracy": 0.7}, {"split_artifact": "second"}),
        ]
    )
    monkeypatch.setattr(harness, "resolve_kind", lambda _kind: lambda _cfg, _rng: next(outputs))
    config = ExperimentConfig(name="changed-input", kind="dummy", seed=1, n_runs=2)
    with pytest.raises(ValueError, match="input artifacts changed between runs"):
        harness.run_experiment(config, manifest_dir=tmp_path)
    assert not list(tmp_path.glob("*.json"))


def test_old_result_manifests_remain_readable(tmp_path: Path) -> None:
    path = harness.run_experiment(
        ExperimentConfig(name="legacy", kind="dummy", seed=1, n_runs=1), manifest_dir=tmp_path
    )
    payload = read_manifest(path).model_dump()
    payload["schema_version"] = 1
    for run in payload["runs"]:
        del run["input_artifacts"]
    legacy = Manifest.model_validate(payload)
    assert legacy.schema_version == 1
    assert legacy.runs[0].input_artifacts == {}
