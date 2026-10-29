"""Add or refresh W1-04's strict-2× label in the computed SQLite movies table."""

from __future__ import annotations

import argparse
from pathlib import Path

from wocbots.data.labels import label_movies_sqlite


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", type=Path, default=Path("data/processed/movies.sqlite"))
    args = parser.parse_args()
    count = label_movies_sqlite(args.sqlite)
    print(f"Labeled {count} movies in {args.sqlite}")


if __name__ == "__main__":
    main()
