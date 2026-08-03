"""W2-04 §9.2 — the ten-row agent-table reproduction (experiment).

This is a **pure experiment** module: it runs the W2-02/W2-03 machinery against the real
Hollywood data and puts the measured numbers beside the published ones. It deliberately
owns no mechanism. If a row misses its band, the bug is upstream (data pipeline, classifier,
init) and this module is the *detector*, not the fix — tuning W2-02 internals from in here
is the ticket's named forbidden shortcut.

Three things live here:

1. **The published table as data** (`PUBLISHED_ROWS`). Spec §9.2's ten rows, transcribed
   once, with both epoch columns. The 5-epoch column is part of the signature: the *gap*
   between 5 and 50 epochs is what says the agent layer is learning rather than memorising,
   so dropping it is a forbidden shortcut and a test pins that both columns are present.

2. **The runner** (`kind: "agent_table"`). One seeded run = build the split, then, for each
   epoch column, train the nine-agent explicit roster (W2-03's `ExplicitAssignment`) and the
   budget+revenue canary, and report every row's eval-slice accuracy. The harness spawns ten
   independent streams from one master seed and aggregates mean ± std per cell (spec §9.1) —
   this module never picks a seed, so "cherry-picked seeds" is not expressible here.

3. **The comparison table** (`AgentTableComparison`). Published beside measured, with a
   per-row delta and an in-band flag, plus the ordering checks and a `notes` block where
   every deviation is written up in prose rather than absorbed (ticket S2).

**Where the numbers come from.** Every accuracy is measured on the **eval slice** — the
90/10 hold-out taken off the *training* side by W1-05 (`make_split`). The test split is not
read anywhere in this module (spec §10.5, forbidden-shortcut #1).

**The canary stays off the crowd path.** The ten-row table contains budget+revenue, but that
row is built by `build_sanity_agent`, never by dealing features: the shipped roster config
holds only the nine real rows, and a `revenue` in it would be rejected at config load
(spec §10.9). The canary's cell is reported here as the pipeline check §9.2 asks for; it
does not enter any crowd, aggregation, or reported *crowd-level* run (forbidden-shortcut #6).

This module calls NO RNG of its own — it only advances the Generator the harness hands it.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from wocbots.agents.classifier import ClassifierSpec, LabeledData
from wocbots.agents.crowd import CrowdConfig, ExplicitAssignmentConfig, build_crowd
from wocbots.agents.training import build_sanity_agent
from wocbots.data.hollywood import build_hollywood_features
from wocbots.data.labels import variant_a_label
from wocbots.data.provenance import RAW_DATA_ROOT
from wocbots.data.splits import EXCLUDED_FROM_FEATURES, SplitArtifact, apply_scaling, make_split
from wocbots.experiments.config import ExperimentConfig
from wocbots.experiments.manifest import Manifest
from wocbots.experiments.registry import register_kind

# --------------------------------------------------------------- the published §9.2 table

# Spec §9.2 match semantics (§10.10, pitfall 10): ten stochastic runs on a ~740-row slice
# carry ~1.5-point standard errors, so the acceptance criterion is a BAND and an ORDERING,
# never a decimal. ±3 points is this ticket's stated tolerance.
BAND_POINTS = 3.0

# Both columns are normative. 5 epochs is not a warm-up to be skipped: the 5→50 delta is
# part of what the table asserts about the agent layer.
EPOCH_COLUMNS: tuple[int, ...] = (5, 50)

# Spec §9.1 default, restated here so the shipped config can be pinned against it.
REQUIRED_RUNS = 10


@dataclass(frozen=True)
class PublishedRow:
    """One row of the spec §9.2 table, transcribed verbatim.

    `accuracy_pct` is keyed by epoch column, in PERCENTAGE POINTS exactly as published.
    Measured accuracies live in [0, 1] everywhere else in the toolkit; the single
    conversion happens in `build_comparison`, and a test pins it.
    """

    features: tuple[str, ...]
    accuracy_pct: Mapping[int, float]
    is_sanity: bool = False


# Spec §9.2, "Individual agent MLPs after training (accuracy, 5 / 50 epochs)". Order is the
# spec's own (descending by 50-epoch accuracy, canary first). Column names are W1-03's ETL
# output vocabulary (`wocbots.data.hollywood.OUTPUT_COLUMNS`), which the spec table uses
# directly — `vote_average`/`vote_count` are the §4.3.5 COMBINED columns, distinct from the
# `tmdb_*`/`ml_*` per-source ones that also appear in the table.
PUBLISHED_ROWS: tuple[PublishedRow, ...] = (
    PublishedRow(("budget", "revenue"), {5: 98.0, 50: 100.0}, is_sanity=True),
    PublishedRow(("budget", "vote_average", "vote_count"), {5: 77.2, 50: 77.6}),
    PublishedRow(("budget", "tmdb_popularity", "vote_average", "vote_count"), {5: 75.4, 50: 75.7}),
    PublishedRow(("budget", "vote_count"), {5: 75.7, 50: 75.5}),
    PublishedRow(("budget", "tmdb_popularity", "tmdb_vote_average", "tmdb_vote_count"), {5: 72.8, 50: 74.9}),
    PublishedRow(("budget", "tmdb_vote_count", "ml_vote_count"), {5: 73.0, 50: 73.4}),
    PublishedRow(("budget", "ml_vote_average", "ml_vote_count"), {5: 62.2, 50: 64.1}),
    PublishedRow(("budget", "ml_vote_count"), {5: 60.3, 50: 61.9}),
    PublishedRow(("budget", "tmdb_vote_average"), {5: 60.9, 50: 61.4}),
    PublishedRow(("budget", "runtime"), {5: 53.9, 50: 56.4}),
)

# The three orderings §9.2 calls out in prose, named here so the reproduction test and the
# comparison manifest assert exactly the same things.
SANITY_FEATURES: tuple[str, ...] = ("budget", "revenue")
WORST_ROW_FEATURES: tuple[str, ...] = ("budget", "runtime")
BEST_REAL_ROW_FEATURES: tuple[str, ...] = ("budget", "vote_average", "vote_count")

# The union of every non-`revenue` column the table needs — the feature matrix W1-05 scales.
TABLE_FEATURE_COLUMNS: tuple[str, ...] = (
    "budget",
    "runtime",
    "tmdb_popularity",
    "tmdb_vote_average",
    "tmdb_vote_count",
    "ml_vote_average",
    "ml_vote_count",
    "vote_average",
    "vote_count",
)

ID_COLUMN = "tmdbId"
LABEL_COLUMN = "label"


def crowd_rows() -> tuple[PublishedRow, ...]:
    """The nine rows a crowd may legally contain (everything but the canary)."""
    return tuple(row for row in PUBLISHED_ROWS if not row.is_sanity)


def sanity_row() -> PublishedRow:
    """The budget+revenue canary row (spec §9.2/§10.9). Exactly one exists."""
    rows = [row for row in PUBLISHED_ROWS if row.is_sanity]
    if len(rows) != 1:  # pragma: no cover - structural, pinned by a test
        raise ValueError(f"expected exactly one sanity row in the §9.2 table, found {len(rows)}")
    return rows[0]


def row_key(features: Sequence[str], epochs: int) -> str:
    """The metric key for one table CELL: `<features joined by '+'>@<epochs>ep`.

    One flat string per cell because that is the shape `registry.RunnerFn` reports and the
    harness aggregates (`Mapping[str, float]`). Values are accuracies in [0, 1], NOT points
    — the comparison layer is the one place the unit changes.
    """
    return f"{'+'.join(features)}@{epochs}ep"


# ------------------------------------------------------------------------- runner params


class AgentTableParams(BaseModel):
    """The `params` block of an `agent_table` experiment config.

    Frozen + ``extra="forbid"`` (O3 ruling): a typo'd key is a `ValidationError`, not a
    silent default that quietly changes what the experiment means.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    crowd_config: str
    """Path (repo-relative) to the explicit nine-row roster crowd config."""

    dataset: Literal["hollywood", "synthetic"] = "hollywood"
    """`hollywood` reads the gitignored raw files under `data/raw/` (W1-01 provenance paths).
    `synthetic` generates a same-shaped frame so the whole path is runnable — and testable
    per-commit — without the datasets present. Only `hollywood` reproduces §9.2."""

    epochs: tuple[int, ...] = EPOCH_COLUMNS
    """Epoch columns to train. Both §9.2 columns by default; a test pins that the shipped
    config keeps 5 (dropping it is a forbidden shortcut)."""

    synthetic_rows: Annotated[int, Field(ge=100)] = 400
    """Row count for `dataset: synthetic`. Ignored for `hollywood`."""


