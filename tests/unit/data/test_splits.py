"""W1-05 test requirements: split determinism, structural leakage guard, no-revenue guard,
and persistence round-trip (S1/S2's actual deliverable — the artifact must survive a
save/load cycle byte-identically, since every downstream experiment reads it back from
disk rather than re-splitting).
"""

import numpy as np
import pandas as pd
import pytest

from wocbots.data.splits import (
    apply_scaling,
    build_feature_matrix,
    load_split_artifact,
    make_split,
    write_split_artifact,
)


@pytest.fixture
def labeled_df() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    n = 400
    df = pd.DataFrame(
        {
            "tmdbId": np.arange(n),
            "budget": rng.uniform(1_000, 100_000_000, n),
            "vote_count": rng.uniform(0, 5000, n),
            "vote_average": rng.uniform(0, 10, n),
            "tmdb_popularity": rng.uniform(0, 200, n),
            "runtime": rng.uniform(60, 200, n),
            "revenue": rng.uniform(0, 500_000_000, n),
        }
    )
    df["label"] = (df["revenue"] > 2 * df["budget"]).astype(int)
    return df


FEATURES = ["budget", "vote_count", "vote_average", "tmdb_popularity", "runtime"]


def test_split_is_deterministic_for_same_seed(labeled_df: pd.DataFrame) -> None:
    a = make_split(labeled_df, "label", rng=np.random.default_rng(42), feature_columns=FEATURES)
    b = make_split(labeled_df, "label", rng=np.random.default_rng(42), feature_columns=FEATURES)
    assert list(a.train_ids) == list(b.train_ids)
    assert list(a.eval_ids) == list(b.eval_ids)
    assert list(a.test_ids) == list(b.test_ids)
    assert a.scaler_min.equals(b.scaler_min)
    assert a.scaler_max.equals(b.scaler_max)


def test_different_seeds_give_different_membership(labeled_df: pd.DataFrame) -> None:
    a = make_split(labeled_df, "label", rng=np.random.default_rng(1), feature_columns=FEATURES)
    b = make_split(labeled_df, "label", rng=np.random.default_rng(2), feature_columns=FEATURES)
    assert list(a.train_ids) != list(b.train_ids)


def test_stratification_within_one_point(labeled_df: pd.DataFrame) -> None:
    overall_rate = labeled_df["label"].mean() * 100
    artifact = make_split(labeled_df, "label", rng=np.random.default_rng(7), feature_columns=FEATURES)
    for ids, name in [
        (artifact.train_ids, "train"),
        (artifact.eval_ids, "eval"),
        (artifact.test_ids, "test"),
    ]:
        sub = labeled_df[labeled_df["tmdbId"].isin(ids)]
        rate = sub["label"].mean() * 100
        assert abs(rate - overall_rate) <= 1.0, f"{name} split off by {abs(rate - overall_rate):.2f}pt"


def test_train_eval_test_partition_is_disjoint_and_complete(labeled_df: pd.DataFrame) -> None:
    artifact = make_split(labeled_df, "label", rng=np.random.default_rng(3), feature_columns=FEATURES)
    train, eval_, test = set(artifact.train_ids), set(artifact.eval_ids), set(artifact.test_ids)
    assert train & eval_ == set()
    assert train & test == set()
    assert eval_ & test == set()
    assert train | eval_ | test == set(labeled_df["tmdbId"])


def test_scaler_params_are_a_function_of_train_rows_only(labeled_df: pd.DataFrame) -> None:
    """Structural leakage guard: perturbing test/eval rows' feature values must not
    change the scaler params, since they were computed once from train_ids and never
    touch the dataframe again.
    """
    artifact = make_split(labeled_df, "label", rng=np.random.default_rng(11), feature_columns=FEATURES)
    non_train_mask = ~labeled_df["tmdbId"].isin(artifact.train_ids)

    perturbed = labeled_df.copy()
    perturbed.loc[non_train_mask, FEATURES] = perturbed.loc[non_train_mask, FEATURES] * 1000 + 1e9

    artifact_again = make_split(perturbed, "label", rng=np.random.default_rng(11), feature_columns=FEATURES)
    assert artifact.scaler_min.equals(artifact_again.scaler_min)
    assert artifact.scaler_max.equals(artifact_again.scaler_max)


def test_apply_scaling_produces_values_in_unit_range_for_train(labeled_df: pd.DataFrame) -> None:
    artifact = make_split(labeled_df, "label", rng=np.random.default_rng(5), feature_columns=FEATURES)
    train_df = labeled_df[labeled_df["tmdbId"].isin(artifact.train_ids)]
    scaled = apply_scaling(train_df, artifact)
    assert (scaled >= 0).all().all()
    assert (scaled <= 1).all().all()


def test_no_revenue_guard_in_feature_matrix_builder(labeled_df: pd.DataFrame) -> None:
    with pytest.raises(ValueError):
        build_feature_matrix(labeled_df, feature_columns=[*FEATURES, "revenue"])


def test_no_revenue_guard_in_make_split(labeled_df: pd.DataFrame) -> None:
    with pytest.raises(ValueError):
        make_split(labeled_df, "label", rng=np.random.default_rng(1), feature_columns=[*FEATURES, "revenue"])


def test_write_then_load_split_artifact_round_trips(labeled_df: pd.DataFrame, tmp_path) -> None:
    artifact = make_split(labeled_df, "label", rng=np.random.default_rng(9), feature_columns=FEATURES)
    manifest_path = write_split_artifact(artifact, tmp_path, version="test")
    loaded = load_split_artifact(manifest_path)

    assert list(loaded.train_ids) == list(artifact.train_ids)
    assert list(loaded.eval_ids) == list(artifact.eval_ids)
    assert list(loaded.test_ids) == list(artifact.test_ids)
    assert loaded.feature_columns == artifact.feature_columns
    assert loaded.scaler_min.equals(artifact.scaler_min)
    assert loaded.scaler_max.equals(artifact.scaler_max)
    assert len(loaded.fold_ids) == len(artifact.fold_ids)
    fold_pairs = zip(artifact.fold_ids, loaded.fold_ids, strict=True)
    for (orig_train, orig_val), (load_train, load_val) in fold_pairs:
        assert list(orig_train) == list(load_train)
        assert list(orig_val) == list(load_val)
