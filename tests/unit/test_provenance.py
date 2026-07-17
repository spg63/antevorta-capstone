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
    original = target.read_text(encoding="utf-8")
    try:
        target.write_text(original + "\n<!-- W0-03 provenance test scratch -->\n", encoding="utf-8")
        prov = capture_provenance()
        assert prov.git_sha.endswith("+dirty")
    finally:
        target.write_text(original, encoding="utf-8")
    clean_prov = capture_provenance()
    assert not clean_prov.git_sha.endswith("+dirty")


def test_all_six_named_packages_present() -> None:
    prov = capture_provenance()
    for name in ("wocbots", "numpy", "pandas", "sklearn", "pydantic", "python"):
        assert name in prov.package_versions
        assert prov.package_versions[name]
