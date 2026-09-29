"""Extract W1-02's Python-built feature reference from its SQLite artifact.

The output preserves W1-03 values and emits aggregate counts only. It does not create
labels or present the source as independent validation of the Python ETL.

Run this script after rebuilding ``data/processed/movies.sqlite`` or changing W1-03's feature
schema or transforms. It is unnecessary during normal development when the SQLite
artifact and committed reference outputs are already current.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from wocbots.data.ground_truth import (
    extract_reference,
    write_excerpt,
    write_reference_manifest,
    write_versioned_reference,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", type=Path, default=Path("data/processed/movies.sqlite"))
    parser.add_argument("--derived-dir", type=Path, default=Path("data/derived"))
    parser.add_argument(
        "--excerpt-path",
        type=Path,
        default=Path("tests/fixtures/w1_02_reference/movies_reference_excerpt_50.csv"),
    )
    parser.add_argument("--version", type=str, default="v1")
    parser.add_argument(
        "--manifest-out",
        type=Path,
        default=Path("data/reference_manifests/movies_reference_v1.json"),
    )
    args = parser.parse_args()

    result = extract_reference(args.sqlite)
    versioned_path = write_versioned_reference(result, args.derived_dir, args.version)
    excerpt_path = write_excerpt(result, args.excerpt_path)
    manifest_path = write_reference_manifest(result, args.manifest_out)

    payload = result.to_manifest_dict()
    payload["versioned_reference_path"] = str(versioned_path)
    payload["excerpt_path"] = str(excerpt_path)
    payload["manifest_path"] = str(manifest_path)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