# ------------------------------------------------------------------------ dataset assembly


@dataclass(frozen=True)
class AgentTableData:
    """The four matrices one run needs.

    The crowd pair carries the nine scaled table features (`revenue` structurally excluded by
    W1-05). The canary pair is budget+revenue, built on its OWN matrix — the only place
    `revenue` is materialised — so the crowd path never sees the column at all (§10.9).
    Both pairs are scaled with parameters fit on the TRAIN rows only (§4.3.9).
    """

    train: LabeledData
    eval: LabeledData
    sanity_train: LabeledData
    sanity_eval: LabeledData


def _labeled(frame: pd.DataFrame, columns: Sequence[str], labels: pd.Series) -> LabeledData:
    return LabeledData(
        features=tuple(columns),
        X=frame[list(columns)].to_numpy(dtype=np.float64),
        y=labels.to_numpy(dtype=np.int_),
    )


def _minmax(frame: pd.DataFrame, columns: Sequence[str], fit_mask: pd.Series) -> pd.DataFrame:
    """Min-max scale `columns`, fitting on `fit_mask` rows ONLY.

    Used for the canary's budget+revenue matrix, which W1-05's `SplitArtifact` deliberately
    cannot carry (`revenue` is excluded from the feature matrix there). Same train-only rule,
    same zero-span guard — leakage is impossible for the same reason it is in `apply_scaling`.
    """
    fitted = frame.loc[fit_mask, list(columns)]
    low = fitted.min()
    span = (fitted.max() - low).replace(0, 1.0)
    return ((frame[list(columns)] - low) / span).clip(lower=0.0, upper=1.0)


