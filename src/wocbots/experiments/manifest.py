"""Manifest models and the canonical JSON writer (W0-03 S3).

The manifest is the only output path an experiment has: a config in, a
`Manifest` out, one file per invocation, filename-stamped so nothing
overwrites a prior run's evidence.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from wocbots.experiments.config import ExperimentConfig
from wocbots.experiments.provenance import Provenance


class RunResult(BaseModel):
    """One seeded run's metrics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_index: int
    metrics: dict[str, float]


class MetricSummary(BaseModel):
    """Aggregate over all runs for one metric."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mean: float
    std: float
    """Population std over runs (ddof=0) — documented here, never silently
    changed to a sample std elsewhere."""


class Manifest(BaseModel):
    """The complete record of one experiment invocation.

    `schema_version` evolves additively; removing/renaming a field is a
    migration, not a silent bump (plan §11).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1
    provenance: Provenance
    config: ExperimentConfig
    runs: list[RunResult]
    aggregate: dict[str, MetricSummary]


def _short_sha(git_sha: str) -> str:
    """First 8 hex chars of the sha, ignoring any `+dirty` suffix."""
    return git_sha.split("+", 1)[0][:8]


def manifest_filename(*, name: str, created_utc: str, git_sha: str) -> str:
    """`<name>_<UTCstamp>_<shortsha>.json`, per plan §7-S3."""
    stamp = datetime.fromisoformat(created_utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{name}_{stamp}_{_short_sha(git_sha)}.json"


def write_manifest(manifest: Manifest, directory: Path) -> Path:
    """Write `manifest` as canonical JSON under `directory`; return the path.

    Canonical form: `sort_keys=True`, UTF-8, a trailing newline. Filenames
    are timestamp-stamped, so repeated invocations never collide/overwrite.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    filename = manifest_filename(
        name=manifest.config.name,
        created_utc=manifest.provenance.created_utc,
        git_sha=manifest.provenance.git_sha,
    )
    path = directory / filename
    payload = manifest.model_dump(mode="json")
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def read_manifest(path: Path) -> Manifest:
    """Read + validate a manifest JSON file back into a `Manifest`."""
    return Manifest.model_validate_json(Path(path).read_text(encoding="utf-8"))
