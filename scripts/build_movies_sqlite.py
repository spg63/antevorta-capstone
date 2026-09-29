"""Build W1-02's canonical feature SQLite from verified W1-01 raw inputs.

The script invokes W1-03 exactly once and serializes its unchanged output to the fixed
``movies`` table. Labels deliberately remain the responsibility of W1-04.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from wocbots.data.ground_truth import SourceTables, build_movies_sqlite, write_build_manifest
from wocbots.data.hollywood import build_hollywood_features
from wocbots.data.provenance import RAW_DATA_ROOT


def _load_raw_inputs(raw_root: Path) -> SourceTables:
    """Load W1-01's five verified files for source tables and W1-03."""
    tmdb_movies = pd.read_csv(raw_root / "tmdb" / "movies.csv")
    tmdb_credits = pd.read_csv(raw_root / "tmdb" / "credits.csv")
    links = pd.read_csv(raw_root / "movielens" / "link.csv")
    ml_movies = pd.read_csv(raw_root / "movielens" / "movie.csv")
    ratings = pd.read_csv(raw_root / "movielens" / "rating.csv")
    return SourceTables(links, ml_movies, ratings, tmdb_movies, tmdb_credits)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=RAW_DATA_ROOT)
    parser.add_argument("--sqlite", type=Path, default=Path("data/processed/movies.sqlite"))
    parser.add_argument(
        "--metadata-out",
        type=Path,
        default=Path("data/reference_manifests/movies_sqlite_v1.json"),
    )
    args = parser.parse_args()

    source_tables = _load_raw_inputs(args.raw_root)
    features = build_hollywood_features(
        source_tables.tmdb_movies,
        source_tables.tmdb_credits,
        source_tables.links,
        source_tables.movies,
        source_tables.ratings,
    )
    result = build_movies_sqlite(features, args.sqlite, source_tables=source_tables)
    metadata_path = write_build_manifest(result, args.metadata_out)
    payload = result.to_manifest_dict()
    payload["metadata_path"] = str(metadata_path)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
