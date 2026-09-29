# Movie SQLite design for the five available datasets

## Scope and conclusion

This note traces the legacy `createHollywoodDB()` entry point, but proposes an
implementation that uses **only** these five files:

```text
data/raw/movielens/link.csv
data/raw/movielens/movie.csv
data/raw/movielens/rating.csv
data/raw/tmdb/credits.csv
data/raw/tmdb/movies.csv
```

All paths in this document are relative to the capstone repository root.

Use **one SQLite database file with six tables**. Five tables preserve one
source file each; the sixth is a query-ready `movies` table derived from the
other five. This is a good capstone design: it makes joins and aggregates
ordinary SQL, keeps the database portable, and lets the derived table be
rebuilt and audited. Six separate database *files* are not needed.

The recommended output is `data/processed/movies.sqlite`. This keeps the CSV
inputs under `data/raw/` and the generated database under `data/processed/`.
Create the `data/processed/` directory during the build if it does not exist.

The existing capstone database is `data/raw/movies.sqlite` and currently has
only the derived `movies` table (3,032 rows). Use that old location only when
an existing consumer requires it; do not write both database files.

## What the legacy entry point actually does

`Runner.kt:createHollywoodDB()` returns unless `Finals.START_FRESH` is true.
When true, it creates the following tables in this fixed order:

1. `links_table` from `link.csv`
2. `genome_tags` from `genome_tags.csv`
3. `movielens_movies` from `movie.csv`
4. `tmdb_credits` from `credits.csv`
5. `genome_scores` from `genome_scores.csv`
6. `individual_tags` from `tag.csv`
7. `individual_ratings` from `rating.csv`
8. `movies` from `movies.csv`, enriched by the earlier tables

Thus the legacy system does **not** merge all CSVs into one table. It creates
several source/intermediate tables and then one wide, denormalized table.
Three legacy inputs are unavailable here (`genome_tags.csv`,
`genome_scores.csv`, and `tag.csv`), so steps 2, 5, and 6 must be removed for
the new implementation.

The six database files are an old research-machine sharding strategy. Rows
are round-robin distributed across six files, then each table exists in every
file. They are not six tables in one database. With the current local
configuration (`Finals.otherUserDataPath` set to the supplied data root), the
legacy output would be:

```text
data/LocalDB/Hollywood/HOLLYWOOD0.sqlite3
data/LocalDB/Hollywood/HOLLYWOOD1.sqlite3
data/LocalDB/Hollywood/HOLLYWOOD2.sqlite3
data/LocalDB/Hollywood/HOLLYWOOD3.sqlite3
data/LocalDB/Hollywood/HOLLYWOOD4.sqlite3
data/LocalDB/Hollywood/HOLLYWOOD5.sqlite3
```

It will not read the supplied inputs unchanged: its testing-mode source path
is `data/LocalData/raw/...`, while the actual files are in `data/raw/...`.
This, plus the obsolete Java/Gradle stack, is why reproducing the design in
the other repository is preferable to running this project.

## Proposed six-table schema

Use source-compatible names, retain source values, and use `TEXT` for JSON.
SQLite's JSON functions operate on JSON stored as text; a special `JSON` type
is neither required nor consistently enforced.

### 1. `movielens_links` — `link.csv`

| Column | SQLite type | Source |
| --- | --- | --- |
| `movie_id` | `INTEGER PRIMARY KEY` | `movieId` |
| `imdb_id` | `INTEGER` | `imdbId` |
| `tmdb_id` | `INTEGER` | `tmdbId` |

Create an index on `tmdb_id`. Keep a missing TMDB ID as `NULL`; do not copy
the legacy code's random negative fallback value.

### 2. `movielens_movies` — `movie.csv`

| Column | SQLite type | Source |
| --- | --- | --- |
| `movie_id` | `INTEGER PRIMARY KEY` | `movieId` |
| `title` | `TEXT NOT NULL` | `title` |
| `genres` | `TEXT NOT NULL` | `genres` |

Retain the source pipe-delimited genres string. It can be converted to JSON
in the derived table if a consumer needs JSON.

### 3. `movielens_ratings` — `rating.csv`

