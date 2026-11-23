"""Run W1-06's seeded, train-only Hollywood anchor ranking."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import numpy as np

from wocbots.data.anchor_analysis import run_anchor_analysis


def _git_sha() -> str:
    try:
        sha_result = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
        dirty_result = subprocess.run(
            ["git", "status", "--porcelain"], check=True, capture_output=True, text=True
        )
        sha = sha_result.stdout.strip()
        dirty = dirty_result.stdout
        return f"{sha}+dirty" if dirty.strip() else sha
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", type=Path, default=Path("data/processed/movies.sqlite"))
    parser.add_argument("--split", type=Path, default=Path("data/derived/split_v1.json"))
    parser.add_argument("--output", type=Path, default=Path("results/manifests/w1_06_anchor_analysis.json"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    analysis = run_anchor_analysis(
        args.sqlite, args.split, args.output, np.random.default_rng(args.seed), args.seed, _git_sha()
    )
    for row in analysis["ranking"][:6]:  # type: ignore[index]
        print(f"{row['feature']}: r={row['point_biserial_r']:.6f}, pc1={row['pc1_loading']:.6f}")


if __name__ == "__main__":
    main()
