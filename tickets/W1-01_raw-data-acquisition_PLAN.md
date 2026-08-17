# W1-01 — Raw data acquisition and provenance — IMPLEMENTATION PLAN

> **Status:** APPROVED FOR IMPLEMENTATION — repository owner, 2026-08-16. **Precedence:** `docs/WoC-Bots_Implementation_Spec.md` v1.2 > mandatory preamble > this plan > `W1-01_raw-data-acquisition.md`. A disagreement is reported, never silently reconciled.
>
> **Planning read record:** `tickets/01_MANDATORY_PREAMBLE.md`, the current-state portion of `AGENT_HANDOFF.md`, W1-01 in full, and spec §4.1 in full. The live W1 provenance module, its tests, fixtures, data README, ignore rules, and W1 dependency rows were also inspected. There was no pre-existing W1-01 plan.

## 1. Metadata

**Wave:** W1. **Blocks:** W1-02 and W1-03. **Binding specification:** spec §4.1 (the two joined public sources and their required raw files); ticket W1-01; preamble §§0, 2–6, 8–9. **Mode:** PLAN.

This is a data-provenance ticket, not an experiment: no results manifest is produced. It must nevertheless be deterministic in its committed metadata: a particular raw byte stream maps to one recorded SHA-256 and one row count.

## 2. Why this exists

The Hollywood pipeline's reference counts only mean something when the exact source bytes are known. W1-01 makes raw inputs locally verifiable while keeping the public repository free of raw datasets. Its small, licensed fixture set gives W1-03 and later unit tests representative input without converting test data into an untracked second dataset.

## 3. Decisions and required rulings

1. **Raw-data distribution is stakeholder supplied.** Follow `data/README.md`: obtain data from the stakeholder, not from an unverified web search. Do not commit an archive or any raw file. This preserves the clean-room boundary and gives the team an auditable acquisition source.
2. **Canonical local layout (recommended):** `data/raw/tmdb/tmdb_5000_movies.csv`, `data/raw/tmdb/tmdb_5000_credits.csv`, and `data/raw/movielens/{links,movies,ratings}.csv`. `data/raw/` remains gitignored. The provenance registry is the one code-level source of paths, checksums, and expected rows.
3. **Filename-alias ruling — repository owner, 2026-08-16:** retain the verified archive layout: `tmdb/{movies,credits}.csv` and `movielens/{link,movie,rating}.csv`. The record documents their relation to the spec-named Kaggle files. Do not silently rename or duplicate 690 MB of raw data.
4. **Fixture license ruling — repository owner, 2026-08-16:** the repository owner attests that they hold the required permissions for the intentionally minimal committed excerpts. Retain source and license/ToS records in `DATA_PROVENANCE.md`; any future excerpt beyond this scoped set requires a fresh authorization check.
5. **Checksum and row-count policy:** SHA-256 is streamed in fixed-size chunks; rows exclude the header. CSVs with quoted embedded newlines must be counted by CSV parsing, while the numeric MovieLens ratings file may use a byte-line count only after its format assumption is documented and tested.

## 4. Verified grounding and live-tree facts

- Spec §4.1 requires TMDb 5000 movies/credits and MovieLens 20M links/movies/ratings; `links.csv` is the crucial MovieLens-to-TMDb identity map. It also names MovieLens genome files, but W1-01's ticket only requires fixtures for the five files above; do not expand scope without a new ticket/ruling.
- `.gitignore` excludes `data/raw/` and derived data files. `data/README.md` says provenance and fixtures, not raw data, are committed.
- The live implementation already has `src/wocbots/data/provenance.py`: immutable `FileProvenance(relative_path, sha256, row_count)`, `RAW_FILES`, chunked `sha256_of(path)`, and `verify(record) -> tuple[bool, str]`. `tests/unit/data/test_provenance.py` skips absent raw files with the explicit CI reason and verifies both checksum and row count.
- The fixture tests currently pin zero budget/revenue plus a usable TMDb row; credits-to-movies keys; a null and non-null MovieLens TMDb link; no-genres-listed; and both singleton/multiple ratings. Current fixtures are small (34–51 physical lines per file, with CSV records potentially spanning lines).
- `data/DATA_PROVENANCE.md` already records source, license/ToS, acquisition date, size, SHA-256, rows, fixture semantics, and a downstream W1-02 blocker. A raw-data file must be independently rehashed and recount-verified before relying on that record.

