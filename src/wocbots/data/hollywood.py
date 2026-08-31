"""Hollywood movie-success ETL (W1-03): join TMDb 5000 + MovieLens 20M, clean, and build
combined features. Spec §4.3 items 1-6 are normative and each has a dedicated function
below so every rule is independently unit-testable on the W1-01 fixtures.

Labels are deliberately NOT computed here — that is W1-04's job (the reconciliation gate
lives there so a labeling mistake can't hide inside this diff). This module's output keeps
raw `revenue`/`budget` for W1-04's use, plus provenance ids (`tmdbId`, `movieId`).

No dataset-specific vocabulary leaks into `wocbots.agents/arena/interaction/aggregation` —
this module is where "movie" is allowed to mean something (preamble §7).
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

# Columns this pipeline guarantees on its output (features + provenance ids + raw
# budget/revenue for W1-04's labeling). No label columns — see module docstring.
OUTPUT_COLUMNS = [
    "tmdbId",
    "movieId",
    "title",
    "budget",
    "revenue",
    "runtime",
    "tmdb_popularity",
    "tmdb_vote_average",
    "tmdb_vote_count",
    "ml_vote_average",
    "ml_vote_count",
    "vote_average",
    "vote_count",
    "genres",
]


def join_datasets(tmdb_movies: pd.DataFrame, links: pd.DataFrame, ml_movies: pd.DataFrame) -> pd.DataFrame:
    """Spec §4.3 rule 1: join on `links.csv`'s `tmdbId`, keep only movies present in BOTH
    datasets (inner join on both link legs).

    `links` maps movieId <-> tmdbId <-> imdbId; rows with a null `tmdbId` (a MovieLens
    title with no TMDb mapping) cannot join and are correctly dropped by the inner merge.
    """
    links_valid = links.dropna(subset=["tmdbId"]).copy()
    links_valid["tmdbId"] = links_valid["tmdbId"].astype("int64")
    links_valid["movieId"] = links_valid["movieId"].astype("int64")

    tmdb = tmdb_movies.rename(columns={"id": "tmdbId"}).copy()
    tmdb["tmdbId"] = tmdb["tmdbId"].astype("int64")

    ml = ml_movies.rename(columns={"genres": "ml_genres"}).copy()
    ml["movieId"] = ml["movieId"].astype("int64")

    merged = tmdb.merge(links_valid[["movieId", "tmdbId"]], on="tmdbId", how="inner")
    merged = merged.merge(ml, on="movieId", how="inner")
    return merged


def _parse_tmdb_genre_names(raw: object) -> list[str]:
    """TMDb's `genres` column is a JSON list of {id, name} objects (as text)."""
    if not isinstance(raw, str) or not raw.strip():
        return []
    try:
        items = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    return [item["name"] for item in items if isinstance(item, dict) and "name" in item]


def _parse_ml_genre_names(raw: object) -> list[str]:
    """MovieLens `genres` is pipe-separated, with the sentinel `(no genres listed)`."""
    if not isinstance(raw, str) or raw == "(no genres listed)" or not raw.strip():
        return []
    return raw.split("|")


def genre_intersection(tmdb_genres_raw: object, ml_genres_raw: object) -> list[str]:
    """Spec §4.3 rule 6: the intersection of the two datasets' genre lists for a movie.

    Order follows the TMDb list (arbitrary but deterministic) so downstream consumers get
    a stable ordering. A stretch feature per the spec — callers may ignore this column.
    """
    tmdb_names = _parse_tmdb_genre_names(tmdb_genres_raw)
    ml_names = set(_parse_ml_genre_names(ml_genres_raw))
    return [name for name in tmdb_names if name in ml_names]


def clean(df: pd.DataFrame, required_feature_columns: list[str]) -> pd.DataFrame:
    """Spec §4.3 rule 2: drop rows with impossible/missing-coded values.

    Zeros in `budget`/`revenue` are missing-coded ("unknown"), never a real $0 movie —
    dropping `revenue <= 0` here (rather than only at labeling time) is deliberate: a
    silently-zero revenue must never fall through to W1-04 and get labeled "failure".
    `required_feature_columns` covers "missing any feature used in the experiment": any
    NaN/zero-as-missing in those columns drops the row too.
    """
    out = df.copy()
    out = out[(out["budget"] > 0) & (out["revenue"] > 0)]
    for col in required_feature_columns:
        if col not in out.columns:
            continue
        out = out[out[col].notna()]
        # zeros are the plague across this data (§4.3.2); a genuinely-zero popularity or
        # vote count is indistinguishable from "unknown" in this source, so treat as missing.
        if pd.api.types.is_numeric_dtype(out[col]):
            out = out[out[col] != 0]
    return out


