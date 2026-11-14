"""Shared Hollywood train/eval materialization for experiments that need the real data.

Extracted from W2-04's runner so W2-03's crowd configs and W2-04's agent table read the
dataset through ONE code path. Two things this centralizes are easy to get wrong separately
and were in fact got wrong once (see `revenue` below):

- **The eval slice is the train-side 90/10, never the test split** (spec §10.5). Both callers
  measure agent quality, which is an eval-slice quantity throughout this codebase.
- **`revenue` is scaled with TRAIN-only statistics.** W1-05 structurally excludes `revenue`
  from its feature matrix (§S3), so any caller wanting the §9.2 sanity agent has to attach it
  by hand. Attaching it RAW (dollars, ~1e8) beside min-max features in [0, 1] destroys the
  fit — the canary scored 55% instead of ~100% and reported a broken pipeline that was
  actually this attachment. Scaling it here, once, from train rows only, keeps the leakage
  discipline W1-05 applies to every other column and gives both callers the same guarantee.

This module never generates membership. Runners load the persisted split artifact;
their seeded generators are reserved for training and later stochastic mechanisms.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from wocbots.agents.classifier import LabeledData
from wocbots.data import (
    apply_scaling,
    load_labeled_sqlite,
)
from wocbots.data.splits import SplitArtifact, split_artifact_digest, validate_split_source

LABEL_COLUMN = "label"
ID_COLUMN = "_rowid"
DEFAULT_LABELED_SQLITE = "data/processed/movies.sqlite"


@dataclass(frozen=True)
class HollywoodSplit:
    """One seeded run's materialized train/eval data plus the artifact they came from.

    `feature_columns` excludes `revenue`. Only the explicitly named ``sanity_*`` views
    carry it for the §9.2 canary.
    """

    artifact: SplitArtifact
    feature_columns: list[str]
    train_data: LabeledData
    eval_data: LabeledData
    test_data: LabeledData
    sanity_train_data: LabeledData
    sanity_eval_data: LabeledData
    sanity_test_data: LabeledData

    @property
    def input_artifacts(self) -> dict[str, str]:
        """Identity of the exact conditions consumed, for each experiment run."""
        return {
            "split_artifact": split_artifact_digest(self.artifact),
            "labeled_source": self.artifact.source_fingerprint,
        }


def load_labeled_hollywood(sqlite_path: str = DEFAULT_LABELED_SQLITE) -> pd.DataFrame:
    """Load W1-04's persisted label; never rebuild labels from raw input files."""
    labeled = load_labeled_sqlite(Path(sqlite_path))
    if LABEL_COLUMN not in labeled:
        raise ValueError("W1-04 labeled SQLite must contain movies.label")
    return labeled


def materialize_split(labeled: pd.DataFrame, artifact: SplitArtifact) -> HollywoodSplit:
    """Materialize only a previously persisted, source-matched split artifact."""
    if not isinstance(artifact, SplitArtifact):
        raise TypeError("materialize_split requires a persisted SplitArtifact")
    validate_split_source(labeled, artifact, LABEL_COLUMN, ID_COLUMN)
    feature_columns = list(artifact.feature_columns)

    scaled = apply_scaling(labeled, artifact)
    scaled[LABEL_COLUMN] = labeled[LABEL_COLUMN].to_numpy()

    train_mask = labeled[ID_COLUMN].isin(artifact.train_ids).to_numpy()
    eval_mask = labeled[ID_COLUMN].isin(artifact.eval_ids).to_numpy()
    test_mask = labeled[ID_COLUMN].isin(artifact.test_ids).to_numpy()

    # See the module docstring: TRAIN-only min-max, matching every other column's treatment.
    revenue_raw = labeled["revenue"].to_numpy(dtype=float)
    revenue_span = artifact.sanity_revenue_max - artifact.sanity_revenue_min or 1.0
    scaled["revenue"] = np.clip((revenue_raw - artifact.sanity_revenue_min) / revenue_span, 0.0, 1.0)

    sanity_columns = [*feature_columns, "revenue"]
    return HollywoodSplit(
        artifact=artifact,
        feature_columns=feature_columns,
        train_data=_labeled_data(scaled[train_mask], feature_columns),
        eval_data=_labeled_data(scaled[eval_mask], feature_columns),
        test_data=_labeled_data(scaled[test_mask], feature_columns),
        sanity_train_data=_labeled_data(scaled[train_mask], sanity_columns),
        sanity_eval_data=_labeled_data(scaled[eval_mask], sanity_columns),
        sanity_test_data=_labeled_data(scaled[test_mask], sanity_columns),
    )


def _labeled_data(frame: pd.DataFrame, columns: list[str]) -> LabeledData:
    return LabeledData(
        features=tuple(columns),
        X=frame[columns].to_numpy(dtype=float),
        y=frame[LABEL_COLUMN].to_numpy(dtype=int),
    )
