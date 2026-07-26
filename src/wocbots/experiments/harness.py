"""The harness runner (W0-04 S1): config -> seeded runs -> manifest.

This module is THE one seed origin in `src/wocbots/` — the RNG/wall-clock
guard (`tests/unit/test_rng_discipline.py`, W0-04 S3) allows
`numpy.random.SeedSequence` / `numpy.random.default_rng` nowhere else.
`run_experiment` is also the only entry point that executes a registered
kind: there is no second way to run an experiment without producing a
manifest.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from wocbots.experiments import kinds as _kinds  # noqa: F401  (import side effect: registers "dummy")
from wocbots.experiments.config import ExperimentConfig
from wocbots.experiments.manifest import Manifest, MetricSummary, RunResult, write_manifest
from wocbots.experiments.provenance import capture_provenance
from wocbots.experiments.registry import resolve_kind

DEFAULT_MANIFEST_DIR = Path("results/manifests")


def run_experiment(
    config: ExperimentConfig | Path | str,
    *,
    manifest_dir: Path = DEFAULT_MANIFEST_DIR,
) -> Path:
    """Run one experiment end to end; return the path of the written manifest.

    Execution path (plan §5): load/validate config -> resolve the kind from
    the registry -> spawn one independent RNG stream per run from the
    config's single master seed -> run -> aggregate mean/std per metric ->
    stamp provenance -> write the manifest. The manifest is the only output.

    Determinism contract: `SeedSequence(config.seed).spawn(config.n_runs)`
    gives each run an independent child stream descended from one master
    seed. This is deliberately NOT `seed + i` — naive per-run offsets
    produce correlated streams, which is exactly the subtle wrongness this
    harness exists to make unthinkable. Spawn order (not run count) governs
    which stream each run gets, so a config's first K runs are identical
    whether `n_runs` is K or anything larger than K.
    """
    cfg = _load_config(config)
    runner = resolve_kind(cfg.kind)

    seed_seq = np.random.SeedSequence(cfg.seed)  # ALLOWLISTED: the one seed origin (W0-04 S3)
    children = seed_seq.spawn(cfg.n_runs)

    runs: list[RunResult] = []
    for i, child in enumerate(children):
        rng = np.random.default_rng(child)  # ALLOWLISTED: the one seed origin (W0-04 S3)
        metrics = runner(cfg, rng)
        runs.append(RunResult(run_index=i, metrics=dict(metrics)))

    manifest = Manifest(
        provenance=capture_provenance(),
        config=cfg,
        runs=runs,
        aggregate=_aggregate(runs),
    )
    return write_manifest(manifest, manifest_dir)


def _load_config(config: ExperimentConfig | Path | str) -> ExperimentConfig:
    if isinstance(config, ExperimentConfig):
        return config
    return ExperimentConfig.from_yaml(config)


def _aggregate(runs: list[RunResult]) -> dict[str, MetricSummary]:
    if not runs:
        return {}
    metric_names = runs[0].metrics.keys()
    summaries: dict[str, MetricSummary] = {}
    for metric in metric_names:
        values = np.array([run.metrics[metric] for run in runs], dtype=float)
        summaries[metric] = MetricSummary(mean=float(values.mean()), std=float(values.std()))
    return summaries


def _main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m wocbots.experiments.harness <config.yaml>")
    path = run_experiment(Path(sys.argv[1]))
    print(f"wrote manifest: {path}")


if __name__ == "__main__":
    _main()
