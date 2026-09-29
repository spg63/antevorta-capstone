# Hollywood SQLite build runbook

Run these commands from the repository root.

## 1. Install the locked dependencies

```bash
uv sync
```

## 2. Supply the raw datasets

The repository does not include the raw datasets. Obtain the stakeholder-provided archive and ensure these
five files exist locally:

```text
data/raw/movielens/link.csv
data/raw/movielens/movie.csv
data/raw/movielens/rating.csv
data/raw/tmdb/movies.csv
data/raw/tmdb/credits.csv
```

Optionally verify their checksums and row counts before building:

```bash
uv run pytest tests/unit/data/test_provenance.py -q
```

## 3. Build the SQLite artifact

```bash
uv run python scripts/build_movies_sqlite.py
```

This creates the ignored `data/processed/movies.sqlite` artifact. It contains five source tables
(`movielens_links`, `movielens_movies`, `movielens_ratings`, `tmdb_movies`, and `tmdb_credits`) plus the
derived W1-03 feature table, `movies`.

## 4. Generate the reference outputs

```bash
uv run python scripts/extract_w1_02_reference.py
```

This validates and exports the derived `movies` table to the local full reference CSV, updates aggregate
manifests, and regenerates the deterministic test fixture. Run it after rebuilding the SQLite artifact or
changing the W1-03 feature schema or transforms; otherwise, normal development can skip it.

## 5. Verify the data pipeline

```bash
uv run pytest tests/unit/data/test_ground_truth.py tests/unit/data/test_hollywood.py -q
```

## Optional: inspect the database

```bash
sqlite3 data/processed/movies.sqlite ".tables"
```
