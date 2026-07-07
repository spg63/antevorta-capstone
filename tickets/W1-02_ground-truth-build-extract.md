# W1-02 — antevorta-db ground-truth build and reference extraction

**Wave:** W1. **Blocked by:** W1-01 (raw data). **Blocks:** W1-04 (validation targets).
**Binding spec sections:** §4.2 (Path A — antevorta-db as ground truth).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The antevorta-db output is the reference ETL — the artifact that lets W1-04 prove the Python pipeline is
*right* rather than merely plausible. It is consulted as ground truth and then retires to validation duty.

## Grounding (read before starting)

- Spec §4.2. `antevorta-db`: `configs/Finals.kt` (table names), `configs/DBLocator.kt` +
  `RawDataLocator.kt` (hardcoded paths — adjusting them is expected), `dbcreator/hollywood/`
  (Facilitator/Pusher ingestion), `columnsAndKeys/TMDBMovies.kt` (`columnNames()` — the joined schema).

## Specification

- **S1.** Run the antevorta-db Hollywood ingestion (JVM build, path constants adjusted) to produce the SQLite
  DB with the joined `movies` table. If the build proves disproportionate, the stakeholder can supply the
  built file — either way the deliverable is the FILE plus a record of how it was produced.
- **S2.** Extract from Python to a versioned reference parquet/CSV: all §4.2 feature columns + the label
  columns (`made_more_than_2x_budget`, `performance_class`, `failure`, `mild_success`, `success`,
  `great_success`, `missing_data`). Record row count, class distribution, per-column null/zero counts.

## Forbidden shortcuts

- Editing antevorta-db ingestion LOGIC (path constants only) — a "fixed" ground truth validates nothing.

## Test requirements

1. Reference table loads with the §4.2 columns; numeric/binary sanity assertions (`performance_class` ∈
   {−1,0,1,2,3}); counts recorded.
2. A committed ~50-row reference excerpt spanning all performance classes.

## Acceptance criteria

- Ground-truth SQLite produced (or provenance-documented as supplied); reference table + counts versioned —
  W1-04's validation targets exist.
