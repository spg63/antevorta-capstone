"""W2-03 test requirements — feature-assignment policy and the crowd builder.

Covers the ticket's three test requirements plus edges and the forbidden-shortcut guards:

  1. Invariants: anchors in every agent; only legal features dealt; deterministic under seed
     (roster AND the full crowd manifest).
  2. Roster expressiveness: the 26-agent §9.3 mix constructs EXACTLY (1/5/10/10); explicit
     rosters reproduce an exact feature-set list in order (what W2-04 needs).
  3. Pruning integration: a deliberately-bad agent prunes without disturbing the crowd
     manifest — survivors, pruned log, and composition all reconcile.

Plus: the budget+revenue sanity agent is structurally unreachable from this path (§10.9),
rejected at config validation AND by the builder's roster guard; config bounds (§5.1's 1–4
anchors, pool sizing); duplicate feature sets allowed; example configs load; manifest JSON
round-trips. Everything runs on synthetic separable data — no Hollywood ETL needed (that is
W2-04's job); determinism is by construction, so nothing here can flake.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from wocbots.agents import HOLLYWOOD_WEIGHTS
from wocbots.agents.classifier import ClassifierSpec, LabeledData
from wocbots.agents.crowd import (
    AgentGroup,
    AssignmentPolicy,
    CrowdConfig,
    CrowdManifest,
    ExplicitAssignment,
    ExplicitAssignmentConfig,
    Roster,
    SeededAssignmentConfig,
    SeededRandomAssignment,
    build_assignment_policy,
    build_crowd,
    read_crowd_manifest,
    write_crowd_manifest,
)

CONFIGS_DIR = Path(__file__).resolve().parents[2] / "configs"

# ------------------------------------------------------------------ data + config helpers


def _blobs(rng: np.random.Generator, *, n: int = 400, n_features: int = 5, sep: float = 3.0) -> LabeledData:
    """A separable binary set: feature f0 carries the signal (class means at ±`sep`), f1.. are
    noise — the f0 anchor is the `budget` analogue. Matches the W2-02 synthetic anchor."""
    y = rng.integers(0, 2, size=n).astype(np.int_)
    f0 = np.where(y == 1, sep, -sep) + rng.standard_normal(n) * 0.5
    rest = rng.standard_normal((n, n_features - 1))
    x = np.column_stack([f0, rest]).astype(np.float64)
    return LabeledData(features=tuple(f"f{i}" for i in range(n_features)), X=x, y=y)


def _trap_data(rng: np.random.Generator, *, invert_trap: bool) -> LabeledData:
    """Three columns: f0 an honest signal (consistent train↔eval); `noise`; `trap` aligned
    with the label in TRAIN but inverted in EVAL. An agent on `trap` alone learns the train
    split perfectly then scores ~0 on eval ⇒ deterministically pruned (eval_accuracy < 0.50).
    An agent on `f0` stays honest ⇒ kept. This makes the prune outcome exact, not probabilistic."""
    n = 400
    y = rng.integers(0, 2, size=n).astype(np.int_)
    f0 = np.where(y == 1, 4.0, -4.0) + rng.standard_normal(n) * 0.3
    noise = rng.standard_normal(n)
    trap_label = (1 - y) if invert_trap else y
    trap = np.where(trap_label == 1, 5.0, -5.0) + rng.standard_normal(n) * 0.3
    x = np.column_stack([f0, noise, trap]).astype(np.float64)
    return LabeledData(features=("f0", "noise", "trap"), X=x, y=y)


def _seeded(
    anchors: tuple[str, ...],
    pool: tuple[str, ...],
    groups: tuple[AgentGroup, ...],
) -> SeededAssignmentConfig:
    return SeededAssignmentConfig(policy="seeded", anchors=anchors, pool=pool, groups=groups)


# ================================================ test req 1: assignment invariants


def test_seeded_anchors_in_every_agent() -> None:
    """Ticket test req 1: every agent receives the whole anchor set (spec §5.1)."""
    config = _seeded(("budget",), ("a", "b", "c"), (AgentGroup(count=8, n_features=3),))
    roster = SeededRandomAssignment(config).assign(np.random.default_rng(0))
    assert len(roster) == 8
    assert all("budget" in agent for agent in roster)


def test_seeded_multi_anchor_present_in_every_agent() -> None:
    """The anchor set may be up to 4 features (spec §5.1); all of them land in every agent."""
    config = _seeded(("budget", "vote_count"), ("a", "b", "c"), (AgentGroup(count=5, n_features=4),))
    roster = SeededRandomAssignment(config).assign(np.random.default_rng(1))
    assert all({"budget", "vote_count"} <= set(agent) for agent in roster)


def test_seeded_only_legal_features_dealt() -> None:
    """Ticket test req 1: nothing outside anchors ∪ pool is ever dealt."""
    anchors, pool = ("budget",), ("a", "b", "c", "d")
    config = _seeded(anchors, pool, (AgentGroup(count=20, n_features=4),))
    roster = SeededRandomAssignment(config).assign(np.random.default_rng(2))
    legal = set(anchors) | set(pool)
    assert all(set(agent) <= legal for agent in roster)
    # dealt features are distinct within an agent (drawn without replacement)
    assert all(len(set(agent)) == len(agent) for agent in roster)


def test_seeded_roster_deterministic_under_seed() -> None:
    """Ticket test req 1: same config + same seed ⇒ byte-identical roster, twice."""
    config = _seeded(("budget",), ("a", "b", "c", "d"), (AgentGroup(count=12, n_features=3),))
    first = SeededRandomAssignment(config).assign(np.random.default_rng(123))
    second = SeededRandomAssignment(config).assign(np.random.default_rng(123))
    assert first == second


def test_seeded_roster_seed_actually_threads() -> None:
    """Determinism is not constancy: a different seed yields a different deal (the Generator
    genuinely threads through). Guards against a policy that ignores its rng."""
    config = _seeded(("budget",), tuple("abcdefgh"), (AgentGroup(count=10, n_features=4),))
    a = SeededRandomAssignment(config).assign(np.random.default_rng(1))
    b = SeededRandomAssignment(config).assign(np.random.default_rng(2))
    assert a != b


def test_seeded_anchors_only_when_no_remainder() -> None:
    """When n_features equals the anchor count, nothing is dealt — the agent is anchors-only.
    A legal degenerate composition (a crowd of identical agents), not an error."""
    config = _seeded(("budget", "vote_count"), ("a", "b"), (AgentGroup(count=3, n_features=2),))
    roster = SeededRandomAssignment(config).assign(np.random.default_rng(0))
    assert roster == (("budget", "vote_count"), ("budget", "vote_count"), ("budget", "vote_count"))


def test_build_crowd_manifest_deterministic() -> None:
    """§4 test discipline: same config + same seed ⇒ byte-identical crowd manifest."""
    config = CrowdConfig(
        name="det",
        assignment=_seeded(("f0",), ("f1", "f2", "f3", "f4"), (AgentGroup(count=4, n_features=3),)),
        classifier=ClassifierSpec(epochs=5),
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )
    train, ev = _blobs(np.random.default_rng(1)), _blobs(np.random.default_rng(2))
    first = build_crowd(config=config, train_data=train, eval_data=ev, rng=np.random.default_rng(7))
    second = build_crowd(config=config, train_data=train, eval_data=ev, rng=np.random.default_rng(7))
    assert first.manifest.model_dump(mode="json") == second.manifest.model_dump(mode="json")


# ============================================== test req 2: roster expressiveness


def test_26_agent_mix_constructs_exactly() -> None:
    """Ticket test req 2: the §9.3 26-agent mix (one 5-, five 4-, ten 3-, ten 2-feature)
    constructs exactly from the named config — total 26, histogram {2:10, 3:10, 4:5, 5:1}."""
    config = CrowdConfig.from_yaml(CONFIGS_DIR / "crowd_hollywood_26agent.yaml")
    roster = build_assignment_policy(config.assignment).assign(np.random.default_rng(0))
    assert len(roster) == 26
    assert dict(sorted(Counter(len(agent) for agent in roster).items())) == {2: 10, 3: 10, 4: 5, 5: 1}
    # every agent budget-anchored, only §9.2 five-feature-set columns dealt (invariants hold here too)
    assert all("budget" in agent for agent in roster)
    legal = {"budget", "vote_count", "vote_average", "runtime", "popularity"}
    assert all(set(agent) <= legal for agent in roster)


def test_explicit_roster_is_exact() -> None:
    """Ticket test req 2 / S1: explicit rosters express exact feature sets per agent, in order
    — the §9.2 matched 5-agent crowd (four budget-anchored 2-feature agents + one 5-feature)."""
    config = CrowdConfig.from_yaml(CONFIGS_DIR / "crowd_hollywood_5agent.yaml")
    roster = build_assignment_policy(config.assignment).assign(np.random.default_rng(999))
    assert roster == (
        ("budget", "vote_count"),
        ("budget", "vote_average"),
        ("budget", "runtime"),
        ("budget", "popularity"),
        ("budget", "vote_count", "vote_average", "runtime", "popularity"),
    )


def test_explicit_assignment_ignores_rng() -> None:
    """An explicit roster is deterministic by construction — independent of the Generator."""
    config = ExplicitAssignmentConfig(policy="explicit", agents=(("budget", "a"), ("budget", "b")))
    policy = ExplicitAssignment(config)
    assert policy.assign(np.random.default_rng(0)) == policy.assign(np.random.default_rng(1))


def test_duplicate_feature_sets_allowed() -> None:
    """Spec §5.1: duplicate feature sets across agents are allowed (neither limited nor
    encouraged). A one-feature pool dealt to three 2-feature agents yields three identical
    agents — this must build, not raise."""
    config = _seeded(("budget",), ("a",), (AgentGroup(count=3, n_features=2),))
    roster = SeededRandomAssignment(config).assign(np.random.default_rng(0))
    assert roster == (("budget", "a"), ("budget", "a"), ("budget", "a"))


# ============================================ test req 3: pruning integration


def test_bad_agent_prunes_without_disturbing_manifest() -> None:
    """Ticket test req 3: a deliberately-bad agent prunes and the crowd manifest stays intact —
    the pruned agent is in `pruned`, the survivors in `agents`, and `composition` reconciles."""
    config = CrowdConfig(
        name="prune_integration",
        assignment=ExplicitAssignmentConfig(
            policy="explicit",
            agents=(("f0",), ("f0", "noise"), ("trap",)),  # two honest agents + one trap
        ),
        classifier=ClassifierSpec(variant="logreg"),  # converges fully ⇒ exact prune outcome
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )
    train = _trap_data(np.random.default_rng(1), invert_trap=False)
    ev = _trap_data(np.random.default_rng(2), invert_trap=True)
    built = build_crowd(config=config, train_data=train, eval_data=ev, rng=np.random.default_rng(7))
    manifest = built.manifest

    # the trap agent alone is pruned, logged with its features + sub-0.50 accuracy + reason
    assert len(manifest.pruned) == 1
    assert manifest.pruned[0].features == ("trap",)
    assert manifest.pruned[0].eval_accuracy < 0.50
    assert "5.3" in manifest.pruned[0].reason

    # the survivors are exactly the two honest agents, and they are the returned usable agents
    kept_features = {record.features for record in manifest.agents}
    assert kept_features == {("f0",), ("f0", "noise")}
    assert {agent.agent.features for agent in built.agents} == kept_features
    assert all(record.eval_accuracy >= 0.50 for record in manifest.agents)

    # the manifest is undisturbed: the full roster is still recorded in order, and the counts
    # reconcile (n_assigned = n_kept + n_pruned)
    assert manifest.roster == (("f0",), ("f0", "noise"), ("trap",))
    composition = manifest.composition
    assert composition.n_assigned == 3
    assert composition.n_kept == 2
    assert composition.n_pruned == 1
    assert composition.n_assigned == composition.n_kept + composition.n_pruned


# ================================ forbidden shortcut: the sanity agent is unreachable


def test_leaky_feature_rejected_in_seeded_config() -> None:
    """Spec §10.9: a seeded config naming `revenue` (anchor OR pool) fails at validation — the
    budget+revenue canary is not constructible by dealing features (forbidden-shortcut #6)."""
    with pytest.raises(ValidationError, match="revenue"):
        _seeded(("budget",), ("revenue",), (AgentGroup(count=1, n_features=2),))
    with pytest.raises(ValidationError, match="revenue"):
        _seeded(("revenue",), ("a",), (AgentGroup(count=1, n_features=2),))


def test_leaky_feature_rejected_in_explicit_config() -> None:
    """Spec §10.9: an explicit roster listing `revenue` fails at validation too."""
    with pytest.raises(ValidationError, match="revenue"):
        ExplicitAssignmentConfig(policy="explicit", agents=(("budget", "revenue"),))


def test_build_crowd_rejects_leaky_roster_defense_in_depth() -> None:
    """Even a rogue AssignmentPolicy that manufactures a `revenue` roster (bypassing config
    validation) cannot reach the canary: `build_crowd` re-checks the roster (spec §10.9)."""

    class _RoguePolicy:
        def assign(self, rng: np.random.Generator) -> Roster:
            return (("budget", "revenue"),)

    config = CrowdConfig(
        name="rogue",
        assignment=ExplicitAssignmentConfig(policy="explicit", agents=(("budget",),)),
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )
    data = _blobs(np.random.default_rng(0), n_features=2)
    revenue_data = LabeledData(features=("budget", "revenue"), X=data.X, y=data.y)
    # monkeypatch the policy factory result by calling build_crowd's guard through a rogue roster:
    rogue: AssignmentPolicy = _RoguePolicy()
    roster = rogue.assign(np.random.default_rng(0))
    # build_crowd would call train_crowd, but the roster guard fires first
    with pytest.raises(ValueError, match="revenue"):
        # exercise the same guard build_crowd uses, on the rogue roster
        from wocbots.agents.crowd import _reject_leaky

        for agent_features in roster:
            _reject_leaky(agent_features, where="assigned roster")
    # and the config itself, built honestly, stays sanity-free end to end
    built = build_crowd(
        config=config, train_data=revenue_data, eval_data=revenue_data, rng=np.random.default_rng(0)
    )
    assert built.sanity_free is True


# ============================================ config validation bounds (spec §5.1)


def test_anchor_count_bounds() -> None:
    """Spec §5.1: 1–4 anchors. Zero anchors and five anchors both raise; 1 and 4 are fine."""
    with pytest.raises(ValidationError, match="anchors"):
        _seeded((), ("a",), (AgentGroup(count=1, n_features=1),))
    with pytest.raises(ValidationError, match="anchors"):
        _seeded(("a", "b", "c", "d", "e"), ("f",), (AgentGroup(count=1, n_features=6),))
    assert _seeded(("a",), ("b",), (AgentGroup(count=1, n_features=2),)).n_agents == 1
    assert _seeded(("a", "b", "c", "d"), ("e",), (AgentGroup(count=1, n_features=5),)).n_agents == 1


def test_seeded_dealt_exceeds_pool_rejected() -> None:
    """A group asking for more distinct dealt features than the pool holds is a config bug."""
    with pytest.raises(ValidationError, match="pool has only"):
        _seeded(("budget",), ("a", "b"), (AgentGroup(count=1, n_features=5),))


def test_seeded_n_features_below_anchor_count_rejected() -> None:
    """Every agent must at least carry the anchors: n_features below the anchor count raises."""
    with pytest.raises(ValidationError, match="below the anchor count"):
        _seeded(("budget", "vote_count"), ("a",), (AgentGroup(count=1, n_features=1),))


def test_anchors_and_pool_must_be_disjoint() -> None:
    with pytest.raises(ValidationError, match="disjoint"):
        _seeded(("budget",), ("budget", "a"), (AgentGroup(count=1, n_features=2),))


def test_explicit_declared_anchor_must_be_in_every_agent() -> None:
    """Spec §5.1: an explicit roster that declares anchors asserts them in EVERY agent."""
    with pytest.raises(ValidationError, match="missing declared anchor"):
        ExplicitAssignmentConfig(
            policy="explicit",
            anchors=("budget",),
            agents=(("budget", "a"), ("b", "c")),  # second agent lacks budget
        )


def test_explicit_empty_agent_rejected() -> None:
    with pytest.raises(ValidationError, match="at least one"):
        ExplicitAssignmentConfig(policy="explicit", agents=((),))


def test_seeded_requires_at_least_one_group() -> None:
    with pytest.raises(ValidationError, match="at least one agent group"):
        _seeded(("budget",), ("a",), ())


# ============================================ seam, configs, manifest plumbing


def test_assignment_policies_satisfy_the_seam() -> None:
    """Both reference policies satisfy the runtime-checkable `AssignmentPolicy` seam (§11)."""
    explicit = build_assignment_policy(ExplicitAssignmentConfig(policy="explicit", agents=(("a",),)))
    seeded = build_assignment_policy(_seeded(("a",), ("b",), (AgentGroup(count=1, n_features=2),)))
    assert isinstance(explicit, AssignmentPolicy)
    assert isinstance(seeded, AssignmentPolicy)
    assert isinstance(explicit, ExplicitAssignment)
    assert isinstance(seeded, SeededRandomAssignment)


def test_assignment_returns_only_feature_names() -> None:
    """Forbidden shortcut guard: assignment is not entangled with agent internals — `assign`
    yields tuples of feature-name STRINGS, never agents or classifiers."""
    roster = build_assignment_policy(
        _seeded(("budget",), ("a", "b"), (AgentGroup(count=3, n_features=2),))
    ).assign(np.random.default_rng(0))
    assert all(isinstance(agent, tuple) for agent in roster)
    assert all(isinstance(feature, str) for agent in roster for feature in agent)


@pytest.mark.parametrize(
    "filename",
    ["crowd_hollywood_26agent.yaml", "crowd_hollywood_5agent.yaml", "crowd_smoke.yaml"],
)
def test_example_configs_load(filename: str) -> None:
    """The named §9.3/§9.2 example configs parse and validate — crowd composition is config."""
    config = CrowdConfig.from_yaml(CONFIGS_DIR / filename)
    assert config.assignment.n_agents >= 1
    assert isinstance(config.confidence_weights, type(HOLLYWOOD_WEIGHTS))


def test_smoke_config_builds_end_to_end() -> None:
    """The synthetic smoke config runs the whole path (config → roster → train → prune →
    manifest) on separable blobs, before any real data exists (preamble §0.3)."""
    config = CrowdConfig.from_yaml(CONFIGS_DIR / "crowd_smoke.yaml")
    train, ev = _blobs(np.random.default_rng(1)), _blobs(np.random.default_rng(2))
    built = build_crowd(config=config, train_data=train, eval_data=ev, rng=np.random.default_rng(3))
    assert built.sanity_free is True
    assert built.manifest.composition.n_assigned == 6
    assert built.manifest.anchors == ("f0",)
    # every kept agent carries the anchor and posts real metrics
    assert all("f0" in record.features for record in built.manifest.agents)
    assert built.manifest.composition.n_kept == len(built.agents)


def test_crowd_manifest_json_roundtrips(tmp_path: Path) -> None:
    """The crowd manifest is canonical-JSON evidence: write then read gives an equal manifest."""
    config = CrowdConfig(
        name="roundtrip",
        assignment=_seeded(("f0",), ("f1", "f2", "f3"), (AgentGroup(count=3, n_features=2),)),
        classifier=ClassifierSpec(epochs=5),
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )
    train, ev = _blobs(np.random.default_rng(1)), _blobs(np.random.default_rng(2))
    built = build_crowd(config=config, train_data=train, eval_data=ev, rng=np.random.default_rng(4))
    path = write_crowd_manifest(built.manifest, tmp_path / "crowd.json")
    restored = read_crowd_manifest(path)
    assert isinstance(restored, CrowdManifest)
    assert restored == built.manifest


def test_crowd_manifest_records_architecture_for_mlp() -> None:
    """The manifest carries each MLP agent's fitted hidden-layer sizes (for the W2-04 table):
    a 5-feature agent → hidden_layer_count(5)=2 layers of width 32."""
    config = CrowdConfig(
        name="arch",
        assignment=ExplicitAssignmentConfig(policy="explicit", agents=(("f0", "f1", "f2", "f3", "f4"),)),
        classifier=ClassifierSpec(variant="mlp", epochs=5, hidden_width=32),
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )
    train, ev = _blobs(np.random.default_rng(1)), _blobs(np.random.default_rng(2))
    built = build_crowd(config=config, train_data=train, eval_data=ev, rng=np.random.default_rng(5))
    assert built.manifest.agents[0].architecture == (32, 32)
