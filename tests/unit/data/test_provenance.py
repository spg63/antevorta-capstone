"""W1-01 test requirement 1: checksums recompute-and-match DATA_PROVENANCE.md, or skip
with a named reason when the (gitignored, never-committed) raw file isn't present locally.
"""

import pytest

from wocbots.data.provenance import RAW_FILES, FileProvenance, verify


@pytest.mark.parametrize("file_provenance", RAW_FILES, ids=lambda f: f.relative_path)
def test_raw_file_checksum_matches_provenance(file_provenance: FileProvenance) -> None:
    if not file_provenance.path.exists():
        pytest.skip(f"raw data not present locally (expected in CI): {file_provenance.path}")
    ok, reason = verify(file_provenance)
    assert ok, reason


@pytest.mark.parametrize("file_provenance", RAW_FILES, ids=lambda f: f.relative_path)
def test_raw_file_row_count_matches_provenance(file_provenance: FileProvenance) -> None:
    import pandas as pd

    if not file_provenance.path.exists():
        pytest.skip(f"raw data not present locally (expected in CI): {file_provenance.path}")

    if file_provenance.relative_path.endswith("rating.csv"):
        # ~690MB / 20M rows: don't load into memory just to count. rating.csv has no
        # embedded newlines (pure numeric CSV), so a line count minus the header is exact.
        with file_provenance.path.open("rb") as fh:
            n = sum(1 for _ in fh) - 1
    else:
        n = len(pd.read_csv(file_provenance.path, low_memory=False))

    assert n == file_provenance.row_count
