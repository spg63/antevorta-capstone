"""W2-04 tests — the §9.2 agent-table reproduction (plan §10).

Two tiers. T1-T6 are fast and run in CI: they pin the spec constant, the metric-key shape,
and manifest completeness without touching the 690 MB raw data. T7-T8 are the ticket's real
acceptance criteria — they need the full dataset, are `@pytest.mark.slow`, and are the
ticket-close gate rather than a per-commit check.

T7/T8 carry `xfail(strict=True)`. The bands they assert are the ticket's, unmodified; they
are expected to miss on the currently shipped data snapshot because W1-04's label gate is
open (see the plan §12-R1). `strict=True` is the point: the day the upstream data is fixed
and the table starts landing, this suite goes RED and forces someone to remove the marker
and flip the status honestly, rather than letting a silent pass go unnoticed.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from wocbots.data.splits import DEFAULT_FEATURE_COLUMNS
from wocbots.experiments.agent_table import (
    AGENT_TABLE_ROWS,
    EPOCH_COLUMNS,
    emit_comparison_table,
    metric_key,
)
from wocbots.experiments.manifest import read_manifest
from wocbots.experiments.registry import resolve_kind

RAW_ROOT = Path("data/raw")

# Spec §9.2 verbatim, re-typed here independently of the source constant so that T1 is a
# real cross-check rather than a tautology comparing the module against itself.
_SPEC_92 = {
    ("budget", "revenue"): (0.98, 1.00),
    ("budget", "vote_average", "vote_count"): (0.772, 0.776),
    ("budget", "tmdb_popularity", "vote_average", "vote_count"): (0.754, 0.757),
    ("budget", "vote_count"): (0.757, 0.755),
    ("budget", "tmdb_popularity", "tmdb_vote_average", "tmdb_vote_count"): (0.728, 0.749),
    ("budget", "tmdb_vote_count", "ml_vote_count"): (0.73, 0.734),
    ("budget", "ml_vote_average", "ml_vote_count"): (0.622, 0.641),
    ("budget", "ml_vote_count"): (0.603, 0.619),
    ("budget", "tmdb_vote_average"): (0.609, 0.614),
    ("budget", "runtime"): (0.539, 0.564),
}


def test_table_has_ten_rows_matching_spec_92() -> None:
    """T1: ten rows, published values equal to the spec table to the decimal."""
    assert len(AGENT_TABLE_ROWS) == 10
    measured = {row.features: (row.published[5], row.published[50]) for row in AGENT_TABLE_ROWS}
    assert measured == _SPEC_92


def test_exactly_one_sanity_row_and_it_is_the_leaky_one() -> None:
    """T2: `revenue` appears in exactly one row, and that row is the flagged canary (§10.9)."""
    sanity = [row for row in AGENT_TABLE_ROWS if row.is_sanity]
    assert len(sanity) == 1
    assert sanity[0].features == ("budget", "revenue")
    leaky = [row for row in AGENT_TABLE_ROWS if "revenue" in row.features]
    assert leaky == sanity


def test_every_non_sanity_feature_is_a_real_split_column() -> None:
    """T3: no row names a feature W1-05's feature matrix cannot supply."""
    available = set(DEFAULT_FEATURE_COLUMNS)
    for row in AGENT_TABLE_ROWS:
        if row.is_sanity:
            continue
        assert set(row.features) <= available, f"{row.slug} names a column W1-05 does not build"


def test_metric_keys_cover_ten_rows_times_two_columns() -> None:
    """T4: 20 distinct keys, one per (row, epoch column), in the documented format."""
    assert EPOCH_COLUMNS == (5, 50)
    keys = [metric_key(row, epochs) for row in AGENT_TABLE_ROWS for epochs in EPOCH_COLUMNS]
    assert len(keys) == 20
    assert len(set(keys)) == 20
    assert "budget+runtime@50ep" in keys
    assert "budget+revenue@5ep" in keys


def test_kind_is_registered() -> None:
    """T4b: the kind resolves, so a config naming it is runnable (W0-03 registry)."""
    assert resolve_kind("w2_04_agent_table") is not None


