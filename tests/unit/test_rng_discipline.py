"""The RNG-discipline guard (W0-04 S3).

AST-walks every file under `src/wocbots/` and fails on:

1. Any attribute call on `numpy.random`/`np.random` EXCEPT `default_rng` and
   `SeedSequence`, and those two only inside `experiments/harness.py` (the
   one seed origin — plan §5).
2. `import random` / `from random import ...` anywhere.
3. `datetime.now`, `datetime.utcnow`, `time.time` outside
   `experiments/provenance.py` (the one licensed wall-clock site).

The allowlist below is named, in-test, and commented per entry (plan §7-S4)
— growing it is a reviewed, deliberate act, not a drive-by edit. The guard
is itself tested against a planted-violation fixture (§10.6): a guard that
can't catch a fixture it knows about is decoration.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "wocbots"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

# --- the named allowlist ------------------------------------------------
_RNG_ALLOWED_CALLS = {"default_rng", "SeedSequence"}
_RNG_ALLOWED_FILES = {"experiments/harness.py"}  # the one seed origin (plan §5)
_WALLCLOCK_ALLOWED_FILES = {"experiments/provenance.py"}  # the one licensed wall-clock site


@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    kind: str
    detail: str


def _numpy_random_attr(node: ast.Attribute) -> str | None:
    """If `node` is `<numpy|np>.random.<attr>`, return `<attr>`; else None."""
    inner = node.value
    if not isinstance(inner, ast.Attribute) or inner.attr != "random":
        return None
    if not isinstance(inner.value, ast.Name) or inner.value.id not in {"numpy", "np"}:
        return None
    return node.attr


def _wallclock_attr(node: ast.Attribute) -> str | None:
    if isinstance(node.value, ast.Name):
        if node.value.id == "datetime" and node.attr in {"now", "utcnow"}:
            return f"datetime.{node.attr}"
        if node.value.id == "time" and node.attr == "time":
            return "time.time"
    return None


def check_source(source: str, *, rel_path: str) -> list[Violation]:
    """Run the guard's checks against `source`, attributed to `rel_path`."""
    tree = ast.parse(source, filename=rel_path)
    found: list[Violation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "random":
                    found.append(Violation(rel_path, node.lineno, "random-import", "import random"))
        elif isinstance(node, ast.ImportFrom) and node.module == "random":
            found.append(Violation(rel_path, node.lineno, "random-import", "from random import ..."))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            rng_attr = _numpy_random_attr(node.func)
            if rng_attr is not None and (
                rng_attr not in _RNG_ALLOWED_CALLS or rel_path not in _RNG_ALLOWED_FILES
            ):
                found.append(Violation(rel_path, node.lineno, "numpy-random", f"numpy.random.{rng_attr}"))
            wallclock_attr = _wallclock_attr(node.func)
            if wallclock_attr is not None and rel_path not in _WALLCLOCK_ALLOWED_FILES:
                found.append(Violation(rel_path, node.lineno, "wall-clock", wallclock_attr))
    return found


def check_tree(root: Path) -> list[Violation]:
    """Run the guard against every `*.py` file under `root`."""
    found: list[Violation] = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        found.extend(check_source(path.read_text(encoding="utf-8"), rel_path=rel))
    return found


def _line_has_comment(source: str, needle: str) -> bool:
    for line in source.splitlines():
        if needle in line:
            return "#" in line
    return False


# --- the guard itself, run against the real tree ------------------------


def test_real_tree_is_clean() -> None:
    violations = check_tree(SRC_ROOT)
    assert violations == [], f"RNG/wall-clock guard violations: {violations}"


def test_allowlist_entries_are_commented() -> None:
    harness_src = (SRC_ROOT / "experiments" / "harness.py").read_text(encoding="utf-8")
    assert _line_has_comment(harness_src, "np.random.SeedSequence(")
    assert _line_has_comment(harness_src, "np.random.default_rng(")

    provenance_src = (SRC_ROOT / "experiments" / "provenance.py").read_text(encoding="utf-8")
    assert _line_has_comment(provenance_src, "datetime.now(")


def test_guard_allows_harness_seed_origin() -> None:
    harness_source = (SRC_ROOT / "experiments" / "harness.py").read_text(encoding="utf-8")
    violations = check_source(harness_source, rel_path="experiments/harness.py")
    assert [v for v in violations if v.kind == "numpy-random"] == []


def test_guard_allows_provenance_wallclock() -> None:
    provenance_source = (SRC_ROOT / "experiments" / "provenance.py").read_text(encoding="utf-8")
    violations = check_source(provenance_source, rel_path="experiments/provenance.py")
    assert [v for v in violations if v.kind == "wall-clock"] == []


# --- the guard's self-test: it must catch a planted violation of each kind


def _fixture_violations() -> list[Violation]:
    fixture_source = (FIXTURES_DIR / "rng_violations.py").read_text(encoding="utf-8")
    return check_source(fixture_source, rel_path="fixtures/rng_violations.py")


def test_guard_catches_random_import() -> None:
    kinds = {v.kind for v in _fixture_violations()}
    assert "random-import" in kinds


def test_guard_catches_numpy_random_outside_harness() -> None:
    kinds = {v.kind for v in _fixture_violations()}
    assert "numpy-random" in kinds


def test_guard_catches_wallclock_outside_provenance() -> None:
    kinds = {v.kind for v in _fixture_violations()}
    assert "wall-clock" in kinds


def test_guard_flags_exactly_the_three_planted_violations() -> None:
    kinds = sorted(v.kind for v in _fixture_violations())
    assert kinds == ["numpy-random", "random-import", "wall-clock"]
