# W1-02 — Hollywood six-table SQLite build and reference extraction — IMPLEMENTATION PLAN

> **Status:** IMPLEMENTED — pending full check suite and independent review. **Precedence:** the stakeholder-approved `tickets/hollywood-database-implementation.md` (six-table design) supersedes W1-02's former one-table / `data/raw/movies.sqlite` design; the mandatory preamble and the spec's normative W1-03 preparation rules remain binding.

## 1. Metadata

**Wave:** W1. **Blocked by:** W1-01 raw inputs. **Blocks:** W1-04's canonical feature artifact. **Mode:** PLAN. This is a deterministic data-artifact ticket, not an experiment; a results manifest is N/A. Evidence is the SQLite build manifest, reference manifest, provenance record, and tests.

## 2. Decision and system meaning

Build one portable SQLite database at `data/processed/movies.sqlite`; do not create the old `data/raw/movies.sqlite` path. The database retains each of the five supplied raw inputs in source tables and contains the query-ready W1-03 feature table as its sixth `movies` table. This gives consumers a single auditable artifact while retaining the exact source rows and relationships used to derive features.

The database is a canonical artifact produced from the same Python pipeline, not independent validation of that pipeline. W1-04 continues to own labels; no label or legacy performance-class columns are created.

## 3. Data contract

| SQLite table | Source / role | Key and indexes |
|---|---|---|
| `movielens_links` | `movielens/link.csv`, renamed to snake case | `movie_id` primary key; index `tmdb_id`; missing TMDb IDs remain `NULL` |
| `movielens_movies` | `movielens/movie.csv`, source genres retained as pipe text | `movie_id` primary key |
| `movielens_ratings` | `movielens/rating.csv`, timestamp stored as `rated_at` text | composite primary key (`user_id`, `movie_id`, `rated_at`); index `movie_id` after load |
| `tmdb_movies` | `tmdb/movies.csv`, source JSON remains text | `tmdb_id` primary key |
| `tmdb_credits` | `tmdb/credits.csv`, cast/crew renamed to JSON-text columns | `tmdb_id` primary key |
| `movies` | Derived W1-03 feature/provenance artifact | preserves exact `OUTPUT_COLUMNS`; indexes on `tmdbId` and `movieId` |

The derived table has exactly these ordered columns:

```text
tmdbId, movieId, title, budget, revenue, runtime, tmdb_popularity,
tmdb_vote_average, tmdb_vote_count, ml_vote_average, ml_vote_count,
vote_average, vote_count, genres
```

Source-table types and column mappings follow `tickets/hollywood-database-implementation.md`. JSON is stored as SQLite `TEXT`; source values are not parsed or normalized during source loading. `genres` in the derived table retains W1-03's stable JSON-list transport encoding.

## 4. Execution path

```text
verified W1-01 CSVs
  -> explicit source-table schemas and batched SQLite loads
  -> source primary-key / lookup indexes
  -> call W1-03 once for the normative join, cleaning, rating aggregation,
     combined vote features, and genre intersection
  -> serialize unchanged ordered W1-03 output as derived movies
  -> atomically replace data/processed/movies.sqlite
  -> extract/validate movies and write local CSV, aggregate manifest, and fixture
```

Calling W1-03 once preserves the existing normative feature semantics without duplicating its transforms in the database writer. The persisted source tables make inputs and the SQL-level rating aggregate auditable; tests will pin `movies` against W1-03 output from the same five raw frames.

## 5. Files and interfaces

