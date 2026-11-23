from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from wocbots.data.anchor_analysis import analyze_train_split, rank_features, write_anchor_analysis
from wocbots.data.splits import DEFAULT_FEATURE_COLUMNS, make_split

FEATURES = ["budget", "vote_count", "vote_average", "tmdb_popularity", "runtime"]


def test_anchor_analysis_smoke_runs_seeded_and_ranks_budget_high() -> None:
    rng = np.random.default_rng(0)
    n = 500
    budget = rng.uniform(1_000, 100_000_000, n)
    noise = rng.normal(0, 1, n)
    # construct a label strongly (but not perfectly) driven by budget so the analysis
    # has something real to find, plus pure-noise features that should rank lower.
    label = (budget + noise * 5_000_000 > np.median(budget)).astype(int)
    df = pd.DataFrame(
        {
            "budget": budget,
            "vote_count": rng.uniform(0, 5000, n),
            "vote_average": rng.uniform(0, 10, n),
            "tmdb_popularity": rng.uniform(0, 200, n),
            "runtime": rng.uniform(60, 200, n),
            "label": label,
        }
    )
    ranking = rank_features(df, FEATURES, "label", rng=np.random.default_rng(1))
    assert set(ranking["feature"]) == set(FEATURES)
    assert "budget" in set(ranking["feature"].head(1))
    assert {"pc1_loading", "abs_pc1_loading", "p_value"} <= set(ranking.columns)


def _labeled_frame() -> pd.DataFrame:
    rng = np.random.default_rng(8)
    n = 120
    frame = pd.DataFrame({column: rng.normal(size=n) for column in DEFAULT_FEATURE_COLUMNS})
    frame["budget"] = np.arange(n, dtype=float)
    frame["revenue"] = rng.uniform(1.0, 100.0, size=n)
    frame["label"] = (frame["budget"] >= 60).astype(int)
    frame["_rowid"] = np.arange(n)
    return frame


def test_analysis_uses_persisted_train_split_and_emits_deterministic_artifact(tmp_path: Path) -> None:
    frame = _labeled_frame()
    artifact = make_split(frame, "label", np.random.default_rng(3), root_seed=3)
    first = analyze_train_split(frame, artifact, np.random.default_rng(42))
    second = analyze_train_split(frame, artifact, np.random.default_rng(42))
    first_path = write_anchor_analysis(first, tmp_path / "first.json")
    second_path = write_anchor_analysis(second, tmp_path / "second.json")

    assert first_path.read_bytes() == second_path.read_bytes()
    assert first["n_train"] == len(artifact.train_ids)
    assert first["ranking"][0]["feature"] == "budget"  # type: ignore[index]


def test_analysis_rejects_split_source_mismatch() -> None:
    frame = _labeled_frame()
    artifact = make_split(frame, "label", np.random.default_rng(3), root_seed=3)
    changed = frame.copy()
    changed.loc[0, "budget"] = -999.0

    with pytest.raises(ValueError, match="does not match"):
        analyze_train_split(changed, artifact, np.random.default_rng(42))


def test_rank_features_rejects_constant_feature() -> None:
    frame = _labeled_frame()
    frame["runtime"] = 1.0

    with pytest.raises(ValueError, match="constant"):
        rank_features(frame, DEFAULT_FEATURE_COLUMNS, "label", np.random.default_rng(42))
