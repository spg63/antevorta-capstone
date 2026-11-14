"""Build W1-05's persisted split from W1-04's labeled SQLite output.

This is a script, not `src/wocbots/`, so it is outside the RNG-discipline AST guard's scope
(`tests/unit/test_rng_discipline.py` only walks `src/wocbots/`) — the one seed origin here is
this script's own `np.random.default_rng(args.seed)` call, mirroring how
`scripts/extract_w1_02_reference.py` is the one caller of `wocbots.data.ground_truth`'s writers.

Usage:
    python scripts/build_w1_05_splits.py \
        --sqlite data/processed/movies.sqlite \
        --derived-dir data/derived \
        --version v1 \
        --seed 42
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

from wocbots.data.ground_truth import load_labeled_sqlite
from wocbots.data.splits import make_split, split_artifact_digest, write_split_artifact


def _digest(ids: np.ndarray) -> str:
    """Return a portable digest of one persisted membership array, never its raw ids."""
    return hashlib.sha256(np.asarray(ids).tobytes()).hexdigest()


def write_provenance_manifest(
    artifact_path: Path, provenance_path: Path, sqlite_path: Path, artifact: object
) -> None:
    """Write the committed, row-free evidence for a generated split artifact."""
    from wocbots.data.splits import SplitArtifact

    if not isinstance(artifact, SplitArtifact):
        raise TypeError("artifact must be a SplitArtifact")
    try:
        git_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"], check=True, capture_output=True, text=True
        ).stdout
        if status.strip():
            git_sha += "+dirty"
    except (OSError, subprocess.CalledProcessError):
        git_sha = "unavailable"
    membership_digests = {
        "train": _digest(artifact.train_ids),
        "eval": _digest(artifact.eval_ids),
        "test": _digest(artifact.test_ids),
        "folds": [
            {"train": _digest(train), "validation": _digest(validation)}
            for train, validation in artifact.fold_ids
        ],
    }
    provenance = {
        "ticket": "W1-05",
        "artifact_schema_version": 2,
        "artifact_digest": split_artifact_digest(artifact),
        "artifact_path": str(artifact_path),
        "labeled_sqlite": str(sqlite_path),
        "git_sha": git_sha,
        "root_seed": artifact.seed,
        "source_fingerprint": artifact.source_fingerprint,
        "feature_columns": artifact.feature_columns,
        "split_counts": {
            "train": len(artifact.train_ids),
            "eval": len(artifact.eval_ids),
            "test": len(artifact.test_ids),
            "folds": len(artifact.fold_ids),
        },
        "membership_digests": membership_digests,
        "scaler": {
            "normal_min": artifact.scaler_min.to_dict(),
            "normal_max": artifact.scaler_max.to_dict(),
            "sanity_revenue_min": artifact.sanity_revenue_min,
            "sanity_revenue_max": artifact.sanity_revenue_max,
        },
    }
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", type=Path, default=Path("data/processed/movies.sqlite"))
    parser.add_argument("--derived-dir", type=Path, default=Path("data/derived"))
    parser.add_argument("--version", type=str, default="v1")
    parser.add_argument("--seed", type=int, default=42, help="Project convention: 42 (see configs/*.yaml)")
    parser.add_argument("--label-column", type=str, default="label")
    parser.add_argument("--id-column", type=str, default="_rowid")
    parser.add_argument(
        "--provenance-manifest",
        type=Path,
        default=Path("results/manifests/w1_05_split_provenance.json"),
    )
    args = parser.parse_args()

    df = load_labeled_sqlite(args.sqlite)
    rng = np.random.default_rng(args.seed)  # ALLOWLISTED: this script is the seed origin, not src/wocbots/

    artifact = make_split(
        df, label_column=args.label_column, rng=rng, id_column=args.id_column, root_seed=args.seed
    )
    manifest_path = write_split_artifact(artifact, args.derived_dir, args.version)
    write_provenance_manifest(manifest_path, args.provenance_manifest, args.sqlite, artifact)

    summary = {
        "manifest_path": str(manifest_path),
        "provenance_manifest_path": str(args.provenance_manifest),
        "seed": artifact.seed,
        "n_rows_total": len(df),
        "n_train": len(artifact.train_ids),
        "n_eval": len(artifact.eval_ids),
        "n_test": len(artifact.test_ids),
        "n_folds": len(artifact.fold_ids),
        "feature_columns": artifact.feature_columns,
        "label_column": args.label_column,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
