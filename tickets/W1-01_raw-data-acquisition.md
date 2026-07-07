# W1-01 — Raw data acquisition and provenance

**Wave:** W1. **Blocked by:** — (may start day 1). **Blocks:** W1-02, W1-03.
**Binding spec sections:** §4.1 (sources).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

Kaggle datasets drift across versions, and the reference counts in spec §4.3 are the project's only anchor to
the published work. Provenance recorded on day 1 is cheap; reconstructing it in week 6 when counts don't
match is forensic.

## Grounding (read before starting)

- Spec §4.1. Kaggle: TMDb 5000 (`tmdb_5000_movies.csv`, `tmdb_5000_credits.csv`); MovieLens 20M (`links.csv`,
  `movies.csv`, `ratings.csv`).

## Specification

- **S1.** Acquire both datasets; document the expected local layout (raw files stay OUT of git).
- **S2.** `data/DATA_PROVENANCE.md`: dataset versions/URLs, download dates, per-file SHA-256 checksums, row
  counts per file.
- **S3.** Commit small fixture excerpts (~50 rows per file, spanning edge cases: zero budgets, missing
  links) for downstream unit tests. **The repo is PUBLIC (index v1.9):** every committed excerpt must comply
  with its source dataset's license/ToS — keep excerpts minimal and record source + license in
  `DATA_PROVENANCE.md`.

## Forbidden shortcuts

- "It's just Kaggle" — no checksums, no ticket.
- Committing raw data or oversized fixtures.

## Test requirements

1. A checksum-verification script/test: recomputes and matches `DATA_PROVENANCE.md` for locally present files
   (skips with a named reason when files absent, e.g. CI).
2. Fixture excerpts load and carry their documented edge cases.

## Acceptance criteria

- Both datasets on disk, provenance + checksums recorded, fixtures committed.
