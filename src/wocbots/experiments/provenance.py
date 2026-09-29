"""Provenance capture (W0-03 S4).

This module is THE one licensed wall-clock site in `src/wocbots/` — the
RNG/wall-clock guard (`tests/unit/test_rng_discipline.py`, W0-04 S3) allows
`datetime.now` nowhere else. Every manifest's `created_utc` traces back to
the single call here.
"""

from __future__ import annotations

import platform as platform_module
import subprocess
from datetime import UTC, datetime
from importlib.metadata import version as _dist_version

from pydantic import BaseModel, ConfigDict

# Display key -> importlib.metadata distribution name, where they differ.
_DIST_NAMES = {
    "numpy": "numpy",
    "pandas": "pandas",
    "sklearn": "scikit-learn",
    "pydantic": "pydantic",
}


class Provenance(BaseModel):
    """What ran, from what: timestamp, code identity, dependency versions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    created_utc: str
    """ISO-8601 UTC timestamp. The one licensed wall-clock read (see below)."""

    git_sha: str
    """`git rev-parse HEAD`, with a `+dirty` suffix iff the working tree has
    uncommitted changes (`git status --porcelain` is non-empty)."""

    package_versions: dict[str, str]
    """wocbots, numpy, pandas, sklearn, pydantic, python."""

    platform: str


def _git_sha() -> str:
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
    if status.strip():
        sha += "+dirty"
    return sha


def _package_versions() -> dict[str, str]:
    from wocbots import __version__ as wocbots_version

    versions: dict[str, str] = {
        "wocbots": wocbots_version,
        "python": platform_module.python_version(),
    }
    for display_key, dist_name in _DIST_NAMES.items():
        versions[display_key] = _dist_version(dist_name)
    return versions


def capture_provenance() -> Provenance:
    """Capture provenance at THIS moment. Call once per experiment invocation."""
    now = datetime.now(UTC)  # ALLOWLISTED: the one licensed wall-clock read (W0-04 S3)
    return Provenance(
        created_utc=now.isoformat(),
        git_sha=_git_sha(),
        package_versions=_package_versions(),
        platform=platform_module.platform(),
    )