def build_agent_table_data(labeled_frame: pd.DataFrame, rng: np.random.Generator) -> AgentTableData:
    """Split + scale one seed's worth of data for the table (W1-05 artifacts, unmodified).

    `labeled_frame` must carry `ID_COLUMN`, `LABEL_COLUMN`, `revenue`, and every column in
    `TABLE_FEATURE_COLUMNS`. Only the Generator handed in is advanced; nothing here originates
    randomness (W0-04).
    """
    required = (*TABLE_FEATURE_COLUMNS, "revenue", ID_COLUMN, LABEL_COLUMN)
    missing = [c for c in required if c not in labeled_frame]
    if missing:
        raise ValueError(f"labeled frame is missing required columns: {missing}")
    ids = labeled_frame[ID_COLUMN]
    if ids.duplicated().any():
        # Split membership is recorded by id, so duplicates would silently place the same
        # row in two splits — a leak. Fail loudly rather than dedupe behind the caller's back.
        raise ValueError(f"{ID_COLUMN} must be unique; found {int(ids.duplicated().sum())} duplicates")

    artifact: SplitArtifact = make_split(
        labeled_frame,
        label_column=LABEL_COLUMN,
        rng=rng,
        id_column=ID_COLUMN,
        feature_columns=list(TABLE_FEATURE_COLUMNS),
    )
    train_mask = ids.isin(set(artifact.train_ids.tolist()))
    eval_mask = ids.isin(set(artifact.eval_ids.tolist()))

    scaled = apply_scaling(labeled_frame, artifact)
    sanity_scaled = _minmax(labeled_frame, SANITY_FEATURES, train_mask)
    labels = labeled_frame[LABEL_COLUMN]

    return AgentTableData(
        train=_labeled(scaled[train_mask], artifact.feature_columns, labels[train_mask]),
        eval=_labeled(scaled[eval_mask], artifact.feature_columns, labels[eval_mask]),
        sanity_train=_labeled(sanity_scaled[train_mask], SANITY_FEATURES, labels[train_mask]),
        sanity_eval=_labeled(sanity_scaled[eval_mask], SANITY_FEATURES, labels[eval_mask]),
    )


