from __future__ import annotations

import subprocess
from pathlib import Path

from wocbots.experiments.provenance import capture_provenance


def test_git_sha_matches_head() -> None:
    prov = capture_provenance()
    expected = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    assert prov.git_sha.split("+", 1)[0] == expected


def test_dirty_suffix_appears_and_is_restored() -> None:
    target = Path("README.md")
    # BYTES, not text. `read_text`/`write_text` apply universal-newline translation: reading
    # collapses the file's endings to "\n", and writing re-expands them to `os.linesep`. On
    # Windows that turns this test's "restore" into a whole-file LF->CRLF rewrite, so the
    # tree stays dirty, the final assert fails, and README.md is left modified afterwards —
    # which is the real source of the phantom "CRLF noise" earlier handoffs warned about.
    # Byte IO round-trips exactly on every platform, which is the property this test needs.
    original = target.read_bytes()
    # The tree may ALREADY be dirty (unrelated WIP — the normal pre-commit state);
    # assert relative to that baseline, not against an assumed-clean tree.
    was_dirty = capture_provenance().git_sha.endswith("+dirty")
    try:
        target.write_bytes(original + b"\n<!-- W0-03 provenance test scratch -->\n")
        prov = capture_provenance()
        assert prov.git_sha.endswith("+dirty")
    finally:
        target.write_bytes(original)
    restored = capture_provenance()
    assert restored.git_sha.endswith("+dirty") == was_dirty
    # The restore must be byte-exact: a test that leaves the working tree modified poisons
    # every later `capture_provenance()` (they all inherit the "+dirty" suffix) and trains
    # the team to ignore a real dirty-tree signal.
    assert target.read_bytes() == original


def test_all_six_named_packages_present() -> None:
    prov = capture_provenance()
    for name in ("wocbots", "numpy", "pandas", "sklearn", "pydantic", "python"):
        assert name in prov.package_versions
        assert prov.package_versions[name]
