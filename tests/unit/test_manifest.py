from __future__ import annotations

import json
from pathlib import Path

from wocbots.experiments.config import ExperimentConfig
from wocbots.experiments.manifest import (
    Manifest,
    MetricSummary,
    RunResult,
    read_manifest,
    write_manifest,
)
from wocbots.experiments.provenance import capture_provenance


def _sample_manifest() -> Manifest:
    return Manifest(
        provenance=capture_provenance(),
        config=ExperimentConfig(name="roundtrip", kind="dummy", seed=1, n_runs=1),
        runs=[RunResult(run_index=0, metrics={"mean": 0.1, "std": 1.0})],
        aggregate={"mean": MetricSummary(mean=0.1, std=0.0)},
    )


def test_round_trip(tmp_path: Path) -> None:
    manifest = _sample_manifest()
    path = write_manifest(manifest, tmp_path)
    assert path.exists()
    loaded = read_manifest(path)
    assert loaded == manifest


def test_filename_convention(tmp_path: Path) -> None:
    manifest = _sample_manifest()
    path = write_manifest(manifest, tmp_path)
    assert path.name.startswith("roundtrip_")
    assert path.suffix == ".json"
    # <name>_<UTCstamp>_<shortsha>.json -> exactly 3 underscore-delimited parts after name
    stem_parts = path.stem.split("_")
    assert stem_parts[0] == "roundtrip"
    assert len(stem_parts) == 3  # name, stamp, shortsha


def test_canonical_json_sorted_utf8_trailing_newline(tmp_path: Path) -> None:
    manifest = _sample_manifest()
    path = write_manifest(manifest, tmp_path)
    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    parsed = json.loads(text)
    # sort_keys=True at write time -> raw text key order matches sorted order
    reserialized_sorted = json.dumps(parsed, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    assert text == reserialized_sorted


def test_manifest_extra_field_rejected() -> None:
    payload = _sample_manifest().model_dump(mode="json")
    payload["unexpected"] = True
    try:
        Manifest.model_validate(payload)
    except Exception as exc:  # pydantic.ValidationError
        assert "unexpected" in str(exc)
    else:
        raise AssertionError("expected ValidationError for unknown manifest field")
