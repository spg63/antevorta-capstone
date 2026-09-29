"""W1-05 S1/S2 runner: build the seeded, label-stratified split + scaler artifact from the
shipped labeled dataset (`data/hollywood_features_labeled_variant_a.csv`, see W1-04's ticket
RESULT block for how that label was ratified) and persist it to `data/derived/`.

This is a script, not `src/wocbots/`, so it is outside the RNG-discipline AST guard's scope
(`tests/unit/test_rng_discipline.py` only walks `src/wocbots/`) — the one seed origin here is
this script's own `np.random.default_rng(args.seed)` call, mirroring how
`scripts/extract_w1_02_reference.py` is the one caller of `wocbots.data.ground_truth`'s writers.

Usage:
    python scripts/build_w1_05_splits.py \
        --labeled-csv data/hollywood_features_labeled_variant_a.csv \
        --derived-dir data/derived \
        --version v1 \
        --seed 42
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from wocbots.data.splits import make_split, write_split_artifact


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--labeled-csv", type=Path, default=Path("data/hollywood_features_labeled_variant_a.csv")
    )
    parser.add_argument("--derived-dir", type=Path, default=Path("data/derived"))
    parser.add_argument("--version", type=str, default="v1")
    parser.add_argument("--seed", type=int, default=42, help="Project convention: 42 (see configs/*.yaml)")
    parser.add_argument("--label-column", type=str, default="label_a")
    parser.add_argument("--id-column", type=str, default="tmdbId")
    args = parser.parse_args()

    df = pd.read_csv(args.labeled_csv)
    rng = np.random.default_rng(args.seed)  # ALLOWLISTED: this script is the seed origin, not src/wocbots/

    artifact = make_split(df, label_column=args.label_column, rng=rng, id_column=args.id_column)
    manifest_path = write_split_artifact(artifact, args.derived_dir, args.version)

    summary = {
        "manifest_path": str(manifest_path),
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
