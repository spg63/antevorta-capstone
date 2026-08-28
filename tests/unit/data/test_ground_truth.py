"""W1-02 pins for Python-built SQLite and feature-reference artifacts."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from wocbots.data.ground_truth import (
    DATABASE_TABLE_NAMES,
    REFERENCE_FEATURE_COLUMNS,
    SourceTables,
    build_movies_sqlite,
    extract_reference,
    load_reference_sqlite,
    write_excerpt,
    write_reference_manifest,
    write_versioned_reference,
)

FIXTURES_ROOT = Path(__file__).resolve().parents[2] / "fixtures"


@pytest.fixture()
def feature_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "tmdbId": [10, 11, 11],
            "movieId": [100, 101, 101],
            "title": ["One", "Two", "Two duplicate"],
            "budget": [100.0, 200.0, 300.0],
            "revenue": [500.0, 0.0, 900.0],
            "runtime": [90.0, 0.0, 120.0],
            "tmdb_popularity": [1.0, 2.0, 3.0],
            "tmdb_vote_average": [7.0, 8.0, 9.0],
            "tmdb_vote_count": [10.0, 20.0, 30.0],
            "ml_vote_average": [6.0, 7.0, 8.0],
            "ml_vote_count": [1.0, 0.0, 3.0],
            "vote_average": [6.5, 8.0, 8.5],
            "vote_count": [11.0, 20.0, 33.0],
            "genres": ['["Drama"]', '["Comedy"]', '["Drama", "Mystery"]'],
        }
    )


@pytest.fixture()
def source_tables() -> SourceTables:
    tmdb_movie = {
        "budget": 100,
        "genres": '[{"name":"Drama"}]',
        "homepage": None,
        "id": 10,
        "keywords": "[]",
        "original_language": "en",
        "original_title": "One",
        "overview": "Overview",
        "popularity": 1.0,
        "production_companies": "[]",
        "production_countries": "[]",
        "release_date": "2000-01-01",
        "revenue": 500,
        "runtime": 90.0,
        "spoken_languages": "[]",
        "status": "Released",
        "tagline": None,
        "title": "One",
        "vote_average": 7.0,
        "vote_count": 10,
    }
    return SourceTables(
        links=pd.DataFrame({"movieId": [100, 101], "imdbId": [1, 2], "tmdbId": [10, None]}),
        movies=pd.DataFrame({"movieId": [100], "title": ["One"], "genres": ["Drama"]}),
        ratings=pd.DataFrame(
            {"userId": [1], "movieId": [100], "rating": [3.5], "timestamp": ["2005-04-02 23:53:47"]}
        ),
        tmdb_movies=pd.DataFrame([tmdb_movie]),
        tmdb_credits=pd.DataFrame({"movie_id": [10], "title": ["One"], "cast": ["[]"], "crew": ["[]"]}),
    )


def test_build_round_trip_preserves_order_and_values(feature_frame: pd.DataFrame, tmp_path: Path) -> None:
    sqlite_path = tmp_path / "movies.sqlite"
    result = build_movies_sqlite(feature_frame, sqlite_path)

    loaded = load_reference_sqlite(sqlite_path)

    assert result.table_name == "movies"
    assert result.columns == REFERENCE_FEATURE_COLUMNS
    assert result.row_count == len(feature_frame)
    assert len(result.sha256) == 64
    assert list(loaded.columns) == list(REFERENCE_FEATURE_COLUMNS)
    assert "index" not in loaded.columns
    pd.testing.assert_frame_equal(loaded, feature_frame, check_dtype=False)


def test_build_retains_five_source_tables_and_required_indexes(
    feature_frame: pd.DataFrame, source_tables: SourceTables, tmp_path: Path
) -> None:
    sqlite_path = tmp_path / "movies.sqlite"
    build_movies_sqlite(feature_frame, sqlite_path, source_tables=source_tables)

    connection = sqlite3.connect(sqlite_path)
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        indexes = {
            row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
        }
        link_row = connection.execute(
            "SELECT movie_id, imdb_id, tmdb_id FROM movielens_links WHERE movie_id = 101"
        ).fetchone()
        rating_row = connection.execute(
            "SELECT rated_at FROM movielens_ratings WHERE movie_id = 100"
        ).fetchone()
    finally:
        connection.close()

    assert tables == set(DATABASE_TABLE_NAMES)
    assert {"idx_movielens_links_tmdb_id", "idx_movielens_ratings_movie_id", "idx_movies_tmdb_id"} <= indexes
    assert link_row == (101, 2, None)
    assert rating_row == ("2005-04-02 23:53:47",)


@pytest.mark.parametrize(
    ("transform", "message"),
    [
        (lambda frame: frame.drop(columns=["title"]), "feature columns"),
        (lambda frame: frame.assign(extra=1), "feature columns"),
        (lambda frame: frame.loc[:, list(reversed(frame.columns))], "feature columns"),
    ],
)
def test_build_rejects_schema_contract_changes_before_replacing_target(
    feature_frame: pd.DataFrame,
    tmp_path: Path,
    transform: Callable[[pd.DataFrame], pd.DataFrame],
    message: str,
) -> None:
    sqlite_path = tmp_path / "movies.sqlite"
    initial = build_movies_sqlite(feature_frame, sqlite_path)

    with pytest.raises(ValueError, match=message):
        build_movies_sqlite(transform(feature_frame), sqlite_path)

    assert (
        build_movies_sqlite(load_reference_sqlite(sqlite_path), tmp_path / "copy.sqlite").sha256
        == initial.sha256
    )


def test_extract_records_exact_counts_and_duplicate_ids(feature_frame: pd.DataFrame, tmp_path: Path) -> None:
    sqlite_path = tmp_path / "movies.sqlite"
    build_movies_sqlite(feature_frame, sqlite_path)

    result = extract_reference(sqlite_path)

    assert result.row_count == 3
    assert result.null_counts == {column: 0 for column in REFERENCE_FEATURE_COLUMNS}
    assert result.zero_counts["revenue"] == 1
    assert result.zero_counts["runtime"] == 1
    assert result.zero_counts["ml_vote_count"] == 1
    assert result.duplicate_tmdb_ids == 1
    assert result.duplicate_movie_ids == 1


def test_invalid_or_noncanonical_table_name_is_rejected(feature_frame: pd.DataFrame, tmp_path: Path) -> None:
    sqlite_path = tmp_path / "movies.sqlite"
    build_movies_sqlite(feature_frame, sqlite_path)

    with pytest.raises(ValueError, match="table_name"):
        load_reference_sqlite(sqlite_path, "other_table")
    with pytest.raises(ValueError, match="table_name"):
        load_reference_sqlite(sqlite_path, "movies; DROP TABLE movies;")


def test_reference_csv_and_manifest_are_deterministic(feature_frame: pd.DataFrame, tmp_path: Path) -> None:
    sqlite_path = tmp_path / "movies.sqlite"
    build_movies_sqlite(feature_frame, sqlite_path)
    result = extract_reference(sqlite_path)

    first_csv = write_versioned_reference(result, tmp_path / "first", "v1")
    second_csv = write_versioned_reference(result, tmp_path / "second", "v1")
    manifest = write_reference_manifest(result, tmp_path / "reference.json")

    assert first_csv.read_bytes() == second_csv.read_bytes()
    assert '"row_count": 3' in manifest.read_text()
    assert '"source_sha256"' in manifest.read_text()


def test_excerpt_is_deterministic_and_preserves_feature_schema(
    feature_frame: pd.DataFrame, tmp_path: Path
) -> None:
    sqlite_path = tmp_path / "movies.sqlite"
    build_movies_sqlite(feature_frame, sqlite_path)
    result = extract_reference(sqlite_path)

    first = write_excerpt(result, tmp_path / "first.csv", seed=7)
    second = write_excerpt(result, tmp_path / "second.csv", seed=7)

    assert first.read_bytes() == second.read_bytes()
    excerpt = pd.read_csv(first)
    assert 1 <= len(excerpt) <= 50
    assert list(excerpt.columns) == list(REFERENCE_FEATURE_COLUMNS)


def test_committed_excerpt_loads_with_the_w1_03_feature_schema() -> None:
    excerpt_path = FIXTURES_ROOT / "w1_02_reference" / "movies_reference_excerpt_50.csv"
    dataframe = pd.read_csv(excerpt_path)

    assert 1 <= len(dataframe) <= 50
    assert list(dataframe.columns) == list(REFERENCE_FEATURE_COLUMNS)