def load_hollywood_frame() -> pd.DataFrame:
    """Raw TMDb + MovieLens files -> W1-03 features -> W1-04 variant-(a) label.

    Reads the gitignored raw files at the W1-01 provenance paths. Raises a named
    `FileNotFoundError` when they are absent so callers can skip with a reason rather than
    fail obscurely — the datasets are never committed (`data/DATA_PROVENANCE.md`).

    NOTE for the reviewer: variant (a) (`revenue > 2 * budget`) is the spec §4.3.7 rule and
    the only computable label today; W1-04's reconciliation gate against the antevorta-db
    reference is still ESCALATED, not closed (see `data/DATA_PROVENANCE.md` §5-6). A §9.2 miss
    therefore has a known upstream suspect, which is exactly what this ticket exists to show.
    """
    paths = {
        "tmdb_movies": RAW_DATA_ROOT / "tmdb5000" / "tmdb_5000_movies.csv",
        "tmdb_credits": RAW_DATA_ROOT / "tmdb5000" / "tmdb_5000_credits.csv",
        "links": RAW_DATA_ROOT / "movielens20m" / "link.csv",
        "ml_movies": RAW_DATA_ROOT / "movielens20m" / "movie.csv",
        "ratings": RAW_DATA_ROOT / "movielens20m" / "rating.csv",
    }
    absent = [str(p) for p in paths.values() if not p.exists()]
    if absent:
        raise FileNotFoundError(
            "Hollywood raw data is not present locally (it is gitignored and never committed; "
            f"see data/DATA_PROVENANCE.md). Missing: {absent}"
        )

    features = build_hollywood_features(
        tmdb_movies=pd.read_csv(paths["tmdb_movies"], low_memory=False),
        tmdb_credits=pd.read_csv(paths["tmdb_credits"], low_memory=False),
        links=pd.read_csv(paths["links"]),
        ml_movies=pd.read_csv(paths["ml_movies"]),
        ratings=pd.read_csv(paths["ratings"]),
        required_feature_columns=list(TABLE_FEATURE_COLUMNS),
    )
    labeled = features.copy()
    labeled[LABEL_COLUMN] = variant_a_label(labeled)
    return labeled


def synthetic_frame(rng: np.random.Generator, n_rows: int) -> pd.DataFrame:
    """A same-shaped stand-in for the Hollywood frame, for running the path without the data.

    Deliberately NOT calibrated to §9.2: it exists so the machinery (config → split → train →
    comparison) is exercised per-commit, not so the table can "pass" without real data. A
    detector calibrated on invented numbers detects nothing — the reproduction test is the one
    that reads §9.2, and it is slow-marked and skips when the raw files are absent.
    """
    signal = rng.standard_normal(n_rows)
    budget = np.exp(rng.uniform(np.log(1e6), np.log(2e8), n_rows))
    revenue = budget * np.exp(0.8 * signal + 0.7)
    noise = rng.standard_normal(n_rows)
    frame = pd.DataFrame(
        {
            ID_COLUMN: np.arange(1, n_rows + 1, dtype=np.int64),
            "budget": budget,
            "revenue": revenue,
            # decreasing association with the label, so the synthetic rows at least span a
            # range rather than all landing on the same number
            "vote_count": np.exp(1.0 * signal + 0.2 * noise + 6.0),
            "vote_average": 6.0 + 0.9 * signal + 0.3 * noise,
            "tmdb_vote_count": np.exp(0.8 * signal + 0.4 * noise + 6.0),
            "tmdb_vote_average": 6.0 + 0.6 * signal + 0.6 * noise,
            "ml_vote_count": np.exp(0.5 * signal + 0.6 * noise + 5.0),
            "ml_vote_average": 6.0 + 0.4 * signal + 0.8 * noise,
            "tmdb_popularity": np.exp(0.7 * signal + 0.5 * noise + 2.0),
            "runtime": 90.0 + 30.0 * rng.standard_normal(n_rows),  # ~uninformative, as published
        }
    )
    frame[LABEL_COLUMN] = variant_a_label(frame)
    return frame


# -------------------------------------------------------------------------------- the runner


