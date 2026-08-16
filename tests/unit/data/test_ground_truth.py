"""W1-02 test requirements.

1. Reference table loads with the §4.2 columns; numeric/binary sanity assertions
   (`performance_class` in {-1,0,1,2,3}); counts recorded.
2. A committed ~50-row reference excerpt spanning all performance classes.

Both requirements are satisfied here *as amended by the stakeholder's 2026-08-14 build-scope
ruling* (see `wocbots.data.ground_truth` module docstring): the reference table has no label
columns to sanity-check or span, because no independent antevorta-db extraction was performed
under that ruling. Test 1's `performance_class` pin and test 2's "spans all performance
classes" requirement are therefore encoded here as explicit, named skips (not silently
dropped) pointing at DATA_PROVENANCE.md section 5, so a future session with real label access
knows exactly what to fill in.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from wocbots.data.ground_truth import (
    LABEL_COLUMNS,
    REFERENCE_FEATURE_COLUMNS,
    ReferenceExtractionResult,
    extract_reference,
    write_excerpt,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_ROOT = Path(__file__).resolve().parents[2] / "fixtures"
SQLITE_ENV_HINT = (
    "movies.sqlite is the stakeholder-supplied ground-truth file (W1-02 S1); not committed to the repo."
)


@pytest.fixture()
def reference_sqlite_path() -> Path:
    # Anchored at the repo root, not cwd: pytest is not guaranteed to run from there.
    candidate = REPO_ROOT / "data" / "raw" / "movies.sqlite"
    if not candidate.exists():
        pytest.skip(f"{candidate} not present locally. {SQLITE_ENV_HINT}")
    return candidate


def _synthetic_reference(n: int = 60) -> pd.DataFrame:
    """A stand-in reference table with the same column set as the real one, plus one
    duplicate-tmdbId pair. Lets the extraction/excerpt logic be exercised in CI, where
    `movies.sqlite` will never exist."""
    df = pd.DataFrame(
        {
            "tmdbId": list(range(n)),
            "movieId": list(range(1000, 1000 + n)),
            "budget": [float(i * 1_000_000) for i in range(n)],
            "revenue": [float(i * 2_500_000) for i in range(n)],
            "runtime": [90.0 + i for i in range(n)],
            "tmdb_popularity": [float(i) for i in range(n)],
            "tmdb_vote_average": [5.0 + (i % 5) * 0.1 for i in range(n)],
            "tmdb_vote_count": [10 + i for i in range(n)],
            "ml_vote_average": [4.0 + (i % 7) * 0.1 for i in range(n)],
            "ml_vote_count": [float(20 + i) for i in range(n)],
            "vote_average": [4.5 + (i % 3) * 0.1 for i in range(n)],
            "vote_count": [float(30 + i) for i in range(n)],
            "genres": ['["Drama"]'] * n,
        }
    )
    # The duplicate-tmdbId artifact the real file carries, reproduced so the excerpt
    # selection can be pinned on it.
    return pd.concat([df, df.iloc[[0]]], ignore_index=True)


def _write_sqlite(df: pd.DataFrame, path: Path, table_name: str = "movies") -> Path:
    con = sqlite3.connect(path)
    try:
        df.to_sql(table_name, con, index=False)
    finally:
        con.close()
    return path


def test_extract_reference_records_counts_and_duplicates(tmp_path: Path) -> None:
    df = _synthetic_reference()
    result = extract_reference(_write_sqlite(df, tmp_path / "movies.sqlite"))

    assert result.row_count == len(df)
    assert result.duplicate_tmdb_ids == 1
    assert set(result.null_counts) == set(result.table.columns)
    assert result.zero_counts["budget"] == 2  # the i == 0 row, plus its duplicate
    assert result.class_distribution == {}


def test_extract_reference_rejects_negative_numeric_values(tmp_path: Path) -> None:
    """The bound check must survive `python -O`, so it raises rather than asserting."""
    df = _synthetic_reference()
    df.loc[3, "revenue"] = -1.0
    path = _write_sqlite(df, tmp_path / "negative.sqlite")

    with pytest.raises(ValueError, match="revenue has negative values"):
        extract_reference(path)


def test_extract_reference_rejects_non_identifier_table_name(tmp_path: Path) -> None:
    path = _write_sqlite(_synthetic_reference(), tmp_path / "movies.sqlite")
    with pytest.raises(ValueError, match="bare SQL identifier"):
        extract_reference(path, table_name="movies; drop table movies")


def test_write_excerpt_keeps_the_duplicate_rows_and_respects_n(tmp_path: Path) -> None:
    """The duplicate pair is the point of the excerpt's data-quality claim — taking it
    after a full-size decile sample and truncating to `n` silently dropped all of it.
    """
    df = _synthetic_reference()
    result = ReferenceExtractionResult(
        table=df,
        source_path=tmp_path / "movies.sqlite",
        row_count=len(df),
        missing_columns=(),
        null_counts={},
        zero_counts={},
        duplicate_tmdb_ids=1,
        duplicate_movie_ids=1,
    )
    out = write_excerpt(result, tmp_path / "excerpt.csv", n=50)
    excerpt = pd.read_csv(out)

    assert len(excerpt) <= 50
    assert excerpt["tmdbId"].duplicated().sum() == 1
    assert excerpt["budget"].max() > excerpt["budget"].median()  # spans the budget range


def test_reference_table_loads_feature_columns(reference_sqlite_path: Path) -> None:
    result = extract_reference(reference_sqlite_path)
    for col in REFERENCE_FEATURE_COLUMNS:
        assert col in result.table.columns, f"expected feature column {col!r} missing from reference table"


def test_reference_table_has_no_negative_numeric_values(reference_sqlite_path: Path) -> None:
    result = extract_reference(reference_sqlite_path)
    for col in ("budget", "revenue", "runtime"):
        assert (result.table[col] >= 0).all()


def test_reference_counts_recorded(reference_sqlite_path: Path) -> None:
    result = extract_reference(reference_sqlite_path)
    assert result.row_count == len(result.table)
    assert set(result.null_counts) == set(result.table.columns)
    assert result.duplicate_tmdb_ids >= 0


@pytest.mark.skip(
    reason=(
        "BLOCKED per DATA_PROVENANCE.md section 5 / stakeholder ruling 2026-08-14: no "
        "performance_class column exists in the supplied ground-truth file (labels were not "
        "extracted -- see ground_truth.py module docstring). Un-skip once a real label source "
        "is supplied and assert result.table['performance_class'].isin([-1, 0, 1, 2, 3]).all()."
    )
)
def test_performance_class_domain_pin() -> None:
    raise AssertionError("should not run while skipped")


def test_committed_excerpt_loads_and_has_expected_shape() -> None:
    excerpt_path = FIXTURES_ROOT / "w1_02_reference" / "movies_reference_excerpt_50.csv"
    assert excerpt_path.exists(), "committed W1-02 reference excerpt is missing"
    df = pd.read_csv(excerpt_path)
    assert 1 <= len(df) <= 50
    for col in REFERENCE_FEATURE_COLUMNS:
        assert col in df.columns


@pytest.mark.skip(
    reason=(
        "BLOCKED per DATA_PROVENANCE.md section 5: the ticket's test requirement 2 asks for an "
        "excerpt 'spanning all performance classes', but no performance_class/label columns "
        "exist in the supplied file under the 2026-08-14 build-scope ruling. The committed "
        "excerpt instead spans budget deciles + the one known duplicate-tmdbId pair (see "
        "write_excerpt's docstring). Un-skip and assert class coverage once labels exist."
    )
)
def test_excerpt_spans_all_performance_classes() -> None:
    raise AssertionError("should not run while skipped")


def test_label_columns_are_explicitly_absent_not_fabricated(reference_sqlite_path: Path) -> None:
    """Guards against a future session silently inventing label values to make S2 'pass'."""
    result = extract_reference(reference_sqlite_path)
    for col in LABEL_COLUMNS:
        assert col not in result.table.columns
