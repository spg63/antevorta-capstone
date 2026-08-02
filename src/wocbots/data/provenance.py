"""Raw-dataset provenance records for the Hollywood data sources (W1-01).

This module is the machine-readable twin of ``data/DATA_PROVENANCE.md``. Keep the two
in sync: if a checksum or row count changes here, it changed there too, and vice versa.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RAW_DATA_ROOT = REPO_ROOT / "data" / "raw"


@dataclass(frozen=True)
class FileProvenance:
    """One recorded raw file: where it lives, and what it should hash/count to."""

    relative_path: str
    sha256: str
    row_count: int  # excludes header

    @property
    def path(self) -> Path:
        return RAW_DATA_ROOT / self.relative_path


# Source of truth: data/DATA_PROVENANCE.md §1-2. Row counts computed with
# pandas.read_csv(...).shape[0] for the TMDb/links/movie files (they contain embedded
# commas/newlines inside quoted JSON fields, so a naive line count under-/over-counts);
# rating.csv is pure numeric CSV, so `wc -l` minus the header is exact.
RAW_FILES: tuple[FileProvenance, ...] = (
    FileProvenance(
        "tmdb5000/tmdb_5000_movies.csv",
        "1e0584a8dd374120e4ed4f2b81f0d2bd0eb95a554708e4a350d00ed5c46d2825",
        4803,
    ),
    FileProvenance(
        "tmdb5000/tmdb_5000_credits.csv",
        "9d0050599ff88d40366c4841204b1489862bca346bfa46c20b05a65d14508435",
        4803,
    ),
    FileProvenance(
        "movielens20m/link.csv",
        "80b677ee7c159b0e8716ed6c5f86932b0ffa029b421ebc05ded338bc69c7a7e2",
        27278,
    ),
    FileProvenance(
        "movielens20m/movie.csv",
        "45763d3eaf1235bca9e5e5b93d41d1ba03823c485c9d3fead23ea0c5eafa6b3a",
        27278,
    ),
    FileProvenance(
        "movielens20m/rating.csv",
        "9ec53ccb3e51c78fd31a451499f1c856c5c778766a7e7979683741ffb696adca",
        20000263,
    ),
)


def sha256_of(path: Path, chunk_size: int = 1 << 20) -> str:
    """Stream a file's SHA-256 (safe for the ~690MB rating.csv)."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(file_provenance: FileProvenance) -> tuple[bool, str]:
    """Recompute a raw file's checksum against its recorded value.

    Returns (ok, reason). ``ok`` is False (not raised) when the file is simply absent —
    callers decide whether that's a skip (CI, no local raw data) or a failure.
    """
    if not file_provenance.path.exists():
        return False, f"file not present locally: {file_provenance.path}"
    actual = sha256_of(file_provenance.path)
    if actual != file_provenance.sha256:
        return False, f"checksum mismatch: recorded {file_provenance.sha256}, got {actual}"
    return True, "ok"