def _crowd_config_for(path: Path | str, epochs: int) -> CrowdConfig:
    """Load the roster config and set its epoch column, re-validating the classifier spec.

    Rebuilt through `ClassifierSpec(...)` rather than `model_copy`, so an out-of-range epoch
    count (§5.2 bounds it to 5–50) raises here instead of reaching sklearn.
    """
    base = CrowdConfig.from_yaml(path)
    spec = ClassifierSpec(**{**base.classifier.model_dump(), "epochs": epochs})
    return CrowdConfig(
        name=base.name,
        assignment=base.assignment,
        classifier=spec,
        confidence_weights=base.confidence_weights,
    )


def _accuracies_by_features(
    config: CrowdConfig, data: AgentTableData, rng: np.random.Generator
) -> dict[tuple[str, ...], float]:
    """Train the roster and return EVERY row's eval accuracy, pruned rows included.

    Read from the `CrowdManifest` rather than from `BuiltCrowd.agents` on purpose: a row that
    prunes (eval accuracy < 0.50, spec §5.3) is dropped from the usable crowd but still owes
    the table a cell. Taking it from `manifest.pruned` keeps the reported table complete and
    makes the prune visible instead of turning it into a missing key.
    """
    built = build_crowd(config=config, train_data=data.train, eval_data=data.eval, rng=rng)
    measured = {record.features: record.eval_accuracy for record in built.manifest.agents}
    measured.update({record.features: record.eval_accuracy for record in built.manifest.pruned})
    return measured


def agent_table_runner(config: ExperimentConfig, rng: np.random.Generator) -> Mapping[str, float]:
    """One seeded run of the §9.2 table: every row × every epoch column.

    Sequence per run: build this run's split from the threaded Generator, then for each epoch
    column train the nine-agent roster plus the canary on its own path. The SAME Generator
    threads through all of it in a fixed order, so one master seed reproduces the whole run.

    Returns eval-slice accuracies in [0, 1], keyed by `row_key`. The harness turns ten of
    these into mean ± std per cell; nothing here selects or inspects a seed.
    """
    params = AgentTableParams.model_validate(config.params)
    if params.dataset == "synthetic":
        frame = synthetic_frame(rng, params.synthetic_rows)
    else:
        frame = load_hollywood_frame()
    data = build_agent_table_data(frame, rng)

    expected = {row.features for row in crowd_rows()}
    metrics: dict[str, float] = {}
    for epochs in params.epochs:
        crowd_config = _crowd_config_for(params.crowd_config, epochs)
        measured = _accuracies_by_features(crowd_config, data, rng)
        if set(measured) != expected:
            raise ValueError(
                f"roster config {params.crowd_config!r} does not match the §9.2 non-canary rows; "
                f"missing={sorted(expected - set(measured))}, unexpected={sorted(set(measured) - expected)}"
            )
        for features, accuracy in measured.items():
            metrics[row_key(features, epochs)] = accuracy

        canary = build_sanity_agent(
            train_data=data.sanity_train,
            eval_data=data.sanity_eval,
            spec=crowd_config.classifier,
            confidence_weights=crowd_config.confidence_weights,
            rng=rng,
        )
        metrics[row_key(SANITY_FEATURES, epochs)] = canary.eval_metrics.accuracy
    return metrics


register_kind("agent_table", agent_table_runner)


# --------------------------------------------------------------------- the comparison table


class ComparisonCell(BaseModel):
    """One published-vs-measured cell. All accuracy fields are PERCENTAGE POINTS."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    features: tuple[str, ...]
    epochs: int
    metric_key: str
    """The harness manifest key this cell was read from — the trace back to the raw runs."""
    published_pct: float
    measured_mean_pct: float
    measured_std_pct: float
    delta_pct: float
    """measured - published. Signed on purpose: "3 points low" and "3 points high" are
    different findings, and an absolute value would hide which."""
    within_band: bool
    is_sanity: bool


class OrderingCheck(BaseModel):
    """One of §9.2's prose orderings, evaluated at the 50-epoch column."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    holds: bool
    detail: str