def aggregate_ml_ratings(ratings: pd.DataFrame) -> pd.DataFrame:
    """Spec §4.3 rules 3-4: scale MovieLens ratings (0-5) onto the TMDb 0-10 scale by
    ×2, THEN aggregate per movie to `ml_vote_count` (rating count) and `ml_vote_average`
    (mean of the scaled ratings). Scaling before aggregating vs. after gives the same
    mean (linear operation) but this order matches the spec's rule numbering exactly.
    """
    scaled = ratings.copy()
    scaled["rating_x2"] = scaled["rating"] * 2.0
    grouped = scaled.groupby("movieId")["rating_x2"].agg(ml_vote_count="count", ml_vote_average="mean")
    return grouped.reset_index()


def combine_vote_features(df: pd.DataFrame) -> pd.DataFrame:
    """Spec §4.3 rule 5: combined `vote_count` (sum) and count-weighted `vote_average`.

    Requires `tmdb_vote_average`/`tmdb_vote_count`/`ml_vote_average`/`ml_vote_count`
    already present (the caller has renamed TMDb's `vote_average`/`vote_count` and
    merged in `aggregate_ml_ratings`'s output — movies with zero MovieLens ratings get
    `ml_vote_count = 0`, which the weighted mean handles as a zero-weight term).
    """
    out = df.copy()
    out["ml_vote_count"] = out["ml_vote_count"].fillna(0)
    out["ml_vote_average"] = out["ml_vote_average"].fillna(0.0)

    out["vote_count"] = (out["tmdb_vote_count"] + out["ml_vote_count"]).astype(float)
    numerator = (
        out["tmdb_vote_average"] * out["tmdb_vote_count"] + out["ml_vote_average"] * out["ml_vote_count"]
    ).astype(float)

    denominator = out["vote_count"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        vote_average = np.divide(
            numerator.to_numpy(dtype=float),
            denominator,
            out=np.full(len(out), np.nan),
            where=denominator != 0,
        )
    out["vote_average"] = vote_average
    return out


def build_hollywood_features(
    tmdb_movies: pd.DataFrame,
    tmdb_credits: pd.DataFrame,  # noqa: ARG001 - accepted for interface symmetry with §4.2's data landmarks; unused (no §4.3 rule consumes cast/crew)
    links: pd.DataFrame,
    ml_movies: pd.DataFrame,
    ratings: pd.DataFrame,
    required_feature_columns: list[str] | None = None,
) -> pd.DataFrame:
    """The full W1-03 pipeline: join -> clean -> transform. No label columns in the
    output (W1-04 owns labeling). `required_feature_columns` defaults to the spec's
    listed agent-feature set (§4.3, final paragraph) minus the optional genre column.
    """
    if required_feature_columns is None:
        required_feature_columns = [
            "budget",
            "runtime",
            "tmdb_popularity",
            "tmdb_vote_average",
            "tmdb_vote_count",
        ]

    joined = join_datasets(tmdb_movies, links, ml_movies)
    # The join retains both source titles as pandas suffixes. The public W1-03 contract
    # carries the TMDb title as movie provenance; without this normalization the declared
    # OUTPUT_COLUMNS schema silently loses its `title` member after the merge.
    joined["title"] = joined["title_x"]
    joined = joined.rename(
        columns={
            "popularity": "tmdb_popularity",
            "vote_average": "tmdb_vote_average",
            "vote_count": "tmdb_vote_count",
        }
    )

    ml_agg = aggregate_ml_ratings(ratings)
    joined = joined.merge(ml_agg, on="movieId", how="left")

    joined = combine_vote_features(joined)

    joined["genres"] = [
        genre_intersection(g_tmdb, g_ml)
        for g_tmdb, g_ml in zip(joined["genres"], joined["ml_genres"], strict=True)
    ]

    cleaned = clean(joined, required_feature_columns)

    result = cleaned[[c for c in OUTPUT_COLUMNS if c in cleaned.columns]].reset_index(drop=True)
    return result
