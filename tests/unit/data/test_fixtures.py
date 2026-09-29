"""W1-01 test requirement 2: fixture excerpts load and carry their documented edge cases."""

from pathlib import Path

import pandas as pd
import pytest

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
FIXTURE_HEADERS = {
    "tmdb5000/tmdb_5000_movies_fixture.csv": [
        "budget",
        "genres",
        "homepage",
        "id",
        "keywords",
        "original_language",
        "original_title",
        "overview",
        "popularity",
        "production_companies",
        "production_countries",
        "release_date",
        "revenue",
        "runtime",
        "spoken_languages",
        "status",
        "tagline",
        "title",
        "vote_average",
        "vote_count",
    ],
    "tmdb5000/tmdb_5000_credits_fixture.csv": ["movie_id", "title", "cast", "crew"],
    "movielens20m/link_fixture.csv": ["movieId", "imdbId", "tmdbId"],
    "movielens20m/movie_fixture.csv": ["movieId", "title", "genres"],
    "movielens20m/rating_fixture.csv": ["userId", "movieId", "rating", "timestamp"],
}


@pytest.mark.parametrize("relative_path, expected_header", FIXTURE_HEADERS.items())
def test_fixtures_have_expected_schema_and_remain_small(
    relative_path: str, expected_header: list[str]
) -> None:
    fixture = FIXTURES / relative_path
    df = pd.read_csv(fixture)

    assert list(df.columns) == expected_header
    assert len(df) <= 60, f"fixture grew beyond the 60-record W1-01 excerpt ceiling: {fixture}"


def test_tmdb_movies_fixture_has_zero_budget_and_zero_revenue_rows() -> None:
    df = pd.read_csv(FIXTURES / "tmdb5000" / "tmdb_5000_movies_fixture.csv")
    assert (df["budget"] == 0).any(), "fixture must include a zero-budget row (§4.3.2)"
    assert (df["revenue"] == 0).any(), "fixture must include a zero-revenue row (§4.3.2)"
    assert ((df["budget"] > 0) & (df["revenue"] > 0)).any(), "fixture needs a usable row too"


def test_tmdb_credits_fixture_keys_match_movies_fixture() -> None:
    movies = pd.read_csv(FIXTURES / "tmdb5000" / "tmdb_5000_movies_fixture.csv")
    credits = pd.read_csv(FIXTURES / "tmdb5000" / "tmdb_5000_credits_fixture.csv")
    assert set(credits["movie_id"]) <= set(movies["id"])


def test_link_fixture_has_null_tmdbid_row() -> None:
    df = pd.read_csv(FIXTURES / "movielens20m" / "link_fixture.csv")
    assert df["tmdbId"].isna().any(), "fixture must include an unmapped (null tmdbId) row (§4.3.1 drop case)"
    assert df["tmdbId"].notna().any(), "fixture needs mappable rows too"


def test_movie_fixture_has_no_genres_listed_row() -> None:
    df = pd.read_csv(FIXTURES / "movielens20m" / "movie_fixture.csv")
    assert (df["genres"] == "(no genres listed)").any()


def test_rating_fixture_has_single_rating_and_multi_rating_movies() -> None:
    df = pd.read_csv(FIXTURES / "movielens20m" / "rating_fixture.csv")
    counts = df.groupby("movieId").size()
    assert (counts == 1).any(), "fixture must include a movie with exactly one rating (§4.3.4 edge case)"
    assert (counts > 1).any(), "fixture must include a movie with multiple ratings"
