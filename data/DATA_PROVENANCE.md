# Data Provenance — W1-01

Raw files live locally at `data/raw/<dataset>/` and are **never committed** (see `.gitignore`).
This file, its checksums, and the small fixture excerpts under `tests/fixtures/` are the
committed record.

**`movie-dataset.zip`:** the stakeholder-provided archive that supplies §1-2's raw files. It
also contains two datasets this pipeline does not use — `movieDataset/` (Kaggle's "The Movies
Dataset": `movies_metadata.csv`, `credits (1).csv`, `keywords.csv`, `links.csv`,
`links_small.csv`, `ratings.csv`, `ratings_small.csv`) and `IMDBMovieData.csv`. Unzip only its
`tmdb/` and `movielens/` folders into `data/raw/`; the other files can be left alone (or
deleted) since no W1-03 rule (§4.3) reads them.

## 1. TMDb 5000 Movie Dataset

- **Source:** Kaggle, "TMDB 5000 Movie Dataset" (`tmdb/5000-movies`).
- **License / ToS:** Kaggle-hosted; underlying data sourced from TMDb under TMDb's terms of
  use (non-commercial, attribution). Fixture excerpts below are kept minimal per the
  repo-public rule (index v1.9).
- **Files acquired:** `tmdb/movies.csv`, `tmdb/credits.csv` (bundled inside
  `movie-dataset.zip` as `tmdb/movies.csv` / `tmdb/credits.csv`; byte-identical to the
  standalone Kaggle download's `tmdb_5000_movies.csv` / `tmdb_5000_credits.csv`).
- **Local path:** `data/raw/tmdb/` (unzip `movie-dataset.zip`'s `tmdb/` folder here).
- **Download recorded:** 2026-07-25 (files supplied directly by the stakeholder-provided
  archive; original Kaggle file dates 2019-09-19).

| File | Rows (excl. header) | Size (bytes) | SHA-256 |
|---|---:|---:|---|
| `movies.csv` | 4,803 | 5,698,602 | `1e0584a8dd374120e4ed4f2b81f0d2bd0eb95a554708e4a350d00ed5c46d2825` |
| `credits.csv` | 4,803 | 40,044,293 | `9d0050599ff88d40366c4841204b1489862bca346bfa46c20b05a65d14508435` |

## 2. MovieLens 20M

- **Source:** Kaggle mirror of GroupLens "MovieLens 20M Dataset" (`grouplens/movielens-20m-dataset`).
- **License / ToS:** GroupLens research-use license (non-commercial, no redistribution of the
  full dataset). Fixture excerpts below are ~50-row samples only, consistent with that term.
- **Files acquired (subset needed for W1):** `link.csv`, `movie.csv`, `rating.csv`, all under
  `movie-dataset.zip`'s `movielens/` folder. (`tag.csv`, `genome_tags.csv`,
  `genome_scores.csv` were also supplied but are not consumed by the Hollywood pipeline —
  §4.3 does not name them — and are therefore not fixtured here.)
- **Local path:** `data/raw/movielens/` (unzip `movie-dataset.zip`'s `movielens/` folder here).
- **Download recorded:** 2026-07-25 (stakeholder-provided archive; original file dates
  2019-09-20).

| File | Rows (excl. header) | Size (bytes) | SHA-256 |
|---|---:|---:|---|
| `link.csv` | 27,278 | 539,334 | `80b677ee7c159b0e8716ed6c5f86932b0ffa029b421ebc05ded338bc69c7a7e2` |
| `movie.csv` | 27,278 | 1,493,648 | `45763d3eaf1235bca9e5e5b93d41d1ba03823c485c9d3fead23ea0c5eafa6b3a` |
| `rating.csv` | 20,000,263 | 690,353,377 | `9ec53ccb3e51c78fd31a451499f1c856c5c778766a7e7979683741ffb696adca` |

Row counts for `tmdb_5000_movies.csv` / `tmdb_5000_credits.csv` / `link.csv` / `movie.csv` were
computed with `pandas.read_csv(...).shape[0]` (fields contain embedded commas/newlines inside
quoted JSON strings, so a naive line count is wrong for the TMDb files). `rating.csv` is pure
numeric CSV with no embedded newlines, so `wc -l` minus the header is exact and matches the
published MovieLens 20M row count (20,000,263 ratings).

## 3. Checksum verification

`tests/unit/data/test_provenance.py` recomputes SHA-256 for any of the files above that are
present on disk and compares against this table. Datasets are gitignored, so in CI (no raw
data present) every case is skipped with a named reason; locally, with `data/raw/` populated,
the test enforces the table stays truthful.

## 4. Fixture excerpts

`tests/fixtures/tmdb5000/` and `tests/fixtures/movielens20m/` hold ~50-row excerpts of each
file above, chosen to span the ETL's edge cases (see each fixture's header comment / the test
that loads it):

- `tmdb_5000_movies_fixture.csv` — includes rows with `budget == 0`, `revenue == 0`, and a
  fully-populated high-budget/high-revenue row.
- `tmdb_5000_credits_fixture.csv` — the matching `movie_id` rows for the movies fixture.
- `link_fixture.csv` — includes rows with a null `tmdbId` (unmapped movie) alongside normal
  mappings, so the join-keeps-both-datasets rule (§4.3.1) has something to drop.
- `movie_fixture.csv` — matching `movieId`s, includes a multi-genre and a `(no genres
  listed)` row.
- `rating_fixture.csv` — multiple ratings for a handful of `movieId`s (so the per-movie
  aggregate rule, §4.3.4, has more than one rating to aggregate), including a movie with only
  one rating (edge case for the mean/weighted-mean math).

## 5. antevorta-db ground truth (W1-02) — BLOCKED

W1-02 requires either building `antevorta-db` (Kotlin/JVM) locally or receiving its built
SQLite output from the stakeholder. **Neither the `antevorta-db` source nor a pre-built
SQLite file was provided in this session's inputs.** Per the clean-room rule and preamble §0.2,
this is a STOP condition, not something to route around — the AI session cannot source
`antevorta-db` from anywhere outside this repo's provided materials. This blocks:

- W1-02 itself (no ground-truth table can be extracted).
- The strict, row-level half of W1-04's reconciliation gate (it can only be checked against
  the reference table, which doesn't exist here yet).

## 6. Investigation note — the join-count discrepancy (feeds W1-04's escalation)

Running the W1-03 pipeline on the raw files above gives **4,227 matched movies** (join
step) against the spec's reference **4,722** — a shortfall of ~495, well outside "should
land close." Diagnosis:

- Every TMDb movie that *does* successfully link to a MovieLens `tmdbId` has a release
  date on or before **2015-11-20**.
- Of the 577 TMDb movies that fail to link, the overwhelming majority (185 + 104 = 289 of
  577) are dated 2015–2016, i.e. released right at or after this `link.csv`'s apparent
  coverage edge. The remainder (2003–2013, ~180 titles) are presumably films that simply
  never entered the MovieLens rating corpus (low-visibility/foreign titles), which is
  expected background attrition, not a bug.

**Conclusion:** this looks like a dataset-vintage mismatch between the MovieLens 20M
`link.csv`/`movie.csv` snapshot bundled in this session's upload and whichever snapshot
the antevorta-db reference build used (a later refresh of "ml-20m" with more/newer movies
mapped would close most of this gap) — exactly the kind of drift `data/DATA_PROVENANCE.md`
exists to catch (see this ticket's own rationale). It is **not** confirmed, because
confirming it requires W1-02's reference table (blocked — see §5 above). Downstream counts
(1,195 dropped vs reference 1,023; 3,032 usable vs reference 3,699; label balance 43.9/56.1
vs reference 47.5/52.5) all track directly from this shortfall.

**This is the W1-04 gate firing.** Per that ticket's own rule ("if neither matches
cleanly... escalate to the stakeholder before closing"), this has been left as an
escalation, not silently reconciled. See W1-04's RESULT block.