def _synthetic_frame(n: int, rng: np.random.Generator) -> object:
    """A tiny in-memory stand-in shaped like W1-04's labeled output, for T6.

    Deliberately NOT the real data: T6 pins determinism of the runner's plumbing, which is a
    property of the seeding contract, not of the dataset.
    """
    import pandas as pd

    frame = pd.DataFrame({col: rng.random(n) * 100.0 for col in DEFAULT_FEATURE_COLUMNS})
    frame["tmdbId"] = np.arange(n)
    frame["revenue"] = rng.random(n) * 1e6
    frame["label"] = (rng.random(n) > 0.5).astype(int)
    return frame


def test_runner_is_deterministic_given_the_same_generator(monkeypatch: pytest.MonkeyPatch) -> None:
    """T6: same Generator state in ⇒ identical metrics out (spec §9.1 reproducibility)."""
    from wocbots.experiments import agent_table
    from wocbots.experiments.config import ExperimentConfig

    frame = _synthetic_frame(400, np.random.default_rng(11))
    monkeypatch.setattr(agent_table, "load_labeled_hollywood", lambda _root: frame)

    config = ExperimentConfig(name="t6", kind="w2_04_agent_table", seed=1, n_runs=1)
    first = dict(agent_table.agent_table_runner(config, np.random.default_rng(99)))
    second = dict(agent_table.agent_table_runner(config, np.random.default_rng(99)))

    assert first == second
    assert len(first) == 20


def test_sanity_row_recovers_a_revenue_defined_label(monkeypatch: pytest.MonkeyPatch) -> None:
    """The canary must be able to see the answer, on data where the answer IS `revenue`.

    Regression pin for a real defect: `revenue` is not in W1-05's feature matrix, so the
    runner attaches it by hand. The first implementation attached it UNSCALED — raw dollars
    (~1e8) next to min-max features in [0, 1] — and the sanity agent collapsed to 55%, i.e.
    it reported "your data pipeline is broken" (spec §9.2) about the runner itself. Here the
    label is `revenue > 2 * budget` by construction, so a correctly-fed canary is near-perfect
    and a badly-scaled one is not.
    """
    import pandas as pd

    from wocbots.experiments import agent_table
    from wocbots.experiments.config import ExperimentConfig

    rng = np.random.default_rng(5)
    n = 600
    frame = pd.DataFrame({col: rng.random(n) * 100.0 for col in DEFAULT_FEATURE_COLUMNS})
    frame["tmdbId"] = np.arange(n)
    frame["budget"] = rng.random(n) * 1e8
    frame["revenue"] = frame["budget"] * (rng.random(n) * 6.0)
    frame["label"] = (frame["revenue"] > 2 * frame["budget"]).astype(int)

    monkeypatch.setattr(agent_table, "load_labeled_hollywood", lambda _root: frame)
    config = ExperimentConfig(name="canary", kind="w2_04_agent_table", seed=1, n_runs=1)
    metrics = agent_table.agent_table_runner(config, np.random.default_rng(3))

    assert metrics["budget+revenue@50ep"] > 0.90, (
        f"sanity agent scored {metrics['budget+revenue@50ep']:.3f} on a label that is a pure "
        "function of its own two features; the runner is not feeding it usable inputs"
    )


# --------------------------------------------------------------------- manifest + slow tier


def _latest_manifest() -> Path | None:
    candidates = sorted(Path("results/manifests").glob("w2_04_agent_table_*.json"))
    return candidates[-1] if candidates else None


def test_manifest_completeness() -> None:
    """T5: every cell traces to config + seed + git SHA; ten runs; all 20 keys per run."""
    path = _latest_manifest()
    if path is None:
        pytest.skip("no w2_04_agent_table manifest committed yet; run the harness first")

    manifest = read_manifest(path)
    assert manifest.config.kind == "w2_04_agent_table"
    assert manifest.config.seed is not None
    assert manifest.provenance.git_sha
    assert len(manifest.runs) == manifest.config.n_runs == 10

    expected = {metric_key(row, epochs) for row in AGENT_TABLE_ROWS for epochs in EPOCH_COLUMNS}
    assert set(manifest.aggregate) == expected
    for run in manifest.runs:
        assert set(run.metrics) == expected

    # The comparison table is a view over this manifest (plan §3-D6) and must render from it.
    table = emit_comparison_table(manifest)
    assert "MISSING FROM MANIFEST" not in table
    assert manifest.provenance.git_sha in table


