"""W2-04 — the §9.2 agent-table reproduction.

The ticket has exactly two test requirements:

  1. **Reproduction (slow):** all ten rows within ±3 points at 50 epochs, orderings preserved
     (budget+revenue ≈ 100 top; budget+runtime worst; budget+vote_average+vote_count best
     real agent). That is `test_reproduction_hollywood_real_data`, marked slow and skipped
     with a named reason when the (gitignored) raw datasets are absent.
  2. **Manifest completeness:** every cell traces to config + seed + SHA.

Everything else here defends the ticket's forbidden shortcuts — no cherry-picked seeds, the
5-epoch column is never dropped, and nothing in W2-02/W2-03 gets tuned from this ticket — and
pins the machinery the slow test depends on so a break shows up per-commit rather than weekly.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from pydantic import ValidationError

from wocbots.agents.crowd import CrowdConfig, ExplicitAssignmentConfig
from wocbots.experiments.agent_table import (
    BAND_POINTS,
    EPOCH_COLUMNS,
    LABEL_COLUMN,
    PUBLISHED_ROWS,
    REQUIRED_RUNS,
    SANITY_FEATURES,
    TABLE_FEATURE_COLUMNS,
    WORST_ROW_FEATURES,
    AgentTableParams,
    build_agent_table_data,
    build_comparison,
    crowd_rows,
    load_hollywood_frame,
    read_comparison,
    render_comparison,
    roster_from_published,
    row_key,
    sanity_row,
    synthetic_frame,
    write_comparison,
)
from wocbots.experiments.config import ExperimentConfig
from wocbots.experiments.harness import run_experiment
from wocbots.experiments.manifest import Manifest, MetricSummary, RunResult, read_manifest
from wocbots.experiments.provenance import Provenance
from wocbots.experiments.registry import registered_kinds

REPO_ROOT = Path(__file__).resolve().parents[2]
ROSTER_CONFIG = REPO_ROOT / "configs" / "crowd_hollywood_agent_table.yaml"
HOLLYWOOD_CONFIG = REPO_ROOT / "configs" / "agent_table_hollywood.yaml"
SMOKE_CONFIG = REPO_ROOT / "configs" / "agent_table_smoke.yaml"


# --------------------------------------------------------------- the published table itself


def test_published_table_has_the_spec_s_ten_rows() -> None:
    assert len(PUBLISHED_ROWS) == 10
    assert len(crowd_rows()) == 9
    assert sanity_row().features == SANITY_FEATURES


def test_published_values_match_spec_9_2_verbatim() -> None:
    """Transcription pin. If the spec table is ever amended, this test is the one that has to
    be edited deliberately — the numbers cannot drift silently."""
    expected = {
        ("budget", "revenue"): (98.0, 100.0),
        ("budget", "vote_average", "vote_count"): (77.2, 77.6),
        ("budget", "tmdb_popularity", "vote_average", "vote_count"): (75.4, 75.7),
        ("budget", "vote_count"): (75.7, 75.5),
        ("budget", "tmdb_popularity", "tmdb_vote_average", "tmdb_vote_count"): (72.8, 74.9),
        ("budget", "tmdb_vote_count", "ml_vote_count"): (73.0, 73.4),
        ("budget", "ml_vote_average", "ml_vote_count"): (62.2, 64.1),
        ("budget", "ml_vote_count"): (60.3, 61.9),
        ("budget", "tmdb_vote_average"): (60.9, 61.4),
        ("budget", "runtime"): (53.9, 56.4),
    }
    actual = {row.features: (row.accuracy_pct[5], row.accuracy_pct[50]) for row in PUBLISHED_ROWS}
    assert actual == expected


def test_both_epoch_columns_are_published_for_every_row() -> None:
    """Forbidden shortcut: skipping the 5-epoch column. The 5→50 gap is part of the signature."""
    assert EPOCH_COLUMNS == (5, 50)
    for row in PUBLISHED_ROWS:
        assert set(row.accuracy_pct) == {5, 50}, row.features


def test_every_row_is_budget_anchored_and_features_are_etl_columns() -> None:
    from wocbots.data.hollywood import OUTPUT_COLUMNS

    for row in PUBLISHED_ROWS:
        assert row.features[0] == "budget", row.features
        assert len(set(row.features)) == len(row.features), row.features
        for feature in row.features:
            assert feature in OUTPUT_COLUMNS, f"{feature} is not a W1-03 ETL output column"


def test_row_keys_are_unique_across_the_whole_table() -> None:
    keys = [row_key(row.features, epochs) for row in PUBLISHED_ROWS for epochs in EPOCH_COLUMNS]
    assert len(set(keys)) == len(keys) == 20


def test_table_feature_columns_exclude_revenue() -> None:
    """§4.3.9 / §10.9: the scaled crowd matrix must never carry `revenue`."""
    assert "revenue" not in TABLE_FEATURE_COLUMNS
    assert set(TABLE_FEATURE_COLUMNS) == {f for row in crowd_rows() for f in row.features}


# ------------------------------------------------------------------------- shipped configs


def test_shipped_roster_matches_published_table() -> None:
    """The YAML roster and `PUBLISHED_ROWS` must agree — neither is trusted over the other."""
    config = CrowdConfig.from_yaml(ROSTER_CONFIG)
    assert isinstance(config.assignment, ExplicitAssignmentConfig)
    assert config.assignment.agents == roster_from_published().agents
    assert config.assignment.anchors == ("budget",)


def test_shipped_roster_omits_the_canary_row() -> None:
    """The ten-row table is nine crowd agents + one canary built elsewhere (§10.9)."""
    config = CrowdConfig.from_yaml(ROSTER_CONFIG)
    assert isinstance(config.assignment, ExplicitAssignmentConfig)
    assert SANITY_FEATURES not in config.assignment.agents
    assert all("revenue" not in agent for agent in config.assignment.agents)


def test_roster_config_would_reject_the_canary_row(tmp_path: Path) -> None:
    """Defense in depth: adding budget+revenue to this config is a load-time error, so the
    canary cannot slip into the crowd path by editing YAML (spec §10.9)."""
    raw = yaml.safe_load(ROSTER_CONFIG.read_text(encoding="utf-8"))
    raw["assignment"]["agents"].append(["budget", "revenue"])
    path = tmp_path / "leaky.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    with pytest.raises(ValidationError, match="leak the label"):
        CrowdConfig.from_yaml(path)


def test_hollywood_config_is_ten_runs_and_keeps_both_columns() -> None:
    """Forbidden shortcuts: single-run numbers, cherry-picked seeds, dropping the 5-ep column."""
    config = ExperimentConfig.from_yaml(HOLLYWOOD_CONFIG)
    params = AgentTableParams.model_validate(config.params)
    assert config.kind == "agent_table"
    assert config.n_runs == REQUIRED_RUNS
    assert params.dataset == "hollywood"
    assert params.epochs == EPOCH_COLUMNS
    assert Path(params.crowd_config) == Path("configs/crowd_hollywood_agent_table.yaml")


def test_agent_table_kind_is_registered() -> None:
    import wocbots.experiments.kinds  # noqa: F401  (import side effect: registration)

    assert "agent_table" in registered_kinds()


def test_unknown_param_key_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentTableParams.model_validate({"crowd_config": str(ROSTER_CONFIG), "epochs": [5, 50], "epocs": [5]})


def test_out_of_range_epochs_rejected_before_sklearn() -> None:
    """§5.2 bounds epochs to 5–50; the runner rebuilds `ClassifierSpec` so a bad column fails
    at config time rather than deep inside a fit."""
    from wocbots.experiments.agent_table import _crowd_config_for

    with pytest.raises(ValidationError):
        _crowd_config_for(ROSTER_CONFIG, 500)


# --------------------------------------------------------------------- split + scaling path


def _frame(seed: int = 3, n_rows: int = 400) -> pd.DataFrame:
    return synthetic_frame(np.random.default_rng(seed), n_rows)


def test_synthetic_frame_has_every_column_the_table_needs() -> None:
    frame = _frame()
    for column in (*TABLE_FEATURE_COLUMNS, "revenue", "tmdbId", LABEL_COLUMN):
        assert column in frame.columns
    assert set(frame[LABEL_COLUMN].unique()) == {0, 1}


def test_split_is_scaled_train_only_and_eval_is_off_the_train_side() -> None:
    """Spec §10.5 / §4.3.9: eval is a slice of TRAIN, and no test row informs the scaler."""
    frame = _frame()
    data = build_agent_table_data(frame, np.random.default_rng(11))
    assert data.train.features == tuple(TABLE_FEATURE_COLUMNS)
    assert data.sanity_train.features == SANITY_FEATURES
    # scaler fit on train ⇒ train values land in [0, 1] by construction
    assert data.train.X.min() >= 0.0 and data.train.X.max() <= 1.0
    assert data.sanity_train.X.min() >= 0.0 and data.sanity_train.X.max() <= 1.0
    # 90/10 eval slice off the 80% train side, so eval is much smaller than train
    assert 0 < data.eval.X.shape[0] < data.train.X.shape[0]
    assert data.eval.X.shape[0] == data.sanity_eval.X.shape[0]


def test_split_rejects_duplicate_ids() -> None:
    """Duplicate ids would place one row in two splits — a leak. It must raise, not dedupe."""
    frame = _frame()
    frame.loc[1, "tmdbId"] = frame.loc[0, "tmdbId"]
    with pytest.raises(ValueError, match="must be unique"):
        build_agent_table_data(frame, np.random.default_rng(0))


def test_split_rejects_a_frame_missing_a_table_column() -> None:
    frame = _frame().drop(columns=["runtime"])
    with pytest.raises(ValueError, match="missing required columns"):
        build_agent_table_data(frame, np.random.default_rng(0))


def test_build_agent_table_data_is_deterministic_under_seed() -> None:
    frame = _frame()
    a = build_agent_table_data(frame, np.random.default_rng(5))
    b = build_agent_table_data(frame, np.random.default_rng(5))
    assert np.array_equal(a.train.X, b.train.X)
    assert np.array_equal(a.eval.y, b.eval.y)
    assert np.array_equal(a.sanity_train.X, b.sanity_train.X)


# ------------------------------------------------------------------------------- the runner


def test_runner_emits_every_cell_of_the_ten_row_table() -> None:
    """One run must report all 10 rows × both epoch columns — a missing cell would silently
    read as "in band" downstream."""
    from wocbots.experiments.agent_table import agent_table_runner

    config = ExperimentConfig(
        name="t",
        kind="agent_table",
        seed=1,
        n_runs=1,
        params={"crowd_config": str(ROSTER_CONFIG), "dataset": "synthetic", "epochs": [5, 50]},
    )
    metrics = agent_table_runner(config, np.random.default_rng(1))
    expected = {row_key(row.features, ep) for row in PUBLISHED_ROWS for ep in (5, 50)}
    assert set(metrics) == expected
    assert all(0.0 <= v <= 1.0 for v in metrics.values())


def test_runner_is_deterministic_under_the_same_seed() -> None:
    from wocbots.experiments.agent_table import agent_table_runner

    config = ExperimentConfig(
        name="t",
        kind="agent_table",
        seed=1,
        n_runs=1,
        params={"crowd_config": str(ROSTER_CONFIG), "dataset": "synthetic", "epochs": [5]},
    )
    first = dict(agent_table_runner(config, np.random.default_rng(42)))
    second = dict(agent_table_runner(config, np.random.default_rng(42)))
    assert first == second


def test_runner_seed_actually_threads() -> None:
    """Guards a constant-seed bug: different Generator state must move the numbers."""
    from wocbots.experiments.agent_table import agent_table_runner

    config = ExperimentConfig(
        name="t",
        kind="agent_table",
        seed=1,
        n_runs=1,
        params={"crowd_config": str(ROSTER_CONFIG), "dataset": "synthetic", "epochs": [5]},
    )
    first = dict(agent_table_runner(config, np.random.default_rng(1)))
    second = dict(agent_table_runner(config, np.random.default_rng(2)))
    assert first != second


def test_runner_rejects_a_roster_that_is_not_the_published_nine(tmp_path: Path) -> None:
    """A roster that has drifted from §9.2 must fail loudly, not silently report 8 rows."""
    from wocbots.experiments.agent_table import agent_table_runner

    raw = yaml.safe_load(ROSTER_CONFIG.read_text(encoding="utf-8"))
    raw["assignment"]["agents"] = raw["assignment"]["agents"][:-1]
    path = tmp_path / "short.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    config = ExperimentConfig(
        name="t",
        kind="agent_table",
        seed=1,
        n_runs=1,
        params={"crowd_config": str(path), "dataset": "synthetic", "epochs": [5]},
    )
    with pytest.raises(ValueError, match="does not match the §9.2 non-canary rows"):
        agent_table_runner(config, np.random.default_rng(0))


def test_a_pruned_row_still_reports_its_cell() -> None:
    """Spec §5.3 drops an agent below 0.50 from the usable crowd — but the TABLE still owes
    that row a number. Read from the crowd manifest (kept + pruned), never from the survivors
    alone, or a bad row would vanish from the report instead of showing up as bad."""
    from wocbots.experiments.agent_table import _accuracies_by_features, _crowd_config_for

    frame = _frame()
    data = build_agent_table_data(frame, np.random.default_rng(9))
    # invert the eval labels so every agent scores below 0.50 and prunes
    inverted = type(data)(
        train=data.train,
        eval=type(data.eval)(features=data.eval.features, X=data.eval.X, y=1 - data.eval.y),
        sanity_train=data.sanity_train,
        sanity_eval=data.sanity_eval,
    )
    config = _crowd_config_for(ROSTER_CONFIG, 5)
    measured = _accuracies_by_features(config, inverted, np.random.default_rng(9))
    assert set(measured) == {row.features for row in crowd_rows()}
    assert any(v < 0.50 for v in measured.values()), "expected the inverted slice to prune rows"


def test_end_to_end_smoke_config_produces_a_manifest_and_comparison(tmp_path: Path) -> None:
    """Preamble §0.3: the whole path runs on synthetic data before the real datasets exist.
    Config -> harness -> manifest -> comparison, with nothing hand-assembled in between."""
    config = ExperimentConfig.from_yaml(SMOKE_CONFIG)
    manifest_path = run_experiment(config, manifest_dir=tmp_path)
    manifest = read_manifest(manifest_path)

    assert len(manifest.runs) == config.n_runs
    assert set(manifest.aggregate) == {row_key(row.features, ep) for row in PUBLISHED_ROWS for ep in (5, 50)}
    comparison = build_comparison(manifest, experiment_manifest=manifest_path.name)
    assert len(comparison.cells) == 20
    assert len(comparison.orderings) == 3


# -------------------------------------------------------------- the comparison table itself


def _manifest_from(means: dict[str, float], *, seed: int = 20260803, n_runs: int = 10) -> Manifest:
    """A Manifest with hand-chosen aggregate means, so the comparison arithmetic is pinned
    against exact numbers rather than whatever a training run happened to produce."""
    config = ExperimentConfig(
        name="agent_table_test",
        kind="agent_table",
        seed=seed,
        n_runs=n_runs,
        params={"crowd_config": str(ROSTER_CONFIG), "dataset": "hollywood", "epochs": [5, 50]},
    )
    return Manifest(
        provenance=Provenance(
            created_utc="2026-08-03T12:00:00+00:00",
            git_sha="0123456789abcdef0123456789abcdef01234567",
            package_versions={"wocbots": "0.1.0"},
            platform="test",
        ),
        config=config,
        runs=[RunResult(run_index=i, metrics=means) for i in range(n_runs)],
        aggregate={k: MetricSummary(mean=v, std=0.015) for k, v in means.items()},
    )


def _perfect_means() -> dict[str, float]:
    """Measured values equal to the published table, in [0, 1] — the in-band baseline."""
    return {
        row_key(row.features, ep): row.accuracy_pct[ep] / 100.0 for row in PUBLISHED_ROWS for ep in (5, 50)
    }


def test_comparison_arithmetic_is_exact() -> None:
    """Unit conversion + delta, hand-computed. budget+vote_count @50 publishes 75.5; a
    measured 0.7400 must read 74.0, delta -1.5, in band."""
    means = _perfect_means()
    means[row_key(("budget", "vote_count"), 50)] = 0.7400
    comparison = build_comparison(_manifest_from(means), experiment_manifest="m.json")
    cell = next(c for c in comparison.cells if c.features == ("budget", "vote_count") and c.epochs == 50)
    assert cell.published_pct == pytest.approx(75.5)
    assert cell.measured_mean_pct == pytest.approx(74.0)
    assert cell.measured_std_pct == pytest.approx(1.5)
    assert cell.delta_pct == pytest.approx(-1.5)
    assert cell.within_band is True


@pytest.mark.parametrize(
    ("measured", "expected_in_band"),
    [
        (0.725, True),  # delta exactly -3.0 -> inclusive, in band
        (0.785, True),  # delta exactly +3.0 -> inclusive, in band
        (0.7249, False),  # a hair beyond -3.0
        (0.7851, False),  # a hair beyond +3.0
    ],
)
def test_band_boundary_is_pinned_on_both_sides(measured: float, expected_in_band: bool) -> None:
    """±3 points, inclusive at exactly 3. Published here is 75.5 (budget+vote_count @50)."""
    assert BAND_POINTS == 3.0
    means = _perfect_means()
    means[row_key(("budget", "vote_count"), 50)] = measured
    comparison = build_comparison(_manifest_from(means), experiment_manifest="m.json")
    cell = next(c for c in comparison.cells if c.features == ("budget", "vote_count") and c.epochs == 50)
    assert cell.within_band is expected_in_band


def test_a_deviation_is_written_up_not_absorbed() -> None:
    """Ticket S2: deviations appear in prose in the manifest. An out-of-band row must produce
    a note naming the cell and both numbers."""
    means = _perfect_means()
    means[row_key(("budget", "runtime"), 50)] = 0.40  # 16.4 points low
    comparison = build_comparison(_manifest_from(means), experiment_manifest="m.json")
    assert comparison.reproduces is False
    assert len(comparison.out_of_band) == 1
    note = next(n for n in comparison.notes if "budget+runtime@50ep" in n)
    assert "40.0" in note and "56.4" in note and "-16.4" in note


def test_extra_notes_are_carried_through() -> None:
    comparison = build_comparison(
        _manifest_from(_perfect_means()),
        experiment_manifest="m.json",
        extra_notes=("W1-04's label gate is still escalated; see DATA_PROVENANCE.md §6.",),
    )
    assert any("W1-04" in note for note in comparison.notes)


def test_a_missing_cell_is_an_error_not_a_blank() -> None:
    means = _perfect_means()
    del means[row_key(("budget", "runtime"), 5)]
    with pytest.raises(KeyError, match="table is incomplete"):
        build_comparison(_manifest_from(means), experiment_manifest="m.json")


def test_orderings_hold_on_the_published_values() -> None:
    comparison = build_comparison(_manifest_from(_perfect_means()), experiment_manifest="m.json")
    assert {c.name for c in comparison.orderings} == {
        "sanity_agent_tops_the_table",
        "budget_runtime_is_worst",
        "best_real_agent_is_budget_vote_average_vote_count",
    }
    assert all(check.holds for check in comparison.orderings)
    assert comparison.reproduces is True


def test_ordering_check_catches_a_broken_ordering() -> None:
    """Make budget+runtime the best real agent: two orderings must flip to False and both
    must be written up."""
    means = _perfect_means()
    means[row_key(WORST_ROW_FEATURES, 50)] = 0.95
    comparison = build_comparison(_manifest_from(means), experiment_manifest="m.json")
    broken = {check.name for check in comparison.orderings if not check.holds}
    assert broken == {"budget_runtime_is_worst", "best_real_agent_is_budget_vote_average_vote_count"}
    assert any("budget_runtime_is_worst" in note for note in comparison.notes)


def test_ordering_check_catches_a_canary_that_is_not_top() -> None:
    """The §9.2 MUST: if budget+revenue is not ~100 and on top, the data pipeline is broken."""
    means = _perfect_means()
    means[row_key(SANITY_FEATURES, 50)] = 0.50
    comparison = build_comparison(_manifest_from(means), experiment_manifest="m.json")
    check = next(c for c in comparison.orderings if c.name == "sanity_agent_tops_the_table")
    assert check.holds is False


# ------------------------------------------------------- ticket test requirement 2: tracing


def test_every_cell_traces_to_config_seed_and_sha() -> None:
    """Ticket test requirement 2, stated directly: from any cell you can reach the config that
    produced it, the master seed, the roster bytes, and the code identity."""
    comparison = build_comparison(_manifest_from(_perfect_means()), experiment_manifest="run.json")

    assert comparison.config.seed == 20260803
    assert comparison.config.n_runs == REQUIRED_RUNS
    assert comparison.git_sha == "0123456789abcdef0123456789abcdef01234567"
    assert comparison.created_utc.startswith("2026-08-03")
    assert comparison.experiment_manifest == "run.json"
    assert len(comparison.crowd_config_sha256) == 64
    assert comparison.band_points == BAND_POINTS

    keys = {cell.metric_key for cell in comparison.cells}
    assert keys == {row_key(row.features, ep) for row in PUBLISHED_ROWS for ep in (5, 50)}


def test_crowd_config_sha_pins_the_actual_roster_bytes(tmp_path: Path) -> None:
    """A hand-edited roster must change the recorded hash, or the trace proves nothing."""
    import hashlib

    expected = hashlib.sha256(ROSTER_CONFIG.read_bytes()).hexdigest()
    comparison = build_comparison(_manifest_from(_perfect_means()), experiment_manifest="m.json")
    assert comparison.crowd_config_sha256 == expected


def test_comparison_json_roundtrips(tmp_path: Path) -> None:
    original = build_comparison(_manifest_from(_perfect_means()), experiment_manifest="m.json")
    path = write_comparison(original, tmp_path / "cmp.json")
    assert read_comparison(path) == original


def test_render_comparison_covers_every_row() -> None:
    comparison = build_comparison(_manifest_from(_perfect_means()), experiment_manifest="m.json")
    table = render_comparison(comparison)
    assert table.count("\n") == 22  # header + separator + 20 cells
    assert "budget+revenue *(sanity)*" in table


# -------------------------------------------- ticket test requirement 1: the reproduction


@pytest.mark.slow
def test_reproduction_hollywood_real_data(tmp_path: Path) -> None:
    """Ticket test requirement 1. All ten rows within ±3 points at 50 epochs; the three §9.2
    orderings preserved. Ten seeded runs from the shipped config — no seed selection here.

    Skipped with a named reason when the raw datasets are absent (they are gitignored and
    never committed; see `data/DATA_PROVENANCE.md`). Running this on synthetic data would
    produce a table that cannot fail, which is exactly what the ticket forbids: this test is
    the DETECTOR for upstream breakage, and a detector calibrated on invented data detects
    nothing.
    """
    try:
        load_hollywood_frame()
    except FileNotFoundError as absent:
        pytest.skip(f"Hollywood raw data not present locally: {absent}")

    config = ExperimentConfig.from_yaml(HOLLYWOOD_CONFIG)
    manifest_path = run_experiment(config, manifest_dir=tmp_path)
    comparison = build_comparison(read_manifest(manifest_path), experiment_manifest=manifest_path.name)

    out_of_band = [c for c in comparison.out_of_band if c.epochs == 50]
    assert not out_of_band, "rows outside ±3 points at 50 epochs:\n" + render_comparison(comparison)

    broken = [check for check in comparison.orderings if not check.holds]
    assert not broken, "broken §9.2 orderings: " + "; ".join(c.detail for c in broken)

    canary = next(c for c in comparison.cells if c.is_sanity and c.epochs == 50)
    assert canary.measured_mean_pct >= 97.0, (
        f"budget+revenue canary measured {canary.measured_mean_pct:.1f}% — spec §9.2: if it is "
        f"not ~100%, the data pipeline is broken (the bug is upstream, not in this ticket)"
    )