| Path | Change | Contract |
|---|---|---|
| `src/wocbots/data/ground_truth.py` | Replace one-table writer internals with six-table build support and schema validation. | `build_movies_sqlite(features, sqlite_path, *, source_tables) -> SQLiteBuildResult`; creates exactly six tables and atomically replaces only the requested artifact. |
| `scripts/build_movies_sqlite.py` | Load five raw CSVs, build source-table inputs, call W1-03 once, and write new default artifact. | Default path `data/processed/movies.sqlite`; no legacy raw-path write unless explicitly requested. |
| `scripts/extract_w1_02_reference.py` | Change default input path only. | Extracts solely derived `movies`; source tables are not exported or modified. |
| `src/wocbots/data/__init__.py` | Export new public result/input types. | Public names stay typed and documented. |
| `tests/unit/data/test_ground_truth.py` | Expand temporary-database pins. | Covers six tables, mappings, indexes, derived contract, atomic failure, and extraction. |
| `data/DATA_PROVENANCE.md`, `data/README.md`, manifests | Replace old path / one-table record. | Records source hashes, schemas, counts, versions, final hash, and non-independence. |
| `.gitignore` | Ignore generated processed artifacts. | `data/processed/` stays untracked; manifests and fixtures stay tracked. |
| `tickets/W1-02_ground-truth-build-extract.md` | Align ticket language with superseding design. | Retains W1-04 label ownership. |

## 6. Implementation sequence

1. Define source-schema constants and typed source-table inputs; validate expected CSV columns before touching a target.
2. Create a temporary SQLite file with explicit `CREATE TABLE` statements, preventing pandas type-inference drift.
3. Bulk insert each source DataFrame in bounded batches and create post-load indexes. Preserve `NULL` TMDb mappings and source JSON/pipe strings exactly.
4. Invoke `build_hollywood_features` once on the five raw frames, validate `OUTPUT_COLUMNS`, and write unchanged output as the sixth `movies` table. Add derived indexes after load.
5. Validate six table names, required schemas/indexes, source and derived row counts, and derived contract before atomic replacement. Hash after close.
6. Move extractor default to `data/processed/movies.sqlite`; retain strict derived-table validation and canonical CSV/manifest/fixture output.
7. Regenerate local artifact and references from verified raw inputs; update committed aggregate outputs only when values legitimately change. Never commit database or full export.
8. Update provenance, data policy, ticket text, and CLI docs.
9. Run focused tests and full check suite; obtain independent review before close.

## 7. Test pins

1. **Six-table schema:** a five-input fixture creates exactly the approved tables, columns/types, and no pandas index columns.
2. **Source preservation:** null TMDb IDs, JSON fields, pipe genres, credit JSON, and rating timestamps survive with required renamed columns.
3. **Keys and indexes:** pins required primary keys and `tmdb_id`, ratings `movie_id`, and derived-ID indexes.
4. **Derived contract:** `movies` matches the one W1-03 call for identical fixture inputs, including JSON genres and combined ratings.
5. **Accounting:** source/derived row counts and derived null/zero/duplicate counts are recorded, never cleaned or hidden by extraction.
6. **Atomic failure:** invalid source schema or derived contract cannot replace a valid database.
7. **Canonical output:** identical inputs yield byte-identical extracted CSV content and equal schema/count metadata; SQLite hashes are recorded, not cross-version behavior pins.
8. **Extractor fixture:** the processed-path default reads only `movies`; the deterministic excerpt has all 14 columns and no labels.
9. **Local integration:** with ignored raw files, build/extract CLIs reproduce aggregate manifests; otherwise skip only for named missing inputs.

## 8. Risks and open questions

- The 20M-row ratings file requires bounded batch insertion; no per-row Python loop or unbounded copy is acceptable.
- A duplicate source primary key must fail clearly rather than be silently deduplicated.
- SQLite bytes may vary across versions; canonical extracted rows are the behavioral reproducibility assertion.
- Existing artifact/manifests reflect the old path and must be regenerated from verified inputs.
- W1-03 remains the normative derived-feature implementation. Independently reproducing it in SQL would be a separate transformation change requiring a new ruling.

## 9. Definition of done

1. `data/processed/movies.sqlite` holds five documented source tables and the exact W1-03-derived `movies` table; the legacy default path is not written.
2. Source data is source-faithful, derived features W1-03-faithful, and labels absent.
3. Builds are atomic, audited, provenance-recorded, and safe for large ratings input.
4. Extractor, manifests, fixture, docs, tests, and ignore policy all use the new design.
5. Checks pass; generated data stays untracked; independent review occurs before closure.
