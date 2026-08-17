"""Splits and normalization (W1-05): seeded, label-stratified 80/20 train/test, a 90/10
eval slice off the training side, 5-fold artifacts for Q2, and min-max scaling fit on the
TRAIN split only. Every experiment downstream reuses these persisted artifacts — nothing
re-randomizes splits between experiments (preamble §3 forbidden-shortcut register).

`revenue` is structurally excluded from the feature matrix here (spec §4.3.9): it defines
the label and MUST NOT appear as an agent input outside the sanity-check agent (§9.2),
which reads it directly from the labeled dataframe, not from this module's feature matrix.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split

# revenue defines the label; it must never reach the feature matrix (spec §4.3.9).
EXCLUDED_FROM_FEATURES = {"revenue"}

# sklearn's `random_state`/`StratifiedKFold` want a plain int, never a Generator.
_SEED_UPPER_BOUND = 2**31 - 1


def _seed_from(rng: np.random.Generator) -> int:
    """One integer seed for sklearn, drawn from the threaded Generator.

    `rng.integers` is a method on the passed-in Generator, NOT a `numpy.random.*` module
    call, so the single-seed-origin contract (W0-04 RNG-discipline guard) holds. Mirrors
    `wocbots.agents.classifier._seed_from`.
    """
    return int(rng.integers(0, _SEED_UPPER_BOUND))


DEFAULT_FEATURE_COLUMNS = [
    "budget",
    "vote_count",
    "vote_average",
    "tmdb_popularity",
    "runtime",
    "tmdb_vote_average",
    "tmdb_vote_count",
    "ml_vote_average",
    "ml_vote_count",
]


@dataclass(frozen=True)
class SplitArtifact:
    """Persisted split membership + scaler parameters for one seed.

    `row_ids` are index labels into the labeled dataframe this split was built from, not
    positions — persist alongside the dataframe's id column (`tmdbId`) if serialized.
    """

    seed: int
    train_ids: np.ndarray
    eval_ids: np.ndarray  # 90/10 slice OFF the training side
    test_ids: np.ndarray
    fold_ids: list[tuple[np.ndarray, np.ndarray]]  # 5-fold (train_idx, val_idx) on TRAIN ids
    feature_columns: list[str]
    scaler_min: pd.Series
    scaler_max: pd.Series


def make_split(
    df: pd.DataFrame,
    label_column: str,
    rng: np.random.Generator,
    id_column: str = "tmdbId",
    feature_columns: list[str] | None = None,
    test_size: float = 0.2,
    eval_size: float = 0.1,
    n_folds: int = 5,
) -> SplitArtifact:
    """Spec §4.3.8-9: build one seed's full split + scaler artifact.

    - 80/20 label-stratified train/test.
    - 90/10 label-stratified eval slice off the TRAIN side (agent eval metrics; spec
      §10.5 — this data never touches the test split).
    - 5-fold label-stratified folds over the TRAIN ids (Q2 cross-validation; cheap to
      generate now per W1-05's own note).
    - Min-max scaler parameters computed on the TRAIN split ONLY.

    Takes the harness `Generator` (W0-04 RNG-discipline rule) rather than a bare seed —
    this module calls no RNG of its own, it only advances the Generator handed to it via
    `_seed_from`, mirroring `wocbots.agents.classifier`/`wocbots.agents.crowd`. Same
    Generator state in ⇒ byte-identical artifact out.
    """
    if feature_columns is None:
        feature_columns = [c for c in DEFAULT_FEATURE_COLUMNS if c in df.columns]
    bad = EXCLUDED_FROM_FEATURES & set(feature_columns)
    if bad:
        raise ValueError(f"feature_columns must not include excluded columns: {bad}")

    # sklearn's splitters want an int/RandomState, not a Generator; draw three independent
    # sub-seeds from the threaded Generator rather than reusing one (which would make step
    # order part of the contract). The first is also the artifact's nominal `seed` record.
    seed_train_test = _seed_from(rng)
    seed_eval_slice = _seed_from(rng)
    seed_kfold = _seed_from(rng)

    ids = df[id_column].to_numpy()
    labels = df[label_column].to_numpy()

    train_idx, test_idx = train_test_split(
        np.arange(len(df)),
        test_size=test_size,
        stratify=labels,
        random_state=seed_train_test,
    )

    train_labels = labels[train_idx]
    train_sub_idx, eval_sub_idx = train_test_split(
        np.arange(len(train_idx)),
        test_size=eval_size,
        stratify=train_labels,
        random_state=seed_eval_slice,
    )
    real_train_idx = train_idx[train_sub_idx]
    real_eval_idx = train_idx[eval_sub_idx]

    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed_kfold)
    fold_ids: list[tuple[np.ndarray, np.ndarray]] = []
    for fold_train_pos, fold_val_pos in skf.split(train_idx, train_labels):
        fold_ids.append((ids[train_idx[fold_train_pos]], ids[train_idx[fold_val_pos]]))

    train_features = df.iloc[real_train_idx][feature_columns]
    scaler_min = train_features.min()
    scaler_max = train_features.max()

    return SplitArtifact(
        seed=seed_train_test,
        train_ids=ids[real_train_idx],
        eval_ids=ids[real_eval_idx],
        test_ids=ids[test_idx],
        fold_ids=fold_ids,
        feature_columns=feature_columns,
        scaler_min=scaler_min,
        scaler_max=scaler_max,
    )


def apply_scaling(df: pd.DataFrame, artifact: SplitArtifact) -> pd.DataFrame:
    """Apply the artifact's TRAIN-fit min-max scaler to any slice of the dataframe.

    Structurally cannot leak: `scaler_min`/`scaler_max` were computed once, from `train_ids`
    only, at `make_split` time — this function only ever reads those already-fixed values.
    """
    out = df[artifact.feature_columns].copy()
    span = (artifact.scaler_max - artifact.scaler_min).replace(0, 1.0)
    scaled = (out - artifact.scaler_min) / span
    return scaled.clip(lower=0.0, upper=1.0)


def build_feature_matrix(df: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    """The one place a feature matrix is materialized — asserts `revenue` cannot leak in
    even if a caller's `feature_columns` list is built carelessly (W1-05 test req 3).
    """
    bad = EXCLUDED_FROM_FEATURES & set(feature_columns)
    if bad:
        raise ValueError(f"feature matrix must not include excluded columns: {bad}")
    return df[feature_columns].copy()


def write_split_artifact(artifact: SplitArtifact, out_dir: Path, version: str) -> Path:
    """Persist a `SplitArtifact` (S1/S2's deliverable): every experiment and mechanism
    comparison reuses this exact file rather than re-splitting (spec §9.1, forbidden
    shortcut register). `out_dir` is expected to be a gitignored derived-data location
    (e.g. `data/derived/`), same convention as `wocbots.data.ground_truth`'s writers.

    Layout: `<out_dir>/split_<version>.npz` holds the id arrays (train/eval/test + one
    pair of arrays per fold, since npz can't nest lists of tuples); `<out_dir>/split_<version>.json`
    holds everything else (seed, feature columns, scaler params, fold count) plus a
    pointer back to the npz file, so either file alone tells you where its sibling is.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    npz_path = out_dir / f"split_{version}.npz"
    json_path = out_dir / f"split_{version}.json"

    npz_payload: dict[str, np.ndarray] = {
        "train_ids": artifact.train_ids,
        "eval_ids": artifact.eval_ids,
        "test_ids": artifact.test_ids,
    }
    for i, (fold_train_ids, fold_val_ids) in enumerate(artifact.fold_ids):
        npz_payload[f"fold_{i}_train_ids"] = fold_train_ids
        npz_payload[f"fold_{i}_val_ids"] = fold_val_ids
    np.savez(npz_path, **npz_payload)  # type: ignore[arg-type]  # np-stub limitation: **dict[str, ndarray] is fine at runtime

    manifest = {
        "seed": artifact.seed,
        "feature_columns": artifact.feature_columns,
        "n_folds": len(artifact.fold_ids),
        "n_train": int(len(artifact.train_ids)),
        "n_eval": int(len(artifact.eval_ids)),
        "n_test": int(len(artifact.test_ids)),
        "scaler_min": artifact.scaler_min.to_dict(),
        "scaler_max": artifact.scaler_max.to_dict(),
        "ids_path": str(npz_path),
    }
    json_path.write_text(json.dumps(manifest, indent=2))
    return json_path


def load_split_artifact(json_path: Path) -> SplitArtifact:
    """Inverse of `write_split_artifact`. Reads the JSON manifest, then the sibling npz
    it points to for the id arrays.
    """
    manifest = json.loads(json_path.read_text())
    npz = np.load(manifest["ids_path"])

    n_folds = manifest["n_folds"]
    fold_ids = [(npz[f"fold_{i}_train_ids"], npz[f"fold_{i}_val_ids"]) for i in range(n_folds)]

    feature_columns = manifest["feature_columns"]
    return SplitArtifact(
        seed=manifest["seed"],
        train_ids=npz["train_ids"],
        eval_ids=npz["eval_ids"],
        test_ids=npz["test_ids"],
        fold_ids=fold_ids,
        feature_columns=feature_columns,
        scaler_min=pd.Series(manifest["scaler_min"])[feature_columns],
        scaler_max=pd.Series(manifest["scaler_max"])[feature_columns],
    )