## 5. Execution-path map

```text
stakeholder-provided source archive / approved dataset download
  -> unpack only required files beneath ignored data/raw/<dataset>/
  -> inspect headers + parse/count records
  -> stream SHA-256 of each exact raw file
  -> record acquisition source/date, source terms, canonical/approved local layout,
     size, checksum, and count in DATA_PROVENANCE.md
  -> mirror machine-checkable path/checksum/count in RAW_FILES
  -> derive minimal license-compliant excerpts in tests/fixtures/
  -> tests: raw present => hash + count must match; raw absent => named skip;
            fixtures => load and prove documented edge cases
```

The raw files are inputs only. The public repository carries the audit record and fixtures, never a copy of those inputs.

## 6. Pre-code gate

Before implementation:

1. Confirm the data owner has supplied or approved both exact datasets and that their public-fixture terms and authorization record are present.
2. Apply the ratified archive-alias layout in decision 3; amend this plan before any later layout change.
3. Check `git status --short`; preserve unrelated work (currently an untracked `tickets/W5-01_baseline-mlp_PLAN.md`).
4. Verify all five files against the planned headers before copying excerpts. Do not infer that a similarly named archive is the correct dataset.

## 7. Files and interfaces

| Path | Change | Contract |
|---|---|---|
| `data/DATA_PROVENANCE.md` | Add/update human-readable provenance. | Source URL/provider, version/date, applicable license/ToS, local layout, per-file bytes, SHA-256, and data-record count are explicit; fixtures and their edge cases are named. |
| `data/README.md` | Clarify the ignored raw-data layout only if needed. | Raw files remain out of Git; users know where to obtain/put them. |
| `.gitignore` | Verify/add narrow raw-data exclusions if absent. | Raw archives and raw datasets cannot be accidentally staged; provenance and test fixtures stay trackable. |
| `src/wocbots/data/provenance.py` | Define/update the machine-readable provenance registry and verification helpers. | `FileProvenance(relative_path: str, sha256: str, row_count: int)`; `RAW_FILES: tuple[FileProvenance, ...]`; `sha256_of(path: Path, chunk_size: int = 1 << 20) -> str`; `verify(record) -> tuple[bool, str]`. No RNG, network I/O, or data download behavior. |
| `tests/fixtures/tmdb5000/`, `tests/fixtures/movielens20m/` | Add minimal excerpts only. | Each file has enough schema and records to exercise its documented edge case, no raw-data dump. |
| `tests/unit/data/test_provenance.py` | Check machine verification. | Missing raw files skip with a named CI/local reason; present files must match their hash and row count. |
| `tests/unit/data/test_fixtures.py` | Check fixture loadability and stated cases. | Fixtures assert edge-case presence rather than merely existing. |

`src/wocbots/data/__init__.py` is updated only if W1-01's public provenance API is not already exported. No ETL, labels, splits, modeling, or `antevorta-db` code belongs in this ticket.

## 8. Observability and provenance

`DATA_PROVENANCE.md` is the durable human-readable record. `RAW_FILES` is its machine-readable twin and must remain synchronized. A mismatch is a failure, not a warning. Test output identifies the individual relative path and reports either its recorded-vs-actual digest or its named absence reason. Since W1-01 runs no scientific experiment, the W0 harness manifest requirement is N/A; record the rationale in the closing report.

## 9. Sequenced implementation steps

1. Re-read the binding documents and this approved plan; re-verify the filename ruling and clean-room/data-license gates.
2. Acquire the approved datasets into the ignored local layout. Inspect headers, byte sizes, and CSV parseability without staging raw files.
3. Compute SHA-256 digests by streaming and obtain reliable data-record counts. Use a parser for files with quoted multiline cells; use line counting only for a documented single-line-record format.
4. Populate `DATA_PROVENANCE.md` with exact values and traceable source/terms/acquisition metadata. State the selected local naming convention and the five required files.
5. Encode the same values in `RAW_FILES`, keeping all paths relative to `data/raw/`; implement streaming hashing and an absence-aware `verify` result.
6. Create five minimal excerpts selected from the verified raw files. Preserve CSV headers and include the specified zero-value, missing-link, genre, and single/multiple-rating cases. Confirm each excerpt is license-compliant before staging.
7. Add tests in the same change set: parameterized raw-file checksum/count verification and independently meaningful fixture assertions.
8. Run the focused provenance/fixture tests first, then the full mandated check suite. With no raw data in CI, ensure skips name the reason; locally, no checksum or row-count case may skip.
9. Re-check that `git status` contains no raw data, archive, derived dataset, or unrelated W5 plan. Update the index/handoff only during ticket close after independent review; do not mark W1-01 complete before that review.

