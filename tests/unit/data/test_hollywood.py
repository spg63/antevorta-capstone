"""W1-03 test requirement 1: per-rule unit tests on the W1-01 fixtures."""

from pathlib import Path

import pandas as pd
import pytest

from wocbots.data.hollywood import (
    aggregate_ml_ratings,
    build_hollywood_features,
    clean,
    combine_vote_features,
    genre_intersection,
    join_datasets,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


@pytest.fixture
def tmdb_movies() -> pd.DataFrame:
    return pd.read_csv(FIXTURES / "tmdb5000" / "tmdb_5000_movies_fixture.csv")


@pytest.fixture
def tmdb_credits() -> pd.DataFrame:
    return pd.read_csv(FIXTURES / "tmdb5000" / "tmdb_5000_credits_fixture.csv")


@pytest.fixture
def links() -> pd.DataFrame:
    return pd.read_csv(FIXTURES / "movielens20m" / "link_fixture.csv")


@pytest.fixture
def ml_movies() -> pd.DataFrame:
    return pd.read_csv(FIXTURES / "movielens20m" / "movie_fixture.csv")


@pytest.fixture
def ratings() -> pd.DataFrame:
    return pd.read_csv(FIXTURES / "movielens20m" / "rating_fixture.csv")


# ---- Rule 1: join keys ----------------------------------------------------------


def test_join_keeps_only_movies_present_in_both_datasets(
    tmdb_movies: pd.DataFrame, links: pd.DataFrame, ml_movies: pd.DataFrame
) -> None:
    joined = join_datasets(tmdb_movies, links, ml_movies)
    # every joined row's tmdbId must have existed in TMDb AND had a valid link AND a
    # matching MovieLens movie row
    valid_links = links.dropna(subset=["tmdbId"])
    expected_tmdb_ids = set(tmdb_movies["id"]) & set(valid_links["tmdbId"].astype(int))
    assert set(joined["tmdbId"]).issubset(expected_tmdb_ids)
    assert len(joined) > 0


def test_join_drops_unmapped_links_rows(
    links: pd.DataFrame, ml_movies: pd.DataFrame, tmdb_movies: pd.DataFrame
) -> None:
    # the fixture deliberately includes a null-tmdbId link row; it must not survive.
    assert links["tmdbId"].isna().any()
    joined = join_datasets(tmdb_movies, links, ml_movies)
    assert joined["tmdbId"].notna().all()


# ---- Rule 2: clean / drop conditions -------------------------------------------


def test_clean_drops_zero_budget() -> None:
    df = pd.DataFrame({"budget": [0, 1000], "revenue": [5000, 5000], "runtime": [100, 100]})
    out = clean(df, required_feature_columns=["runtime"])
    assert list(out["budget"]) == [1000]


def test_clean_drops_zero_revenue() -> None:
    df = pd.DataFrame({"budget": [1000, 1000], "revenue": [0, 5000], "runtime": [100, 100]})
    out = clean(df, required_feature_columns=["runtime"])
    assert list(out["revenue"]) == [5000]


def test_clean_drops_missing_required_feature() -> None:
    df = pd.DataFrame(
        {
            "budget": [1000, 1000],
            "revenue": [5000, 5000],
            "runtime": [None, 100],
        }
    )
    out = clean(df, required_feature_columns=["runtime"])
    assert len(out) == 1
    assert out["runtime"].iloc[0] == 100


def test_clean_treats_zero_as_missing_for_required_numeric_feature() -> None:
    df = pd.DataFrame(
        {
            "budget": [1000, 1000],
            "revenue": [5000, 5000],
            "tmdb_popularity": [0.0, 12.5],
        }
    )
    out = clean(df, required_feature_columns=["tmdb_popularity"])
    assert len(out) == 1
    assert out["tmdb_popularity"].iloc[0] == 12.5


# ---- Rule 3-4: ML rating scale (x2) + per-movie aggregation --------------------


def test_ml_rating_aggregation_scales_by_two_and_averages() -> None:
    ratings = pd.DataFrame({"movieId": [1, 1, 1, 2], "rating": [3.0, 4.0, 5.0, 2.0]})
    agg = aggregate_ml_ratings(ratings)
    row1 = agg[agg.movieId == 1].iloc[0]
    # (3+4+5)/3 = 4.0 on the 0-5 scale -> x2 = 8.0 on the 0-10 scale
    assert row1["ml_vote_count"] == 3
    assert row1["ml_vote_average"] == pytest.approx(8.0)
    row2 = agg[agg.movieId == 2].iloc[0]
    assert row2["ml_vote_count"] == 1
    assert row2["ml_vote_average"] == pytest.approx(4.0)  # 2.0 * 2


def test_ml_rating_aggregation_single_rating_edge_case(ratings: pd.DataFrame) -> None:
    agg = aggregate_ml_ratings(ratings)
    counts = agg.set_index("movieId")["ml_vote_count"]
    assert (counts == 1).any(), "fixture's single-rating movie should aggregate to count 1"


# ---- Rule 5: combined vote_count (sum) / vote_average (weighted mean) ---------


def test_combine_vote_features_hand_computed_pin() -> None:
    df = pd.DataFrame(
        {
            "tmdb_vote_average": [8.0],
            "tmdb_vote_count": [100.0],
            "ml_vote_average": [6.0],
            "ml_vote_count": [50.0],
        }
    )
    out = combine_vote_features(df)
    # vote_count = 100 + 50 = 150
    # vote_average = (8*100 + 6*50) / 150 = (800 + 300) / 150 = 1100/150 = 7.3333...
    assert out["vote_count"].iloc[0] == pytest.approx(150.0)
    assert out["vote_average"].iloc[0] == pytest.approx(1100.0 / 150.0)


def test_combine_vote_features_handles_zero_ml_votes() -> None:
    df = pd.DataFrame(
        {
            "tmdb_vote_average": [7.5],
            "tmdb_vote_count": [200.0],
            "ml_vote_average": [pd.NA],
            "ml_vote_count": [pd.NA],
        }
    )
    out = combine_vote_features(df)
    assert out["vote_count"].iloc[0] == pytest.approx(200.0)
    assert out["vote_average"].iloc[0] == pytest.approx(7.5)


# ---- Rule 6: genre intersection -------------------------------------------------


def test_genre_intersection_basic() -> None:
    tmdb_raw = (
        '[{"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"}, {"id": 14, "name": "Fantasy"}]'
    )
    ml_raw = "Adventure|Fantasy|IMAX"
    assert genre_intersection(tmdb_raw, ml_raw) == ["Adventure", "Fantasy"]


def test_genre_intersection_no_genres_listed_sentinel() -> None:
    tmdb_raw = '[{"id": 28, "name": "Action"}]'
    ml_raw = "(no genres listed)"
    assert genre_intersection(tmdb_raw, ml_raw) == []


def test_genre_intersection_empty_tmdb_genres() -> None:
    assert genre_intersection("[]", "Action|Comedy") == []


# ---- Full pipeline smoke (row count is recorded, not asserted, per W1-03 test req 2) --


def test_full_pipeline_runs_on_fixtures_and_excludes_labels(
    tmdb_movies: pd.DataFrame,
    tmdb_credits: pd.DataFrame,
    links: pd.DataFrame,
    ml_movies: pd.DataFrame,
    ratings: pd.DataFrame,
) -> None:
    out = build_hollywood_features(tmdb_movies, tmdb_credits, links, ml_movies, ratings)
    label_like = {
        "made_more_than_2x_budget",
        "performance_class",
        "failure",
        "mild_success",
        "success",
        "great_success",
        "missing_data",
    }
    assert not (label_like & set(out.columns)), "W1-03 output must not contain label columns"
    assert list(out.columns) == [
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
    assert out["title"].notna().all()
    assert "budget" in out.columns and "revenue" in out.columns
    assert (out["budget"] > 0).all()
    assert (out["revenue"] > 0).all()
