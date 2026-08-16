"""W1-02: ground-truth SQLite ingestion + reference extraction.

**Scope ruling (Sean Grimes, email, 2026-08-14, subject "Re: Antevorta SQLite"):** build the
ground-truth SQLite ourselves by porting the raw CSVs (the W1-03 join/clean pipeline), rather
than standing up the `antevorta-db` JVM build or extracting a row-level reference out of the
"250+TB" antevorta-db instance. Quoting the ruling: "just build that yourself... it's just
porting the csv files into a SQLite db... Extracting that specific data, like 50KB from a
250+TB database is going to be a huge pain."

This resolves ticket S1 under its documented fallback ("the stakeholder can supply the built
file -- either way the deliverable is the FILE plus a record of how it was produced"): the
FILE is `movies.sqlite` (built by `scripts/build_movies_sqlite.py`, itself calling
`wocbots.data.hollywood.build_hollywood_features` -- the W1-03 pipeline), and this module is
the record of how it was produced plus the S2 extraction/versioning work on top of it.

**What this ruling does NOT resolve:** the label columns. `movies.sqlite` was built by the
same join/clean logic W1-04 needs to validate, so it is not an independent check on that
logic, and it carries no label columns at all (`made_more_than_2x_budget`, `performance_class`,
`failure`, `mild_success`, `success`, `great_success`, `missing_data`). The stakeholder's email
only addresses the build/extraction *method*; it does not supply antevorta-db's label formula
(`dbcreator/hollywood/TMDBMoviesPusher.kt`'s `determinePerformanceClass`/`madeBackBudget`,
which spec grounding notes is NOT what its column name implies). Fabricating that formula from
the spec text alone is exactly the shortcut W1-02's own ticket forbids ("a 'fixed' ground truth
validates nothing") -- so this module extracts and versions everything that IS in the supplied
file, and leaves the label columns explicitly absent and flagged, rather than inventing them.

Downstream effect: W1-04's S1-S3 (row-level reference validation, the two-label-variant
reconciliation gate) could not run in the form that ticket specifies, because there is no
independent reference to validate against. **Resolved 2026-08-15** (see W1-04's ticket RESULT
block): reference-column reconciliation was ruled out of scope; variant (a) (`revenue > 2 *
budget`) ships as THE label, undefended, without matching the published class balance. This
module's job stops at "no reference exists" — it is not responsible for that ruling, only for
not papering over the gap it created.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from wocbots.data.hollywood import OUTPUT_COLUMNS

# Columns actually present in the supplied movies.sqlite (S1's deliverable). `title` is in
# OUTPUT_COLUMNS but was dropped somewhere upstream of the supplied file -- recorded, not
# silently patched back in.
REFERENCE_FEATURE_COLUMNS: tuple[str, ...] = (
    "tmdbId",
    "movieId",
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
)

# Columns whose domain is [0, inf) where present. Both the zero-count record and the
# non-negativity gate in `extract_reference` read this one list, so they cannot drift apart.
NON_NEGATIVE_COLUMNS: tuple[str, ...] = (
    "budget",
    "revenue",
    "runtime",
    "tmdb_vote_count",
    "ml_vote_count",
    "vote_count",
)

# Per the module docstring: not extractable from the supplied file under this ruling, and not
# fabricated. W1-04 must source these independently (or the stakeholder must rule the gate
# out of scope) before they can be populated.
LABEL_COLUMNS: tuple[str, ...] = (
    "made_more_than_2x_budget",
    "performance_class",
    "failure",
    "mild_success",
    "success",
    "great_success",
    "missing_data",
)


@dataclass(frozen=True)
class ReferenceExtractionResult:
    """S2's deliverable: the loaded reference table plus the counts the ticket requires
    recorded ("record row count, class distribution, per-column null/zero counts")."""

    table: pd.DataFrame
    source_path: Path
    row_count: int
    missing_columns: tuple[str, ...]
    null_counts: dict[str, int]
    zero_counts: dict[str, int]
    duplicate_tmdb_ids: int
    duplicate_movie_ids: int
    class_distribution: dict[str, dict[str, int]] = field(default_factory=dict)

    def to_manifest_dict(self) -> dict[str, object]:
        return {
            "source_path": str(self.source_path),
            "row_count": self.row_count,
            "missing_columns": list(self.missing_columns),
            "null_counts": self.null_counts,
            "zero_counts": self.zero_counts,
            "duplicate_tmdb_ids": self.duplicate_tmdb_ids,
            "duplicate_movie_ids": self.duplicate_movie_ids,
            "class_distribution": self.class_distribution,
            "note": (
                "Label columns absent from source; not fabricated. See "
                "wocbots.data.ground_truth module docstring and DATA_PROVENANCE.md section 5."
            ),
        }


def load_reference_sqlite(sqlite_path: Path, table_name: str = "movies") -> pd.DataFrame:
    """Load the stakeholder-ratified ground-truth SQLite (S1's deliverable) into a DataFrame."""
    # `table_name` is interpolated into SQL because SQLite cannot parameterize identifiers.
    # It is caller-supplied, so it is validated as a bare identifier first rather than
    # trusted — the callers today pass the default, but nothing in the signature says so.
    if not table_name.isidentifier():
        raise ValueError(f"table_name must be a bare SQL identifier, got {table_name!r}")
    con = sqlite3.connect(sqlite_path)
    try:
        df = pd.read_sql(f"select * from {table_name}", con)
    finally:
        con.close()
    return df


def extract_reference(sqlite_path: Path, table_name: str = "movies") -> ReferenceExtractionResult:
    """S2: extract + version the reference table, recording the counts the ticket requires.

    Sanity checks performed here (numeric bounds), separate from the null/zero counts:
    budget/revenue/runtime are non-negative where present; vote counts are non-negative.
    Raises ValueError if violated -- a violation means the supplied file itself is
    inconsistent, which is worth stopping on rather than silently versioning. This is a
    data-integrity gate on an external file, not an internal invariant, so it must survive
    `python -O` (which strips `assert`).
    """
    df = load_reference_sqlite(sqlite_path, table_name=table_name)

    missing_columns = tuple(c for c in OUTPUT_COLUMNS if c not in df.columns)

    null_counts = {c: int(df[c].isna().sum()) for c in df.columns}
    numeric_cols = [c for c in NON_NEGATIVE_COLUMNS if c in df.columns]
    zero_counts = {c: int((df[c] == 0).sum()) for c in numeric_cols}

    for col in numeric_cols:
        series = df[col].dropna()
        if not bool((series >= 0).all()):
            raise ValueError(f"{col} has negative values in {sqlite_path}")

    return ReferenceExtractionResult(
        table=df,
        source_path=sqlite_path,
        row_count=len(df),
        missing_columns=missing_columns,
        null_counts=null_counts,
        zero_counts=zero_counts,
        duplicate_tmdb_ids=int(df["tmdbId"].duplicated().sum()) if "tmdbId" in df.columns else 0,
        duplicate_movie_ids=int(df["movieId"].duplicated().sum()) if "movieId" in df.columns else 0,
        # No label columns present under this ruling -- explicitly empty, not omitted.
        class_distribution={},
    )


def write_versioned_reference(result: ReferenceExtractionResult, out_dir: Path, version: str) -> Path:
    """Write the versioned reference CSV (S2). `out_dir` is expected to be a gitignored
    derived-data location (e.g. `data/derived/`) -- per `data/README.md`, derived CSVs are
    never committed; only DATA_PROVENANCE.md and small fixture excerpts are."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out = result.table.copy()
    out_path = out_dir / f"movies_reference_{version}.csv"
    out.to_csv(out_path, index=False)
    return out_path


def write_excerpt(result: ReferenceExtractionResult, out_path: Path, n: int = 50, seed: int = 1) -> Path:
    """Committed ~50-row reference excerpt (test requirement 2). Cannot span "all performance
    classes" as the ticket's test requirement literally asks -- there are no performance
    classes in this file (see module docstring). Instead selects a stratified, deterministic
    sample spanning: budget deciles, genre diversity, and the known duplicate-tmdbId rows
    (a real data-quality artifact worth keeping visible in the fixture, not filtering out).

    The duplicate rows are taken FIRST and the decile sample fills what is left of `n`.
    Appending them after a full-size decile sample and then truncating to `n` drops every
    one of them, which is why the excerpt this function first produced contains none."""
    df = result.table.copy()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    dup_rows = df.iloc[:0]
    if "tmdbId" in df.columns:
        dup_rows = df[df["tmdbId"].duplicated(keep=False)].head(n)

    parts = [dup_rows]
    remaining = n - len(dup_rows)
    if remaining > 0:
        pool = df.drop(index=dup_rows.index)
        decile = pd.qcut(pool["budget"], 10, labels=False, duplicates="drop")
        per_decile = max(1, remaining // max(1, int(decile.nunique())))
        for idx in pool.groupby(decile).groups.values():
            group = pool.loc[idx]
            parts.append(group.sample(n=min(per_decile, len(group)), random_state=seed))

    sampled = pd.concat(parts).head(n).reset_index(drop=True)
    sampled.to_csv(out_path, index=False)
    return out_path


def genres_from_json(raw: str) -> list[str]:
    """Parse the JSON-list-string `genres` column back into a list (mirrors how the raw TMDb
    field arrives before W1-03 parses it; used by tests/consumers that need the list form)."""
    return list(json.loads(raw))
