"""W0-01 §10 pins — scaffold integrity.

§10.1 (fresh-environment) and §10.3 (lockfile honesty) are proven by the CI workflow
definition itself (`uv sync --frozen` in a fresh runner); §10.6 (structural review proof)
is a close-report artifact, not a pytest. What CAN be pinned in-process lands here.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import wocbots

REPO_ROOT = Path(__file__).resolve().parents[2]

# §10.5 — the index streams table, mirrored. If the team re-deals streams, this table,
# CODEOWNERS, and the index change in the SAME PR (drift between them is a test failure,
# not a surprise review request).
EXPECTED_OWNERSHIP = {
    "/src/wocbots/experiments/": "@CORE-TBD",
    "/src/wocbots/aggregation/": "@CORE-TBD",
    "/src/wocbots/protocols.py": "@CORE-TBD",
    "/src/wocbots/data/": "@DATA-TBD",
    "/src/wocbots/agents/": "@AGENTS-TBD",
    "/src/wocbots/arena/": "@ARENA-TBD",
    "/src/wocbots/interaction/": "@ARENA-TBD",
    "/src/wocbots/evaluation/": "@EVAL-TBD",
    "/configs/": "@CORE-TBD",
    "/results/": "@EVAL-TBD",
    "*": "@CORE-TBD",
}

ALL_PACKAGES = [
    "wocbots",
    "wocbots.agents",
    "wocbots.arena",
    "wocbots.interaction",
    "wocbots.aggregation",
    "wocbots.data",
    "wocbots.evaluation",
    "wocbots.experiments",
]


def test_version_import() -> None:
    """§10.4 — the package installs and carries the pinned version."""
    assert wocbots.__version__ == "0.1.0"


@pytest.mark.parametrize("package", ALL_PACKAGES)
def test_all_packages_import(package: str) -> None:
    """§10.4 — all eight packages import from a fresh sync."""
    importlib.import_module(package)


def test_codeowners_matches_streams_table() -> None:
    """§10.5 — CODEOWNERS is the streams table, byte-for-byte in path→owner terms."""
    codeowners = REPO_ROOT / "CODEOWNERS"
    assert codeowners.is_file(), "CODEOWNERS must live at the repo root (S4 location ruling)"
    parsed: dict[str, str] = {}
    for line in codeowners.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        path, owner = stripped.split(maxsplit=1)
        parsed[path] = owner
    assert parsed == EXPECTED_OWNERSHIP


@pytest.mark.slow
def test_slow_marker_dummy() -> None:
    """§10.2 — the registered `slow` mark: excluded by `-m "not slow"`, included by plain pytest.

    Deliberately trivial; its presence is the pin. `--strict-markers` (pyproject) makes any
    UNREGISTERED mark a collection error.
    """
    assert True