def _measured_50ep() -> dict[str, float]:
    path = _latest_manifest()
    if path is None:
        pytest.skip("no w2_04_agent_table manifest committed yet; run the harness first")
    manifest = read_manifest(path)
    return {row.slug: manifest.aggregate[metric_key(row, 50)].mean * 100.0 for row in AGENT_TABLE_ROWS}


@pytest.mark.slow
@pytest.mark.xfail(
    strict=True,
    reason=(
        "W1-04 label gate OPEN: the shipped snapshot yields class balance 43.93/56.07 vs the "
        "published 47.5/52.5 (W1-04 tolerance is +/-1 pt), from a join of 4,227 vs the spec's "
        "4,722. Bands below are the ticket's, unmodified. Remove this marker when W1-04 is "
        "ruled; strict=True makes the suite fail loudly if the table starts passing."
    ),
)
def test_agent_table_reproduces_published_bands() -> None:
    """T7: all ten rows within +/-3 points of §9.2 at 50 epochs (ticket test req 1)."""
    measured = _measured_50ep()
    out_of_band = []
    for row in AGENT_TABLE_ROWS:
        published = row.published[50] * 100.0
        delta = measured[row.slug] - published
        if abs(delta) > 3.0:
            out_of_band.append(f"{row.slug}: {measured[row.slug]:.2f}% vs {published:.1f}% ({delta:+.2f})")
    assert not out_of_band, "rows outside the +/-3 point band at 50 epochs:\n" + "\n".join(out_of_band)


@pytest.mark.slow
@pytest.mark.xfail(
    strict=True,
    reason=(
        "Same upstream cause as the band test: W1-04's gate is open and W1-06 ranks `budget` "
        "LAST (point-biserial r=0.0224) against §9.2's expectation that it anchors every row. "
        "Orderings below are the ticket's, unmodified."
    ),
)
def test_orderings_preserved() -> None:
    """T8: the three orderings §9.2 calls out (ticket test req 1, second half)."""
    measured = _measured_50ep()
    sanity = "budget+revenue"
    best_real = "budget+vote_average+vote_count"
    worst_real = "budget+runtime"

    real = {slug: acc for slug, acc in measured.items() if slug != sanity}

    assert measured[sanity] >= 97.0, f"sanity agent at {measured[sanity]:.2f}%, expected ~100% (§9.2)"
    assert measured[sanity] == max(measured.values()), "sanity agent must top the table"
    assert real[best_real] == max(real.values()), (
        f"{best_real} should be the best real agent; got {max(real, key=lambda k: real[k])}"
    )
    assert real[worst_real] == min(real.values()), (
        f"{worst_real} should be the worst real agent; got {min(real, key=lambda k: real[k])}"
    )


@pytest.mark.slow
def test_comparison_table_artifact_matches_committed_manifest() -> None:
    """The committed markdown report must be regenerable from the committed manifest (D6)."""
    report = Path("results/W2-04_agent_table_comparison.md")
    path = _latest_manifest()
    if path is None or not report.exists():
        pytest.skip("manifest or comparison report not committed yet")

    manifest = read_manifest(path)
    rendered = emit_comparison_table(manifest)
    committed = report.read_text(encoding="utf-8")
    # The committed file carries an appended prose section (ticket S2); the generated table
    # must appear in it verbatim, so numbers cannot drift from their evidence.
    assert rendered.strip() in committed, "committed report does not match the manifest it cites"


def test_manifest_json_is_canonical() -> None:
    """Manifests are sorted-key JSON (W0-03 S3) — pinned so a hand-edit is visible in diff."""
    path = _latest_manifest()
    if path is None:
        pytest.skip("no w2_04_agent_table manifest committed yet; run the harness first")
    text = path.read_text(encoding="utf-8")
    payload = json.loads(text)
    assert json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n" == text
