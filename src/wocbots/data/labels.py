"""Hollywood labels and reconciliation against the reference-derived threshold.

The shipped rule is strict 2×. The comparison threshold is 1.5×, with the reference
code's exact-5× fall-through corrected as directed; it is not an exact reproduction
of the reference column and does not independently validate the input dataset.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


def variant_a_label(df: pd.DataFrame, budget_col: str = "budget", revenue_col: str = "revenue") -> pd.Series:
    """Spec §4.3.7's stated rule: 1 if revenue > 2 * budget, else 0.

    `revenue == 2 * budget` is deliberately NOT a success (strict `>`), a documented
    boundary choice pinned by `test_boundary_exactly_2x_budget_is_not_success`.
    """
    return (df[revenue_col] > 2 * df[budget_col]).astype(int)


def variant_b_from_reference(
    reference_df: pd.DataFrame, id_col: str, reference_label_col: str = "made_more_than_2x_budget"
) -> pd.Series:
    """Extract the reference's own precomputed label column, indexed by `id_col`.

    Not exercised by any test in this session (blocked — no reference table exists yet).
    Kept here, ready to call, so unblocking W1-02 doesn't require touching W1-04's code.
    """
    return reference_df.set_index(id_col)[reference_label_col]


def class_balance_pct(labels: pd.Series) -> pd.Series:
    """Class balance as percentages, index-sorted (0 then 1) for stable comparison."""
    return (labels.value_counts(normalize=True).sort_index() * 100).round(2)


def reference_threshold_label(
    df: pd.DataFrame, budget_col: str = "budget", revenue_col: str = "revenue"
) -> pd.Series:
    """Reference-derived comparison with the exact-5× fall-through corrected."""
    return (df[revenue_col] > 1.5 * df[budget_col]).astype(int)


def label_movies_sqlite(sqlite_path: Path) -> int:
    """Atomically populate the W1-04 label on the computed movies table.

    Re-running refreshes every row using the same strict threshold. Invalid financial
    values abort the transaction rather than being silently assigned a label.
    """
    if not sqlite_path.is_file():
        raise FileNotFoundError(sqlite_path)
    with sqlite3.connect(sqlite_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        frame = pd.read_sql_query("SELECT rowid AS _rowid, budget, revenue FROM movies", connection)
        if frame.empty:
            raise ValueError("movies table must not be empty")
        for column in ("budget", "revenue"):
            values = pd.to_numeric(frame[column], errors="raise")
            if not np.isfinite(values).all() or (values <= 0).any():
                raise ValueError(f"{column} must contain finite positive values")
        columns = {row[1] for row in connection.execute('PRAGMA table_info("movies")')}
        if "label" not in columns:
            connection.execute("ALTER TABLE movies ADD COLUMN label INTEGER CHECK (label IN (0, 1))")
        labels = variant_a_label(frame)
        connection.executemany(
            "UPDATE movies SET label = ? WHERE rowid = ?",
            [(int(label), int(row_id)) for label, row_id in zip(labels, frame["_rowid"], strict=True)],
        )
        return len(frame)


def reconcile_labels(df: pd.DataFrame) -> dict[str, object]:
    """Compare both definitions on the same valid W1-03 rows without rounding."""
    if df.empty:
        raise ValueError("reconciliation requires at least one row")
    for column in ("budget", "revenue"):
        values = pd.to_numeric(df[column], errors="raise")
        if not np.isfinite(values).all() or (values <= 0).any():
            raise ValueError(f"{column} must contain finite positive values")
    labels_a = variant_a_label(df)
    labels_b = reference_threshold_label(df)

    def balance(labels: pd.Series) -> dict[str, object]:
        positives = int(labels.sum())
        counts = [len(labels) - positives, positives]
        percentages = [100.0 * count / len(labels) for count in counts]
        matches = all(
            abs(actual - target) <= 1.0 for actual, target in zip(percentages, (47.5, 52.5), strict=True)
        )
        return {"counts": counts, "percentages": percentages, "matches_published": matches}

    return {
        "row_count": len(df),
        "variant_a": balance(labels_a),
        "reference_threshold_corrected": balance(labels_b),
        "disagreement_rows": int((labels_a != labels_b).sum()),
    }
