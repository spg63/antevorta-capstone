"""W1-04 label boundary and reconciliation tests."""

import sqlite3
from pathlib import Path
from typing import cast

import pandas as pd
import pytest

from wocbots.data.ground_truth import load_reference_sqlite
from wocbots.data.labels import (
    class_balance_pct,
    label_movies_sqlite,
    reconcile_labels,
    reference_threshold_label,
    variant_a_label,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
FEATURE_SQLITE = REPO_ROOT / "data" / "processed" / "movies.sqlite"


def test_boundary_exactly_2x_budget_is_not_success() -> None:
    df = pd.DataFrame({"budget": [1000.0], "revenue": [2000.0]})
    labels = variant_a_label(df)
    assert labels.iloc[0] == 0


def test_boundary_just_above_2x_budget_is_success() -> None:
    df = pd.DataFrame({"budget": [1000.0], "revenue": [2000.01]})
    labels = variant_a_label(df)
    assert labels.iloc[0] == 1


def test_boundary_just_below_2x_budget_is_not_success() -> None:
    df = pd.DataFrame({"budget": [1000.0], "revenue": [1999.99]})
    labels = variant_a_label(df)
    assert labels.iloc[0] == 0


def test_class_balance_pct_is_percentages_rounded_to_two_places() -> None:
    """Exact-arithmetic pin on the mechanism the shipped-balance test below relies on:
    3 zeros / 4 rows -> 75.0 / 25.0, index-sorted 0 then 1."""
    balance = class_balance_pct(pd.Series([0, 0, 0, 1]))
    assert list(balance.index) == [0, 1]
    assert balance.loc[0] == 75.0
    assert balance.loc[1] == 25.0


@pytest.mark.skipif(
    not FEATURE_SQLITE.exists(),
    reason="Full W1-03 SQLite is a local, uncommitted dataset artifact.",
)
def test_shipped_label_balance_gate_on_local_data() -> None:
    result = reconcile_labels(load_reference_sqlite(FEATURE_SQLITE))
    balance = cast(dict[str, object], result["variant_a"])
    assert result["row_count"] == 3032
    assert balance["counts"] == [1332, 1700]
    # The session driver waived this requirement after it failed; do not claim it passed.
    assert balance["matches_published"] is False


def test_reference_comparison_boundary_and_corrected_five_times() -> None:
    df = pd.DataFrame({"budget": [100] * 6, "revenue": [149, 150, 151, 499, 500, 501]})
    assert reference_threshold_label(df).tolist() == [0, 0, 1, 1, 1, 1]


def test_reconciliation_counts_and_disagreement() -> None:
    df = pd.DataFrame({"budget": [100] * 4, "revenue": [100, 175, 200, 501]}, index=[5, 2, 7, 1])
    result = reconcile_labels(df)
    assert result["row_count"] == 4
    assert result["disagreement_rows"] == 2
    assert result["variant_a"] == {"counts": [3, 1], "percentages": [75.0, 25.0], "matches_published": False}
    assert result["reference_threshold_corrected"] == {
        "counts": [1, 3],
        "percentages": [25.0, 75.0],
        "matches_published": False,
    }


@pytest.mark.parametrize("budget,revenue", [(0, 10), (10, 0), (10, float("nan")), (float("inf"), 10)])
def test_reconciliation_rejects_invalid_rows(budget: float, revenue: float) -> None:
    with pytest.raises(ValueError):
        reconcile_labels(pd.DataFrame({"budget": [budget], "revenue": [revenue]}))


def test_reconciliation_rejects_empty() -> None:
    with pytest.raises(ValueError):
        reconcile_labels(pd.DataFrame({"budget": [], "revenue": []}))


@pytest.mark.parametrize("zeros,expected", [(46, False), (47, True), (48, True), (49, False)])
def test_published_balance_tolerance(zeros: int, expected: bool) -> None:
    df = pd.DataFrame({"budget": [100] * 100, "revenue": [100] * zeros + [300] * (100 - zeros)})
    balance = cast(dict[str, object], reconcile_labels(df)["variant_a"])
    assert balance["matches_published"] == expected


def test_sqlite_labels_are_persisted_and_refreshed(tmp_path: Path) -> None:
    path = tmp_path / "movies.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE movies (budget REAL, revenue REAL)")
        connection.executemany("INSERT INTO movies VALUES (?, ?)", [(100, 199), (100, 200), (100, 201)])
    assert label_movies_sqlite(path) == 3
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT label FROM movies ORDER BY rowid").fetchall() == [(0,), (0,), (1,)]
        connection.execute("UPDATE movies SET revenue = 500 WHERE rowid = 1")
    assert label_movies_sqlite(path) == 3
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT label FROM movies ORDER BY rowid").fetchall() == [(1,), (0,), (1,)]


def test_sqlite_invalid_values_roll_back_without_adding_column(tmp_path: Path) -> None:
    path = tmp_path / "movies.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE movies (budget REAL, revenue REAL)")
        connection.execute("INSERT INTO movies VALUES (100, NULL)")
    with pytest.raises(ValueError):
        label_movies_sqlite(path)
    with sqlite3.connect(path) as connection:
        assert [row[1] for row in connection.execute("PRAGMA table_info(movies)")] == ["budget", "revenue"]