class AgentTableComparison(BaseModel):
    """The W2-04 deliverable (ticket S2): the table beside the published values.

    Every cell traces to config + seed + git SHA — `config` carries the seed, `n_runs`, and
    the roster config path; `crowd_config_sha256` pins the roster's exact bytes; `git_sha`
    and `created_utc` come from the harness manifest's provenance; `experiment_manifest`
    names the file holding the per-run numbers this table summarises. That chain is the
    ticket's second test requirement.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1
    experiment_manifest: str
    git_sha: str
    created_utc: str
    config: ExperimentConfig
    crowd_config_sha256: str
    band_points: float
    cells: tuple[ComparisonCell, ...]
    orderings: tuple[OrderingCheck, ...]
    notes: tuple[str, ...]
    """Prose. Every out-of-band row and every broken ordering gets a line here, so a
    deviation is written up rather than absorbed into a mean (ticket S2)."""

    @property
    def out_of_band(self) -> tuple[ComparisonCell, ...]:
        return tuple(cell for cell in self.cells if not cell.within_band)

    @property
    def reproduces(self) -> bool:
        """True iff every 50-epoch cell is in band and every ordering holds."""
        in_band = all(cell.within_band for cell in self.cells if cell.epochs == 50)
        return in_band and all(check.holds for check in self.orderings)


def _ordering_checks(measured_50: Mapping[tuple[str, ...], float]) -> tuple[OrderingCheck, ...]:
    """The three orderings §9.2 states in prose, at 50 epochs.

    Evaluated from measured means only — an ordering that holds "because the published table
    says so" would check nothing.
    """
    checks: list[OrderingCheck] = []
    canary = measured_50.get(SANITY_FEATURES)
    others = {f: v for f, v in measured_50.items() if f != SANITY_FEATURES}

    if canary is None or not others:
        return (OrderingCheck(name="orderings", holds=False, detail="table incomplete at 50 epochs"),)

    top = max(others.values())
    checks.append(
        OrderingCheck(
            name="sanity_agent_tops_the_table",
            holds=canary >= top,
            detail=f"budget+revenue {canary:.1f} vs best real agent {top:.1f} (spec §9.2: ~100)",
        )
    )

    worst_features = min(others, key=lambda f: others[f])
    checks.append(
        OrderingCheck(
            name="budget_runtime_is_worst",
            holds=worst_features == WORST_ROW_FEATURES,
            detail=f"lowest real agent is {'+'.join(worst_features)} at {others[worst_features]:.1f}",
        )
    )

    best_features = max(others, key=lambda f: others[f])
    checks.append(
        OrderingCheck(
            name="best_real_agent_is_budget_vote_average_vote_count",
            holds=best_features == BEST_REAL_ROW_FEATURES,
            detail=f"highest real agent is {'+'.join(best_features)} at {others[best_features]:.1f}",
        )
    )
    return tuple(checks)


def _sha256_of_text(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_comparison(
    manifest: Manifest,
    *,
    experiment_manifest: str,
    extra_notes: Sequence[str] = (),
) -> AgentTableComparison:
    """Turn a harness `Manifest` into the published-vs-measured table (ticket S2).

    The ONE place accuracies change unit: the harness records [0, 1] accuracies, §9.2
    publishes percentage points, so every measured value is multiplied by 100 here and
    nowhere else. A missing cell is an error, not a blank — a table with a hole in it would
    read as "in band" by omission.
    """
    params = AgentTableParams.model_validate(manifest.config.params)
    cells: list[ComparisonCell] = []
    measured_50: dict[tuple[str, ...], float] = {}

    for row in PUBLISHED_ROWS:
        for epochs in params.epochs:
            key = row_key(row.features, epochs)
            summary = manifest.aggregate.get(key)
            if summary is None:
                raise KeyError(f"manifest has no aggregate for cell {key!r}; the table is incomplete")
            published = row.accuracy_pct[epochs]
            mean_pct = summary.mean * 100.0
            std_pct = summary.std * 100.0
            delta = mean_pct - published
            if epochs == 50:
                measured_50[row.features] = mean_pct
            cells.append(
                ComparisonCell(
                    features=row.features,
                    epochs=epochs,
                    metric_key=key,
                    published_pct=published,
                    measured_mean_pct=mean_pct,
                    measured_std_pct=std_pct,
                    delta_pct=delta,
                    # inclusive at exactly ±3: the ticket says "within ±3 points", and both
                    # sides of that boundary are pinned in the tests
                    within_band=abs(delta) <= BAND_POINTS,
                    is_sanity=row.is_sanity,
                )
            )

    orderings = _ordering_checks(measured_50) if 50 in params.epochs else ()

    notes = [
        f"{cell.metric_key}: measured {cell.measured_mean_pct:.1f} ± {cell.measured_std_pct:.1f} vs "
        f"published {cell.published_pct:.1f} (delta {cell.delta_pct:+.1f} pts, outside ±{BAND_POINTS:g}). "
        f"Investigate upstream before adjusting anything in W2-02/W2-03 (ticket: a miss files a bug "
        f"upstream, it does not tune this layer)."
        for cell in cells
        if not cell.within_band
    ]
    notes += [
        f"ordering {check.name!r} does NOT hold: {check.detail}." for check in orderings if not check.holds
    ]
    notes += list(extra_notes)

    return AgentTableComparison(
        experiment_manifest=experiment_manifest,
        git_sha=manifest.provenance.git_sha,
        created_utc=manifest.provenance.created_utc,
        config=manifest.config,
        crowd_config_sha256=_sha256_of_text(params.crowd_config),
        band_points=BAND_POINTS,
        cells=tuple(cells),
        orderings=orderings,
        notes=tuple(notes),
    )


def render_comparison(comparison: AgentTableComparison) -> str:
    """The comparison as a Markdown table, for pasting into a closing report or PR body."""
    header = (
        "| Agent features | Epochs | Published | Measured (mean ± std) | Delta | In band |\n"
        "|---|---:|---:|---|---:|:--:|\n"
    )
    rows = "".join(
        f"| {'+'.join(cell.features)}{' *(sanity)*' if cell.is_sanity else ''} | {cell.epochs} | "
        f"{cell.published_pct:.1f} | {cell.measured_mean_pct:.1f} ± {cell.measured_std_pct:.1f} | "
        f"{cell.delta_pct:+.1f} | {'yes' if cell.within_band else 'NO'} |\n"
        for cell in comparison.cells
    )
    return header + rows


def write_comparison(comparison: AgentTableComparison, path: Path | str) -> Path:
    """Write the comparison as canonical JSON — same form as the crowd/experiment manifests
    (`sort_keys=True`, UTF-8, trailing newline) so evidence files diff cleanly."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = comparison.model_dump(mode="json")
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def read_comparison(path: Path | str) -> AgentTableComparison:
    """Read + validate a comparison JSON file back into an `AgentTableComparison`."""
    return AgentTableComparison.model_validate_json(Path(path).read_text(encoding="utf-8"))


