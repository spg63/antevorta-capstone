"""W1-05 test requirements: split determinism, structural leakage guard, no-revenue guard,
and persistence round-trip (S1/S2's actual deliverable — the artifact must survive a
save/load cycle byte-identically, since every downstream experiment reads it back from
disk rather than re-splitting).
"""

import json
import shutil
from dataclasses import replace
from pathlib import Path

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
            "_rowid": np.arange(n),
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
        sub = labeled_df[labeled_df["_rowid"].isin(ids)]
        rate = sub["label"].mean() * 100
        assert abs(rate - overall_rate) <= 1.0, f"{name} split off by {abs(rate - overall_rate):.2f}pt"


def test_train_eval_test_partition_is_disjoint_and_complete(labeled_df: pd.DataFrame) -> None:
    artifact = make_split(labeled_df, "label", rng=np.random.default_rng(3), feature_columns=FEATURES)
    train, eval_, test = set(artifact.train_ids), set(artifact.eval_ids), set(artifact.test_ids)
    assert train & eval_ == set()
    assert train & test == set()
    assert eval_ & test == set()
    assert train | eval_ | test == set(labeled_df["_rowid"])


def test_scaler_params_are_a_function_of_train_rows_only(labeled_df: pd.DataFrame) -> None:
    """Structural leakage guard: perturbing test/eval rows' feature values must not
    change the scaler params, since they were computed once from train_ids and never
    touch the dataframe again.
    """
    artifact = make_split(labeled_df, "label", rng=np.random.default_rng(11), feature_columns=FEATURES)
    non_train_mask = ~labeled_df["_rowid"].isin(artifact.train_ids)

    perturbed = labeled_df.copy()
    perturbed.loc[non_train_mask, FEATURES] = perturbed.loc[non_train_mask, FEATURES] * 1000 + 1e9

    artifact_again = make_split(perturbed, "label", rng=np.random.default_rng(11), feature_columns=FEATURES)
    assert artifact.scaler_min.equals(artifact_again.scaler_min)
    assert artifact.scaler_max.equals(artifact_again.scaler_max)


def test_apply_scaling_produces_values_in_unit_range_for_train(labeled_df: pd.DataFrame) -> None:
    artifact = make_split(labeled_df, "label", rng=np.random.default_rng(5), feature_columns=FEATURES)
    train_df = labeled_df[labeled_df["_rowid"].isin(artifact.train_ids)]
    scaled = apply_scaling(train_df, artifact)
    assert (scaled >= 0).all().all()
    assert (scaled <= 1).all().all()


def test_no_revenue_guard_in_feature_matrix_builder(labeled_df: pd.DataFrame) -> None:
    with pytest.raises(ValueError):
        build_feature_matrix(labeled_df, feature_columns=[*FEATURES, "revenue"])


def test_no_revenue_guard_in_make_split(labeled_df: pd.DataFrame) -> None:
    with pytest.raises(ValueError):
        make_split(labeled_df, "label", rng=np.random.default_rng(1), feature_columns=[*FEATURES, "revenue"])


def test_folds_partition_the_train_ids_and_exclude_the_eval_slice(labeled_df: pd.DataFrame) -> None:
    """Regression guard: the folds must be cut from the post-eval-carve-out train set.

    Fails against the original `skf.split(train_idx, ...)` loop, which cut from the 80%
    slice taken BEFORE the eval rows were removed — every fold's training side then carried
    the eval rows, so any Q2 cross-validation would be scored against agent eval metrics
    computed on rows it had already trained on.
    """
    artifact = make_split(labeled_df, "label", rng=np.random.default_rng(3), feature_columns=FEATURES)
    train_ids = set(artifact.train_ids)
    eval_ids = set(artifact.eval_ids)

    for fold_train, fold_val in artifact.fold_ids:
        assert set(fold_train) | set(fold_val) == train_ids
        assert set(fold_train) & set(fold_val) == set()
        assert not (set(fold_train) | set(fold_val)) & eval_ids


def test_folds_never_touch_the_test_split(labeled_df: pd.DataFrame) -> None:
    artifact = make_split(labeled_df, "label", rng=np.random.default_rng(4), feature_columns=FEATURES)
    test_ids = set(artifact.test_ids)
    for fold_train, fold_val in artifact.fold_ids:
        assert not (set(fold_train) | set(fold_val)) & test_ids


def test_write_then_load_split_artifact_round_trips(labeled_df: pd.DataFrame, tmp_path: Path) -> None:
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


def test_split_artifact_loads_after_the_pair_is_moved(labeled_df: pd.DataFrame, tmp_path: Path) -> None:
    """The manifest's `ids_path` is provenance, not an address — a written-then-relocated
    artifact pair must still load, since experiments consume these from wherever they sit.
    """
    artifact = make_split(labeled_df, "label", rng=np.random.default_rng(11), feature_columns=FEATURES)
    written = tmp_path / "written"
    manifest_path = write_split_artifact(artifact, written, version="test")

    moved = tmp_path / "moved"
    shutil.move(str(written), str(moved))

    loaded = load_split_artifact(moved / manifest_path.name)
    assert list(loaded.train_ids) == list(artifact.train_ids)


def test_load_rejects_tampered_duplicate_membership(labeled_df: pd.DataFrame, tmp_path: Path) -> None:
    """An NPZ edit must not turn into a silently accepted split artifact."""
    artifact = make_split(labeled_df, "label", rng=np.random.default_rng(12), feature_columns=FEATURES)
    manifest_path = write_split_artifact(artifact, tmp_path, version="test")
    npz_path = tmp_path / "split_test.npz"
    with np.load(npz_path) as original:
        payload = {key: original[key] for key in original.files}
    payload["train_ids"] = np.append(payload["train_ids"], payload["train_ids"][0])
    np.savez(npz_path, **payload)

    with pytest.raises(ValueError, match="metadata|duplicate ids"):
        load_split_artifact(manifest_path)


def test_load_rejects_tampered_json_metadata(labeled_df: pd.DataFrame, tmp_path: Path) -> None:
    artifact = make_split(labeled_df, "label", rng=np.random.default_rng(15), feature_columns=FEATURES)
    manifest_path = write_split_artifact(artifact, tmp_path, version="test")
    manifest = json.loads(manifest_path.read_text())
    manifest["n_test"] += 1
    manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match="JSON metadata"):
        load_split_artifact(manifest_path)


def test_materialization_rejects_incomplete_source_partition(labeled_df: pd.DataFrame) -> None:
    """The source-aware validation rejects an otherwise plausible missing membership."""
    from wocbots.experiments.hollywood_data import materialize_split

    artifact = make_split(labeled_df, "label", rng=np.random.default_rng(13), feature_columns=FEATURES)
    tampered = replace(artifact, test_ids=artifact.test_ids[:-1])

    with pytest.raises(ValueError, match="complete source partition"):
        materialize_split(labeled_df, tampered)


def test_materialization_cannot_regenerate_a_split(labeled_df: pd.DataFrame) -> None:
    """Consumers accept only artifacts; an RNG can never trigger a hidden re-split."""
    from wocbots.experiments.hollywood_data import materialize_split

    with pytest.raises(TypeError, match="persisted SplitArtifact"):
        materialize_split(labeled_df, np.random.default_rng(14))  # type: ignore[arg-type]
