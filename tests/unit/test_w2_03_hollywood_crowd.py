"""W2-03 real-data closure tests — the gap the thirty synthetic tests left open.

`test_w2_03_crowd.py` proves the assignment policy and crowd builder are correct against
frames it constructs itself. That is the right way to test a mechanism, but it cannot catch a
config naming a column the real ETL does not emit, because the synthetic frames are built to
match whatever the config says. Both shipped Hollywood configs named `popularity`; the W1-03
ETL emits `tmdb_popularity`. Every §9.2/§9.3 crowd would have raised
`KeyError: feature 'popularity' is not in this dataset` the first time anyone ran one.

`test_hollywood_configs_name_only_real_etl_columns` is the fast, data-free regression pin for
exactly that class of bug: it reads the shipped YAML and checks every feature against
`DEFAULT_FEATURE_COLUMNS`, the single source of truth for what W1-05 can supply. It needs no
dataset, so it runs in CI and stays green forever after.

The `@slow` tests build the crowds for real and require `data/raw/` to be populated.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from wocbots.agents.crowd import CrowdConfig
from wocbots.data.splits import DEFAULT_FEATURE_COLUMNS
from wocbots.experiments.crowd_build import HOLLYWOOD_CROWD_CONFIGS, build_hollywood_crowd
from wocbots.experiments.registry import resolve_kind

RAW_ROOT = Path("data/raw")

_requires_raw_data = pytest.mark.skipif(
    not (RAW_ROOT / "tmdb" / "movies.csv").exists(),
    reason="raw Hollywood data not present locally (expected in CI); see data/DATA_PROVENANCE.md",
)


def _roster_features(config: CrowdConfig) -> set[str]:
    """Every feature name a config can put in front of a classifier, both policy branches."""
    assignment = config.assignment
    names: set[str] = set(assignment.anchors)
    explicit_agents = getattr(assignment, "agents", None)
    if explicit_agents is not None:
        for agent in explicit_agents:
            names.update(agent)
    pool = getattr(assignment, "pool", None)
    if pool is not None:
        names.update(pool)
    return names


@pytest.mark.parametrize("config_path", HOLLYWOOD_CROWD_CONFIGS)
def test_hollywood_configs_name_only_real_etl_columns(config_path: str) -> None:
    """The regression pin for the `popularity` / `tmdb_popularity` defect.

    Fast and data-free: `DEFAULT_FEATURE_COLUMNS` is what W1-05's feature matrix can supply,
    so any crowd config naming something outside it cannot be built, full stop.
    """
    config = CrowdConfig.from_yaml(config_path)
    available = set(DEFAULT_FEATURE_COLUMNS)
    unknown = sorted(_roster_features(config) - available)
    assert not unknown, (
        f"{config_path} names features the W1-03 ETL does not emit: {unknown}. "
        f"Available columns: {sorted(available)}"
    )


def test_the_column_check_catches_a_planted_bad_name(tmp_path: Path) -> None:
    """The pin's self-test: a checker that cannot catch the bug it was written for is
    decoration (same reasoning as the W0-04 RNG guard's planted-violation fixture).

    Plants the ORIGINAL defect — `popularity` instead of `tmdb_popularity` — and requires the
    check to reject it.
    """
    planted = tmp_path / "planted.yaml"
    planted.write_text(
        "name: planted\n"
        "assignment:\n"
        "  policy: explicit\n"
        "  anchors: [budget]\n"
        "  agents:\n"
        "    - [budget, popularity]\n"
        "    - [budget, vote_count]\n"
        "classifier: {variant: mlp, epochs: 20, hidden_width: 32}\n"
        "confidence_weights: {w_acc: 0.3, w_prec: 0.5, w_rec: 0.2}\n",
        encoding="utf-8",
    )
    config = CrowdConfig.from_yaml(planted)
    unknown = sorted(_roster_features(config) - set(DEFAULT_FEATURE_COLUMNS))
    assert unknown == ["popularity"], "the column check would not have caught the real defect"


def test_both_named_hollywood_configs_are_covered() -> None:
    """Spec §9.2 (matched five) and §9.3 (the 26-agent mix) must both ship as named configs."""
    assert len(HOLLYWOOD_CROWD_CONFIGS) == 2
    for path in HOLLYWOOD_CROWD_CONFIGS:
        assert Path(path).exists(), f"named config missing: {path}"


def test_crowd_kind_is_registered() -> None:
    assert resolve_kind("w2_03_hollywood_crowd") is not None


def test_the_two_configs_exercise_both_policy_branches() -> None:
    """One explicit roster, one seeded deal — together they cover the whole §5.1 seam."""
    policies = {CrowdConfig.from_yaml(p).assignment.policy for p in HOLLYWOOD_CROWD_CONFIGS}
    assert policies == {"explicit", "seeded"}


@pytest.mark.slow
@_requires_raw_data
def test_five_agent_crowd_builds_on_real_data() -> None:
    """Spec §9.2 crowd-level: five agents, four 2-feature anchored on budget + one 5-feature."""
    crowd = build_hollywood_crowd("configs/crowd_hollywood_5agent.yaml", np.random.default_rng(20260810))
    manifest = crowd.manifest

    assert len(manifest.roster) == 5
    assert all("budget" in features for features in manifest.roster), "§5.1: budget anchors every agent"
    sizes = sorted(len(features) for features in manifest.roster)
    assert sizes == [2, 2, 2, 2, 5], f"§9.2 matched roster shape wrong: {sizes}"
    assert crowd.sanity_free, "§10.9: no revenue-seeing agent may reach a crowd"
    assert len(manifest.agents) + len(manifest.pruned) == 5, "manifest must reconcile"


@pytest.mark.slow
@_requires_raw_data
def test_twenty_six_agent_crowd_builds_on_real_data() -> None:
    """Spec §9.3: one 5-feature, five 4-feature, ten 3-feature, ten 2-feature."""
    crowd = build_hollywood_crowd("configs/crowd_hollywood_26agent.yaml", np.random.default_rng(20260810))
    manifest = crowd.manifest

    assert len(manifest.roster) == 26
    assert all("budget" in features for features in manifest.roster)
    histogram: dict[int, int] = {}
    for features in manifest.roster:
        histogram[len(features)] = histogram.get(len(features), 0) + 1
    assert histogram == {5: 1, 4: 5, 3: 10, 2: 10}, f"§9.3 composition wrong: {histogram}"
    assert crowd.sanity_free
    assert len(manifest.agents) + len(manifest.pruned) == 26


@pytest.mark.slow
@_requires_raw_data
def test_real_crowd_build_is_deterministic_under_seed() -> None:
    """Same master seed ⇒ byte-identical crowd manifest, on real data (ticket test req 1)."""
    first = build_hollywood_crowd("configs/crowd_hollywood_26agent.yaml", np.random.default_rng(7))
    second = build_hollywood_crowd("configs/crowd_hollywood_26agent.yaml", np.random.default_rng(7))
    assert first.manifest.model_dump(mode="json") == second.manifest.model_dump(mode="json")
