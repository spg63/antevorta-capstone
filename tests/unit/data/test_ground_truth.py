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

from pathlib import Path

import pandas as pd
import pytest

from wocbots.data.ground_truth import (
    LABEL_COLUMNS,
    REFERENCE_FEATURE_COLUMNS,
    extract_reference,
)

FIXTURES_ROOT = Path(__file__).resolve().parents[2] / "fixtures"
SQLITE_ENV_HINT = "movies.sqlite is the stakeholder-supplied ground-truth file (W1-02 S1); not committed to the repo."


@pytest.fixture()
def reference_sqlite_path() -> Path:
    candidate = Path("data/raw/movies.sqlite")
    if not candidate.exists():
        pytest.skip(f"{candidate} not present locally. {SQLITE_ENV_HINT}")
    return candidate


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