| Column | SQLite type | Source |
| --- | --- | --- |
| `user_id` | `INTEGER NOT NULL` | `userId` |
| `movie_id` | `INTEGER NOT NULL` | `movieId` |
| `rating` | `REAL NOT NULL` | `rating` |
| `rated_at` | `TEXT NOT NULL` | `timestamp` |

The supplied file uses values such as `2005-04-02 23:53:47`, so retain them as
text in this format. Use `PRIMARY KEY (user_id, movie_id, rated_at)` or a
surrogate integer key. After bulk loading, create an index on `movie_id`; add
`user_id` only if the application queries rating histories by user.

### 4. `tmdb_movies` — `movies.csv`

Map source `id` to `tmdb_id INTEGER PRIMARY KEY`. Store the remaining source
columns as follows:

```text
budget INTEGER, genres TEXT, homepage TEXT, keywords TEXT,
original_language TEXT, original_title TEXT, overview TEXT,
popularity REAL, production_companies TEXT, production_countries TEXT,
release_date TEXT, revenue INTEGER, runtime REAL, spoken_languages TEXT,
status TEXT, tagline TEXT, title TEXT, vote_average REAL, vote_count INTEGER
```

`genres`, `keywords`, `production_companies`, `production_countries`, and
`spoken_languages` are source JSON arrays and should remain JSON text.

### 5. `tmdb_credits` — `credits.csv`

| Column | SQLite type | Source |
| --- | --- | --- |
| `tmdb_id` | `INTEGER PRIMARY KEY` | `movie_id` |
| `title` | `TEXT` | `title` |
| `cast_json` | `TEXT` | `cast` |
| `crew_json` | `TEXT` | `crew` |

Do not split cast and crew into people tables unless actor/crew lookup is a
frequent product feature. The raw JSON is sufficient for the current scope.

### 6. `movies` — derived query table

Build this from TMDB movies joined through the MovieLens link table, with
MovieLens metadata and rating aggregates. The existing capstone artifact has
this exact 14-column contract (using its current camel-case names):

```text
tmdbId, movieId, title, budget, revenue, runtime, tmdb_popularity,
tmdb_vote_average, tmdb_vote_count, ml_vote_average, ml_vote_count,
vote_average, vote_count, genres
```

`tmdbId` is the primary lookup key; index `movieId` if consumers query it.
Credits remain in `tmdb_credits` and can be joined when needed, avoiding a
large duplicated JSON payload in the common feature table.

## Build order and relationships

1. Create the database and five source tables.
2. Load `movielens_links`, `movielens_movies`, `tmdb_movies`, and
   `tmdb_credits` in transactions.
3. Load `movielens_ratings` in batched transactions.
4. Create the ratings and lookup indexes after load.
5. Create or refresh the derived `movies` table.
6. Validate source row counts, duplicate IDs, unmatched IDs, null counts, and
   the final schema before replacing an existing database artifact.

```text
tmdb_movies (tmdb_id) ────────┐
tmdb_credits (tmdb_id) ───────┤
                              ├── movies
movielens_links (tmdb_id, movie_id) ─┤
movielens_movies (movie_id) ─────────┤
movielens_ratings (movie_id) ────────┘
```

The core MovieLens aggregate is:

```sql
SELECT movie_id,
       COUNT(*) AS ml_vote_count,
       AVG(rating) * 2.0 AS ml_vote_average
FROM movielens_ratings
GROUP BY movie_id;
```

Multiplying by two aligns MovieLens's 0–5 ratings with TMDB's 0–10 scale.
Define the existing `vote_average` and `vote_count` fields explicitly in the
new pipeline, because they are application-level combined features rather
than columns supplied by either CSV.

## Legacy behavior deliberately not copied

- Six disk shards and cross-shard query merging.
- The three unavailable MovieLens files and their tables.
- Random negative values for missing TMDB identifiers.
- Revenue-performance classification columns.
- The legacy derived table's implicit data cleaning and reliance on prior
  selector queries.

Relevant implementation sources: `Runner.kt`, `DataPaths.kt`, `DBLocator.kt`,
`dbcreator/hollywood/`, and `dbInteraction/columnsAndKeys/`.
