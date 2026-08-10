"""W2-04 §9.2 — the ten-row agent-table reproduction (experiment kind + comparison emitter).

A PURE EXPERIMENT. It adds no mechanism: it configures W2-02's train/evaluate machinery
against W1's real Hollywood splits and reports what ten independently trained classifiers
score at 5 and 50 epochs. The ticket states its own epistemics — "if it misses, the bug is
upstream and this ticket is the detector, not the fix" — so nothing here may be tuned to
make the numbers land. Bands are asserted in the tests; deviations are escalated, never
absorbed (plan §3-D7).

Three things are load-bearing and must not be casually changed:

1. **Accuracy comes from the EVAL slice, never the test split** (spec §10.5, plan §3-D1).
   W1-05's 90/10 eval slice is carved off the TRAINING side; the test split is untouchable
   until final evaluation in W5. Measuring here on test would burn the holdout for a
   calibration check.
2. **The raw-data load is memoised; the SPLIT is not** (plan §3-D4). The W1-03 ETL takes no
   seed and returns the same frame every time, so re-running it per seeded run costs minutes
   to recompute an identical answer. Split membership IS the stochastic dimension the ten
   runs sample, so it is re-derived per run from that run's Generator. Caching the split
   too would report one run ten times with a fabricated std.
3. **The sanity row goes down its own constructor** (spec §10.9, plan §3-D5). `budget,
   revenue` is row 1 of §9.2 and is built by `build_sanity_agent`, the only path allowed to
   see `revenue`. It is reported here because pipeline validation is exactly the use §10.9
   permits, and it never enters a crowd.

This module calls NO RNG of its own: it only advances the Generator the harness hands it
(the W0-04 RNG-discipline guard).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from wocbots.agents import HOLLYWOOD_WEIGHTS
from wocbots.agents.classifier import ClassifierSpec, LabeledData
from wocbots.agents.training import build_sanity_agent, evaluate, train_agent
from wocbots.experiments.config import ExperimentConfig
from wocbots.experiments.hollywood_data import load_labeled_hollywood, materialize_split
from wocbots.experiments.manifest import Manifest
from wocbots.experiments.registry import register_kind

# Spec §9.2 reports accuracy at exactly these two epoch counts. The gap between the columns
# is part of the signature the ticket reproduces, so both live in ONE manifest (plan §3-D2).
# They sit exactly on `ClassifierSpec.epochs`' [5, 50] bounds — not a coincidence (spec §5.2).
EPOCH_COLUMNS: tuple[int, ...] = (5, 50)


@dataclass(frozen=True)
class AgentTableRow:
    """One row of spec §9.2: a feature set and its published accuracy at 5 and 50 epochs.

    `published` values are quoted from the spec table verbatim, as fractions. They are a
    SPEC CONSTANT — changing one is a spec change routed to the stakeholder, never a
    refactor (plan §11).
    """

    features: tuple[str, ...]
    published: Mapping[int, float]
    is_sanity: bool = False

    @property
    def slug(self) -> str:
        """Stable metric-key stem: the feature names joined by `+`, in spec order."""
        return "+".join(self.features)


# Spec §9.2, all ten rows, in the spec's own order (best-known first, weakest last). The
# sanity row leads because the spec leads with it: it is the pipeline canary, and if it is
# not ~100% then nothing below it means anything.
AGENT_TABLE_ROWS: tuple[AgentTableRow, ...] = (
    AgentTableRow(("budget", "revenue"), {5: 0.98, 50: 1.00}, is_sanity=True),
    AgentTableRow(("budget", "vote_average", "vote_count"), {5: 0.772, 50: 0.776}),
    AgentTableRow(("budget", "tmdb_popularity", "vote_average", "vote_count"), {5: 0.754, 50: 0.757}),
    AgentTableRow(("budget", "vote_count"), {5: 0.757, 50: 0.755}),
    AgentTableRow(
        ("budget", "tmdb_popularity", "tmdb_vote_average", "tmdb_vote_count"),
        {5: 0.728, 50: 0.749},
    ),
    AgentTableRow(("budget", "tmdb_vote_count", "ml_vote_count"), {5: 0.73, 50: 0.734}),
    AgentTableRow(("budget", "ml_vote_average", "ml_vote_count"), {5: 0.622, 50: 0.641}),
    AgentTableRow(("budget", "ml_vote_count"), {5: 0.603, 50: 0.619}),
    AgentTableRow(("budget", "tmdb_vote_average"), {5: 0.609, 50: 0.614}),
    AgentTableRow(("budget", "runtime"), {5: 0.539, 50: 0.564}),
)


def metric_key(row: AgentTableRow, epochs: int) -> str:
    """The manifest key for one table cell. Flat `str -> float` because that is the shape
    `RunResult.metrics` and `harness._aggregate` accept."""
    return f"{row.slug}@{epochs}ep"


def _accuracy_for_row(
    row: AgentTableRow,
    epochs: int,
    train_data: LabeledData,
    eval_data: LabeledData,
    rng: np.random.Generator,
) -> float:
    """Train one §9.2 row at one epoch count and score it on the eval slice.

    The sanity row takes `build_sanity_agent` (the `revenue` path); every other row takes
    `train_agent`, whose leak guard makes a `revenue`-seeing crowd agent unconstructible
    (spec §10.9). No pruning happens here — §5.3's 0.50 cut is a crowd-construction step,
    and §9.2 reports weak rows rather than dropping them (plan §4).
    """
    spec = ClassifierSpec(epochs=epochs)
    if row.is_sanity:
        trained = build_sanity_agent(
            train_data=train_data,
            eval_data=eval_data,
            rng=rng,
            spec=spec,
            confidence_weights=HOLLYWOOD_WEIGHTS,
        )
    else:
        trained = train_agent(
            features=row.features,
            train_data=train_data,
            eval_data=eval_data,
            spec=spec,
            confidence_weights=HOLLYWOOD_WEIGHTS,
            rng=rng,
        )
    metrics = evaluate(trained.classifier, eval_data, row.features)
    return metrics.accuracy


def agent_table_runner(config: ExperimentConfig, rng: np.random.Generator) -> Mapping[str, float]:
    """One seeded run of the §9.2 reproduction: 10 rows × 2 epoch columns = 20 cells.

    The harness owns the 10-run mean ± std (spec §9.1, plan §3-D3) — this returns one run's
    raw cells and aggregates nothing itself.
    """
    raw_root_param = config.params.get("raw_root", "data/raw")
    raw_root = str(raw_root_param) if isinstance(raw_root_param, (str, Path)) else "data/raw"

    labeled = load_labeled_hollywood(raw_root)
    # Split membership is this run's stochastic dimension (plan §3-D4); the shared helper
    # owns the eval-slice and revenue-scaling contracts (see `hollywood_data`).
    split = materialize_split(labeled, rng)

    results: dict[str, float] = {}
    for row in AGENT_TABLE_ROWS:
        for epochs in EPOCH_COLUMNS:
            results[metric_key(row, epochs)] = _accuracy_for_row(
                row, epochs, split.train_data, split.eval_data, rng
            )
    return results


register_kind("w2_04_agent_table", agent_table_runner)


def emit_comparison_table(manifest: Manifest) -> str:
    """Render the published-vs-measured comparison table from a written manifest (D6).

    Derived, never hand-typed: the report and the evidence cannot disagree because the report
    IS a view over `manifest.aggregate`. Deltas are in percentage POINTS (measured − published),
    which is the unit the ticket's ±3 band is stated in.
    """
    provenance = manifest.provenance
    lines = [
        "# W2-04 — §9.2 agent-table reproduction: published vs measured",
        "",
        f"**Config:** `{manifest.config.name}` · **Seed:** `{manifest.config.seed}` · "
        f"**Runs:** {len(manifest.runs)} · **Git SHA:** `{provenance.git_sha}` · "
        f"**Generated:** {provenance.created_utc}",
        "",
        "Accuracy on the W1-05 eval slice (train-side 90/10; the test split is untouched — "
        "spec §10.5). Every cell is a mean ± population std over "
        f"{len(manifest.runs)} seeded runs (spec §9.1). Δ is measured − published, in "
        "percentage points.",
        "",
        "| Agent features | Epochs | Published | Measured (mean ± std) | Δ (pts) | Within ±3 |",
        "|---|---:|---:|---|---:|:---:|",
    ]
    for row in AGENT_TABLE_ROWS:
        for epochs in EPOCH_COLUMNS:
            key = metric_key(row, epochs)
            summary = manifest.aggregate.get(key)
            if summary is None:
                lines.append(f"| `{row.slug}` | {epochs} | — | **MISSING FROM MANIFEST** | — | ✗ |")
                continue
            published_pts = row.published[epochs] * 100.0
            measured_pts = summary.mean * 100.0
            std_pts = summary.std * 100.0
            delta = measured_pts - published_pts
            within = "✓" if abs(delta) <= 3.0 else "✗"
            label = f"`{row.slug}`" + (" *(sanity)*" if row.is_sanity else "")
            lines.append(
                f"| {label} | {epochs} | {published_pts:.1f}% | "
                f"{measured_pts:.2f}% ± {std_pts:.2f} | {delta:+.2f} | {within} |"
            )
    lines.append("")
    return "\n".join(lines)
