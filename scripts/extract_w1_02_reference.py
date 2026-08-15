"""W1-02 S2 runner: extract + version the reference table from the stakeholder-ratified
ground-truth SQLite (see `wocbots.data.ground_truth` module docstring for the ruling this
implements and what it does NOT resolve -- the label columns).

Usage:
    python scripts/extract_w1_02_reference.py \
        --sqlite /path/to/movies.sqlite \
        --derived-dir data/derived \
        --excerpt-path tests/fixtures/w1_02_reference/movies_reference_excerpt_50.csv \
        --version v1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from wocbots.data.ground_truth import extract_reference, write_excerpt, write_versioned_reference


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", type=Path, required=True)
    parser.add_argument("--derived-dir", type=Path, default=Path("data/derived"))
    parser.add_argument("--excerpt-path", type=Path, default=Path("tests/fixtures/w1_02_reference/movies_reference_excerpt_50.csv"))
    parser.add_argument("--version", type=str, default="v1")
    parser.add_argument("--counts-out", type=Path, default=None, help="Optional path to write the counts manifest as JSON")
    args = parser.parse_args()

    result = extract_reference(args.sqlite)
    versioned_path = write_versioned_reference(result, args.derived_dir, args.version)
    excerpt_path = write_excerpt(result, args.excerpt_path)

    manifest = result.to_manifest_dict()
    manifest["versioned_reference_path"] = str(versioned_path)
    manifest["excerpt_path"] = str(excerpt_path)

    print(json.dumps(manifest, indent=2))
    if args.counts_out:
        args.counts_out.parent.mkdir(parents=True, exist_ok=True)
        args.counts_out.write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