## 10. Exact test pins

1. **Digest pin, each of five records:** for a temporary known byte sequence, `sha256_of` equals the standard SHA-256; for each locally present registered raw file, the streamed result exactly equals that record's 64-hex digest.
2. **Verification boundaries:** missing file returns `(False, "file not present locally: …")` and the parameterized test skips with the named CI reason; a one-byte-corrupted temporary copy returns `False` with both recorded and actual digests; a matching file returns `(True, "ok")`.
3. **Row-count pins:** each present raw file equals its recorded header-excluded count. Include a quoted embedded-newline CSV test to prevent replacing parser counting with naive `wc -l` for TMDb-like inputs; separately pin the ratings-file optimized count against a small numeric fixture.
4. **Fixture load and edge pins:** TMDb movies have budget `0`, revenue `0`, and at least one usable row; credits keys are a subset of movie IDs; links contain both null and valid `tmdbId`; MovieLens movies include `(no genres listed)` and a multi-genre record; ratings include a one-rating movie and a multi-rating movie.
5. **Fixture scope pin:** assert every required fixture has the expected header and stays below a named small-record ceiling (recommended: 60 parsed rows) so a future raw-data dump fails review/tests.

## 11. Blast radius and non-goals

W1-02 consumes the verified raw layout for reference-table validation; W1-03 consumes the five fixtures and raw schemas for its pandas ETL. W1-04 relies on the provenance record to explain any reference-count discrepancy. Changes to source snapshot, filenames, CSV parser behavior, rows, or checksums are therefore data-contract changes: update docs, registry, fixtures, and downstream assumptions together and obtain review.

Non-goals: building/running `antevorta-db` (W1-02), joining/cleaning/feature construction (W1-03), choosing labels (W1-04), downloading unapproved datasets from the internet, or committing raw/derived data.

## 12. Risks and open items

- **Authorization constraint:** committed excerpts remain limited to the current test scope under the repository owner's 2026-08-16 permission attestation; expanding or replacing them requires a fresh authorization check.
- **Layout constraint:** the repository owner ratified the current archive aliases on 2026-08-16. Any migration to canonical filenames is a data-contract change, not a cleanup.
- **Risk:** Kaggle and MovieLens snapshots drift. A changed checksum or row count means a different source artifact; record it and assess downstream reference counts rather than overwriting the old fact.
- **Risk:** `ratings.csv` is large. Hash it streamingly and count without loading all rows into memory.
- **Existing downstream blocker, not W1-01 scope:** the handoff records W1-02 as blocked pending `antevorta-db` source or SQLite; this plan must not work around that clean-room stop condition.

## 13. Definition of done

1. The approved local layout contains both datasets and exactly the five documented raw files, all ignored by Git.
2. `DATA_PROVENANCE.md` and `RAW_FILES` agree on approved layout, source/terms/date, checksum, and row count for every file.
3. Five minimal, license-compliant fixtures are committed and prove their documented edge cases.
4. Checksum verification behaves correctly for present, absent, and mismatched inputs; row counts are correctly measured for the CSV structure.
5. `ruff check .`, `ruff format --check .`, `mypy src tests`, and `pytest` are green (named skips only where raw data is deliberately unavailable).
6. No raw data, archives, or derived datasets are staged; no unrelated work is included.
7. A results manifest is explicitly N/A; touched paths and verification output are recorded in the closing report.
8. An independent reviewer reads the full diff, checks the preamble’s forbidden-shortcut register and exact pins, and is recorded in `00_INDEX.md`; only then update `AGENT_HANDOFF.md` and close the ticket.
