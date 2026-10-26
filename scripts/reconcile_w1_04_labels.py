"""Measure W1-04 label balances on the Python-built W1-03 SQLite table."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from wocbots.data.ground_truth import load_reference_sqlite
from wocbots.data.labels import reconcile_labels
from wocbots.data.provenance import sha256_of


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", type=Path, default=Path("data/processed/movies.sqlite"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.sqlite.is_file():
        parser.error(f"input does not exist: {args.sqlite}")
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"], check=True, capture_output=True, text=True
    ).stdout
    result = {
        "git_sha": sha,
        "worktree_dirty": bool(status),
        "input_path": str(args.sqlite),
        "input_sha256": sha256_of(args.sqlite),
        "input_kind": "python_w1_03_sqlite; not independent reference validation",
        "seed": None,
        "shipped_label": "revenue > 2 * budget",
        "comparison_label": "revenue > 1.5 * budget; exact-5x reference fall-through corrected by user",
        "balance_waiver": (
            "Session driver explicitly waived published-balance requirement on 2026-10-25; "
            "stakeholder acceptance pending"
        ),
        "results": reconcile_labels(load_reference_sqlite(args.sqlite)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
