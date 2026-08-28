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

This module calls NO RNG of its own: it only advances the Generator it is handed
(the W0-04 RNG-discipline guard).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from wocbots.agents.classifier import LabeledData
from wocbots.data import (
    apply_scaling,
    build_hollywood_features,
    make_split,
    variant_a_label,
)
from wocbots.data.splits import SplitArtifact

LABEL_COLUMN = "label"
ID_COLUMN = "tmdbId"
DEFAULT_RAW_ROOT = "data/raw"


@dataclass(frozen=True)
class HollywoodSplit:
    """One seeded run's materialized train/eval data plus the artifact they came from.

    `feature_columns` excludes `revenue`; `train_data`/`eval_data` carry it as a trailing
    column so the §9.2 sanity agent is constructible, and ONLY via `build_sanity_agent`.
    """

    artifact: SplitArtifact
    feature_columns: list[str]
    train_data: LabeledData
    eval_data: LabeledData


@lru_cache(maxsize=4)
def load_labeled_hollywood(raw_root: str = DEFAULT_RAW_ROOT) -> pd.DataFrame:
    """The W1-03 ETL + W1-04 variant-(a) label, memoised per raw-data root.

    Deterministic and seed-free, so memoising cannot affect any result — it only avoids
    re-reading 20,000,263 rating rows once per seeded run. `rating.csv` is read with
    `usecols` because spec §4.3.3-4 needs exactly two columns of a ~690 MB file.
    """
    root = Path(raw_root)
    tmdb_movies = pd.read_csv(root / "tmdb" / "movies.csv")
    tmdb_credits = pd.read_csv(root / "tmdb" / "credits.csv")
    links = pd.read_csv(root / "movielens" / "link.csv")
    ml_movies = pd.read_csv(root / "movielens" / "movie.csv")
    ratings = pd.read_csv(root / "movielens" / "rating.csv", usecols=["movieId", "rating"])

    features = build_hollywood_features(tmdb_movies, tmdb_credits, links, ml_movies, ratings)
    labeled = features.copy()
    labeled[LABEL_COLUMN] = variant_a_label(labeled)
    return labeled


def materialize_split(labeled: pd.DataFrame, rng: np.random.Generator) -> HollywoodSplit:
    """Derive one run's split from `rng` and pack the scaled train/eval matrices.

    The SPLIT is per-run on purpose: split membership is the stochastic dimension the spec
    §9.1 ten-run protocol samples. Memoising it would report one run ten times with a
    fabricated std.
    """
    artifact = make_split(labeled, label_column=LABEL_COLUMN, rng=rng)
    feature_columns = list(artifact.feature_columns)

    scaled = apply_scaling(labeled, artifact)
    scaled[LABEL_COLUMN] = labeled[LABEL_COLUMN].to_numpy()

    train_mask = labeled[ID_COLUMN].isin(artifact.train_ids).to_numpy()
    eval_mask = labeled[ID_COLUMN].isin(artifact.eval_ids).to_numpy()

    # See the module docstring: TRAIN-only min-max, matching every other column's treatment.
    revenue_raw = labeled["revenue"].to_numpy(dtype=float)
    revenue_train = revenue_raw[train_mask]
    revenue_min = float(revenue_train.min())
    revenue_span = float(revenue_train.max()) - revenue_min or 1.0
    scaled["revenue"] = np.clip((revenue_raw - revenue_min) / revenue_span, 0.0, 1.0)

    columns = [*feature_columns, "revenue"]
    return HollywoodSplit(
        artifact=artifact,
        feature_columns=feature_columns,
        train_data=_labeled_data(scaled[train_mask], columns),
        eval_data=_labeled_data(scaled[eval_mask], columns),
    )


def _labeled_data(frame: pd.DataFrame, columns: list[str]) -> LabeledData:
    return LabeledData(
        features=tuple(columns),
        X=frame[columns].to_numpy(dtype=float),
        y=frame[LABEL_COLUMN].to_numpy(dtype=int),
    )
