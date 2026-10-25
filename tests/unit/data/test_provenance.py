"""W1-01 raw-file provenance pins and local-data verification."""

import hashlib
import re
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

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_PROVENANCE_PATH = REPO_ROOT / "data" / "DATA_PROVENANCE.md"
_RAW_TABLE_HEADER = "| File | Rows (excl. header) | Size (bytes) | SHA-256 |"
_SOURCE_SECTIONS = (
    ("## 1. TMDb 5000 Movie Dataset", "tmdb"),
    ("## 2. MovieLens 20M", "movielens"),
)


def _documented_raw_files(markdown: str) -> dict[str, tuple[str, int]]:
    """Read the two W1-01 source tables without treating later report tables as inputs."""
    records: dict[str, tuple[str, int]] = {}
    for heading, directory in _SOURCE_SECTIONS:
        if heading not in markdown:
            raise ValueError(f"missing provenance section: {heading}")
        section = markdown.split(heading, maxsplit=1)[1].split("\n## ", maxsplit=1)[0]
        if _RAW_TABLE_HEADER not in section:
            raise ValueError(f"missing raw-file table in section: {heading}")
        table_lines = section.split(_RAW_TABLE_HEADER, maxsplit=1)[1].lstrip("\n").splitlines()
        if not table_lines or not table_lines[0].startswith("|---|"):
            raise ValueError(f"missing table separator in section: {heading}")

        row_lines: list[str] = []
        for line in table_lines[1:]:
            if not line.startswith("|"):
                break
            row_lines.append(line)
        if not row_lines:
            raise ValueError(f"no raw-file records in section: {heading}")
        for line in row_lines:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) != 4:
                raise ValueError(f"malformed raw-file row in section {heading}: {line}")
            relative_path = f"{directory}/{cells[0].strip('`')}"
            if relative_path in records:
                raise ValueError(f"duplicate documented raw-file path: {relative_path}")
            try:
                row_count = int(cells[1].replace(",", ""))
            except ValueError as error:
                raise ValueError(f"invalid row count for {relative_path}: {cells[1]}") from error
            sha256 = cells[3].strip("`")
            if re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
                raise ValueError(f"invalid SHA-256 for {relative_path}: {sha256}")
            records[relative_path] = (sha256, row_count)
    return records


def _assert_documented_records_match_registry(records: dict[str, tuple[str, int]]) -> None:
    expected = {record.relative_path: (record.sha256, record.row_count) for record in RAW_FILES}
    if records != expected:
        raise AssertionError(
            "DATA_PROVENANCE.md raw-file records differ from RAW_FILES; "
            f"documented={records}, registry={expected}"
        )


def _provenance_markdown(tmdb_rows: str, movielens_rows: str) -> str:
    return "\n".join(
        (
            "## 1. TMDb 5000 Movie Dataset",
            _RAW_TABLE_HEADER,
            "|---|---:|---:|---|",
            tmdb_rows,
            "",
            "## 2. MovieLens 20M",
            _RAW_TABLE_HEADER,
            "|---|---:|---:|---|",
            movielens_rows,
            "",
            "## 3. Checksum verification",
        )
    )


def test_documented_raw_file_records_match_machine_registry() -> None:
    records = _documented_raw_files(DATA_PROVENANCE_PATH.read_text(encoding="utf-8"))

    assert len(records) == 5
    _assert_documented_records_match_registry(records)


def test_documented_raw_files_rejects_malformed_digest() -> None:
    markdown = _provenance_markdown(
        "| `movies.csv` | 4,803 | 5 | `not-a-sha` |",
        "| `rating.csv` | 20,000,263 | 6 | "
        "`9ec53ccb3e51c78fd31a451499f1c856c5c778766a7e7979683741ffb696adca` |",
    )

    with pytest.raises(ValueError, match="invalid SHA-256 for tmdb/movies.csv"):
        _documented_raw_files(markdown)


def test_documented_raw_files_rejects_malformed_table() -> None:
    markdown = "\n".join(
        (
            "## 1. TMDb 5000 Movie Dataset",
            _RAW_TABLE_HEADER,
            "not a Markdown table separator",
            "## 2. MovieLens 20M",
        )
    )

    with pytest.raises(ValueError, match="missing table separator"):
        _documented_raw_files(markdown)


def test_documented_raw_files_rejects_duplicate_path() -> None:
    digest = "a" * 64
    markdown = _provenance_markdown(
        "\n".join(
            (
                f"| `movies.csv` | 1 | 2 | `{digest}` |",
                f"| `movies.csv` | 3 | 4 | `{digest}` |",
            )
        ),
        f"| `rating.csv` | 5 | 6 | `{digest}` |",
    )

    with pytest.raises(ValueError, match="duplicate documented raw-file path: tmdb/movies.csv"):
        _documented_raw_files(markdown)


@pytest.mark.parametrize(
    ("path", "replacement"),
    (
        ("tmdb/movies.csv", ("0" * 64, 4803)),
        (
            "movielens/rating.csv",
            ("9ec53ccb3e51c78fd31a451499f1c856c5c778766a7e7979683741ffb696adca", 1),
        ),
    ),
)
def test_documented_registry_comparison_detects_checksum_and_row_count_drift(
    path: str, replacement: tuple[str, int]
) -> None:
    records = _documented_raw_files(DATA_PROVENANCE_PATH.read_text(encoding="utf-8"))
    records[path] = replacement

    with pytest.raises(AssertionError, match="differ from RAW_FILES"):
        _assert_documented_records_match_registry(records)


def test_documented_registry_comparison_detects_missing_record() -> None:
    records = _documented_raw_files(DATA_PROVENANCE_PATH.read_text(encoding="utf-8"))
    records.pop("tmdb/movies.csv")

    with pytest.raises(AssertionError, match="differ from RAW_FILES"):
        _assert_documented_records_match_registry(records)


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
