"""W1-06: feature-correlation anchor analysis. Pure analysis, no toolkit code paths —
ranks candidate agent features by association with the label (point-biserial correlation
+ first-component PCA loadings), on the TRAIN split only (spec §5.1, §9.2). Run once per
dataset; the chosen anchor set becomes configuration for W2-03.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pointbiserialr
from sklearn.decomposition import PCA

from wocbots.data.ground_truth import load_labeled_sqlite
from wocbots.data.splits import (
    SplitArtifact,
    load_split_artifact,
    split_artifact_digest,
    validate_split_source,
)

# sklearn's `random_state` wants a plain int, never a Generator.
_SEED_UPPER_BOUND = 2**31 - 1


def _seed_from(rng: np.random.Generator) -> int:
    """One integer seed for sklearn, drawn from the threaded Generator (mirrors
    `wocbots.agents.classifier._seed_from` / `wocbots.data.splits._seed_from`).
    """
    return int(rng.integers(0, _SEED_UPPER_BOUND))


def rank_features(
    train_df: pd.DataFrame, feature_columns: list[str], label_column: str, rng: np.random.Generator
) -> pd.DataFrame:
    """Point-biserial correlation of each feature with the binary label, plus each
    feature's loading on the first PCA component (computed on min-max-scaled features so
    no single large-scale feature dominates the component by units alone).

    Takes the harness `Generator` (W0-04 RNG-discipline rule) rather than a bare seed —
    this module calls no RNG of its own, it only advances the Generator handed to it.
    """
    if not feature_columns or len(set(feature_columns)) != len(feature_columns):
        raise ValueError("feature_columns must be non-empty and unique")
    missing = set([label_column, *feature_columns]) - set(train_df.columns)
    if missing:
        raise ValueError(f"analysis dataframe is missing columns: {sorted(missing)}")
    labels = train_df[label_column].to_numpy()
    if len(labels) < 2 or not set(labels).issubset({0, 1}):
        raise ValueError(f"{label_column} must contain at least two binary labels")
    if len(set(labels.tolist())) != 2:
        raise ValueError(f"{label_column} must contain both binary classes")
    corr_rows = []
    for col in feature_columns:
        values = train_df[col].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"feature {col!r} contains non-finite values")
        if np.ptp(values) == 0:
            raise ValueError(f"feature {col!r} is constant on the analysis train split")
        r, p = pointbiserialr(labels, values)
        corr_rows.append({"feature": col, "point_biserial_r": float(r), "p_value": float(p)})
    corr_df = pd.DataFrame(corr_rows)

    scaled = train_df[feature_columns].copy()
    span = scaled.max() - scaled.min()
    span = span.replace(0, 1.0)
    scaled = (scaled - scaled.min()) / span

    pca = PCA(n_components=1, random_state=_seed_from(rng))
    pca.fit(scaled.to_numpy())
    loadings = pd.Series(pca.components_[0], index=feature_columns, name="pc1_loading")

    ranking = corr_df.merge(loadings.reset_index().rename(columns={"index": "feature"}), on="feature")
    ranking["abs_point_biserial_r"] = ranking["point_biserial_r"].abs()
    ranking["abs_pc1_loading"] = ranking["pc1_loading"].abs()
    ranking = ranking.sort_values(
        ["abs_point_biserial_r", "feature"], ascending=[False, True], kind="stable"
    ).reset_index(drop=True)
    return ranking


def analyze_train_split(
    labeled: pd.DataFrame, artifact: SplitArtifact, rng: np.random.Generator
) -> dict[str, object]:
    """Rank only the persisted W1-05 training membership, never eval or test rows."""
    validate_split_source(labeled, artifact)
    train = labeled.loc[labeled["_rowid"].isin(artifact.train_ids)]
    if len(train) != len(artifact.train_ids):
        raise ValueError("persisted train membership could not be materialized from the labeled source")
    ranking = rank_features(train, artifact.feature_columns, "label", rng)
    return {
        "artifact_schema_version": 1,
        "ticket": "W1-06",
        "root_seed": int(artifact.seed),
        "source_fingerprint": artifact.source_fingerprint,
        "split_artifact_digest": split_artifact_digest(artifact),
        "feature_columns": artifact.feature_columns,
        "label_column": "label",
        "n_train": len(train),
        "ranking": ranking.to_dict(orient="records"),
    }


def write_anchor_analysis(analysis: dict[str, object], output_path: Path) -> Path:
    """Write canonical, row-free W1-06 evidence atomically for later configuration review."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary_path.write_text(json.dumps(analysis, indent=2, sort_keys=True, allow_nan=False) + "\n")
    os.replace(temporary_path, output_path)
    return output_path


def run_anchor_analysis(
    sqlite_path: Path,
    split_path: Path,
    output_path: Path,
    rng: np.random.Generator,
    analysis_seed: int,
    git_sha: str,
) -> dict[str, object]:
    """Load one persisted source/split pair, rank its training rows, and persist evidence."""
    labeled = load_labeled_sqlite(sqlite_path)
    analysis = analyze_train_split(labeled, load_split_artifact(split_path), rng)
    analysis["analysis_seed"] = analysis_seed
    analysis["git_sha"] = git_sha
    write_anchor_analysis(analysis, output_path)
    return analysis