def roster_from_published() -> ExplicitAssignmentConfig:
    """The nine non-canary rows as an `ExplicitAssignment` config, built from `PUBLISHED_ROWS`.

    Used by the test that pins the shipped YAML against the spec table: the config file and
    this function must agree, so a hand-edit to either is caught rather than trusted.
    """
    return ExplicitAssignmentConfig(
        policy="explicit",
        anchors=("budget",),
        agents=tuple(row.features for row in crowd_rows()),
    )


def assert_no_revenue_in_features(columns: Sequence[str]) -> None:
    """Guard for callers assembling a crowd feature list from this module's constants."""
    leaked = sorted(EXCLUDED_FROM_FEATURES.intersection(columns))
    if leaked:
        raise ValueError(f"{leaked} must not appear in crowd features (spec §4.3.9/§10.9)")


__all__ = [
    "BAND_POINTS",
    "BEST_REAL_ROW_FEATURES",
    "EPOCH_COLUMNS",
    "ID_COLUMN",
    "LABEL_COLUMN",
    "PUBLISHED_ROWS",
    "REQUIRED_RUNS",
    "SANITY_FEATURES",
    "TABLE_FEATURE_COLUMNS",
    "WORST_ROW_FEATURES",
    "AgentTableComparison",
    "AgentTableData",
    "AgentTableParams",
    "ComparisonCell",
    "OrderingCheck",
    "PublishedRow",
    "agent_table_runner",
    "assert_no_revenue_in_features",
    "build_agent_table_data",
    "build_comparison",
    "crowd_rows",
    "load_hollywood_frame",
    "read_comparison",
    "render_comparison",
    "roster_from_published",
    "row_key",
    "sanity_row",
    "synthetic_frame",
    "write_comparison",
]
