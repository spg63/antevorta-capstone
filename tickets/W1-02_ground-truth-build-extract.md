# W1-02 — Python SQLite build and reference extraction

**Wave:** W1. **Blocked by:** W1-01 (raw data). **Blocks:** W1-04 (validation targets).
**Binding spec sections:** §4.2 (SQLite reference workflow), as amended by the stakeholder ruling below.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The SQLite output is the durable, language-neutral reference artifact for the Hollywood data pipeline. It
retains five raw-source tables plus one reproducibly built derived feature table, letting W1-04 and later
tickets consume a provenance-recorded artifact without making the database a runtime dependency.

## Stakeholder ruling (2026-08-17)

`antevorta-db` is **not required** to create this ticket's SQLite file. Build it with the project's reliable
Python data stack: load the five stakeholder-provided raw sources into source tables, construct the W1-03
feature table from those inputs, and write it as the derived `movies` table through Python's standard-library
`sqlite3` driver. The canonical output is `data/processed/movies.sqlite`; do not write the legacy raw-data
location. This supersedes the ticket's earlier JVM-build requirement and former one-table design.

The resulting SQLite is a canonical Python-pipeline artifact, **not an independent validation oracle** for
that same pipeline. W1-04 must not claim self-comparison as independent ETL validation. Label materialization
remains W1-04's responsibility; W1-02 must not fabricate the legacy `antevorta-db` label columns.

## Grounding (read before starting)

- Spec §4.2's SQLite/Python-reader workflow.
- W1-01 provenance and raw-data layout.
- W1-03's `build_hollywood_features` output contract and `OUTPUT_COLUMNS`.
- `pandas.DataFrame.to_sql` with the standard-library `sqlite3` driver; no JVM build and no new database
  dependency.

## Specification

- **S1.** Build SQLite deterministically with five source tables and the W1-03-derived `movies` table. Record
  raw-input provenance, source/derived schemas and counts, writer/library versions, and SQLite SHA-256. The
  deliverable is the file plus the record of how it was produced.
- **S2.** Extract the W1-03 feature/provenance columns from Python to a versioned reference parquet/CSV and
  record row count, per-column null/zero counts, and duplicate-identity counts. Do not create label columns
  in this ticket; after W1-04 supplies the ratified label, its output may be recorded separately with its
  own class distribution.

## Forbidden shortcuts

- Reimplementing or altering W1-03 transformation logic in the SQLite writer. The writer serializes the
  already-built feature table unchanged; it does not join, clean, impute, deduplicate, or label data.
- Claiming this Python-built database independently validates the Python ETL.

## Test requirements

1. SQLite `movies` loads with the W1-03 output columns; schema, row count, null/zero counts, and duplicate
   identity counts equal the extracted reference record.
2. Rebuilding from the same verified inputs produces the same table/schema and canonical extracted content.
3. A committed ~50-row feature reference excerpt loads with all feature/provenance columns. Class-coverage
   assertions belong to W1-04 once labels exist.

## Acceptance criteria

- Python-built SQLite produced with reproducible provenance; feature reference table + counts versioned.
- W1-04 has the canonical feature artifact it needs, and its label/validation scope explicitly does not
  misrepresent this same-pipeline SQLite as independent ground truth.
