"""W1-01 raw-file provenance pins and local-data verification."""

import hashlib
from pathlib import Path

import pytest

import wocbots.data.provenance as provenance
from wocbots.data.provenance import (
    RAW_FILES,
    FileProvenance,
    count_csv_records,
    sha256_of,
    verify,
)


def test_sha256_of_streams_known_bytes_across_small_chunks(tmp_path: Path) -> None:
    payload = b"provenance bytes\x00across chunks"
    path = tmp_path / "known.bin"
    path.write_bytes(payload)

    assert sha256_of(path, chunk_size=3) == hashlib.sha256(payload).hexdigest()


def test_sha256_of_rejects_nonpositive_chunk_size(tmp_path: Path) -> None:
    path = tmp_path / "known.bin"
    path.write_bytes(b"x")

    with pytest.raises(ValueError, match="chunk_size must be positive"):
        sha256_of(path, chunk_size=0)


def test_verify_missing_file_returns_named_reason(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(provenance, "RAW_DATA_ROOT", tmp_path)
    record = FileProvenance("missing.csv", "a" * 64, 0)

    assert verify(record) == (False, f"file not present locally: {tmp_path / 'missing.csv'}")


def test_verify_reports_recorded_and_actual_digests_on_corruption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    path = raw_root / "sample.csv"
    path.write_bytes(b"header\nunchanged\n")
    expected = sha256_of(path)
    path.write_bytes(b"header\ncorrupted\n")
    monkeypatch.setattr(provenance, "RAW_DATA_ROOT", raw_root)

    ok, reason = verify(FileProvenance("sample.csv", expected, 1))

    assert not ok
    assert expected in reason
    assert sha256_of(path) in reason


def test_verify_accepts_matching_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    path = raw_root / "sample.csv"
    path.write_bytes(b"header\nrecord\n")
    monkeypatch.setattr(provenance, "RAW_DATA_ROOT", raw_root)

    assert verify(FileProvenance("sample.csv", sha256_of(path), 1)) == (True, "ok")


def test_count_csv_records_handles_quoted_embedded_newlines(tmp_path: Path) -> None:
    path = tmp_path / "multiline.csv"
    path.write_text('id,description\n1,"first line\nsecond line"\n2,ordinary\n')

    assert count_csv_records(path) == 2


def test_count_csv_records_uses_line_count_for_numeric_rating_format(tmp_path: Path) -> None:
    path = tmp_path / "rating.csv"
    path.write_text("userId,movieId,rating,timestamp\n1,2,4.0,10\n2,2,3.5,11\n")

    assert count_csv_records(path, single_line_records=True) == 2


@pytest.mark.parametrize("file_provenance", RAW_FILES, ids=lambda f: f.relative_path)
def test_raw_file_checksum_matches_provenance(file_provenance: FileProvenance) -> None:
    if not file_provenance.path.exists():
        pytest.skip(f"raw data not present locally (expected in CI): {file_provenance.path}")
    ok, reason = verify(file_provenance)
    assert ok, reason


@pytest.mark.parametrize("file_provenance", RAW_FILES, ids=lambda f: f.relative_path)
def test_raw_file_row_count_matches_provenance(file_provenance: FileProvenance) -> None:
    if not file_provenance.path.exists():
        pytest.skip(f"raw data not present locally (expected in CI): {file_provenance.path}")

    actual_count = count_csv_records(
        file_provenance.path,
        single_line_records=file_provenance.relative_path.endswith("rating.csv"),
    )
    assert actual_count == file_provenance.row_count
