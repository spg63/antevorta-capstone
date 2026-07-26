"""W2-03 §5.1 / §9.3 — the feature-assignment policy and the crowd builder.

Crowd diversity is the load-bearing wisdom-of-crowds precondition, and it comes entirely
from *how features are dealt out* (spec §5.1). This module makes crowd composition **pure
configuration**: a seeded assignment policy behind a seam, plus explicit rosters, so the
§9.2 reproduction (W2-04) and every experiment after it is a config file, not code.

Two things live here, deliberately separated (the ticket's forbidden shortcut is "assignment
entangled with agent internals"):

1. **Assignment** — turning a config into a *roster*: a tuple of feature-name tuples, one
   per agent. This knows NOTHING about classifiers, training, or agent state; it only deals
   feature names. Two reference policies sit behind the `AssignmentPolicy` seam (spec §11):

   - `SeededRandomAssignment` (spec §5.1): every agent receives the shared anchor set;
     the remaining features are dealt randomly from a pool; duplicate feature sets across
     agents are neither limited nor encouraged. Deterministic under the harness Generator.
   - `ExplicitAssignment`: exact feature sets per agent, verbatim from config — what W2-04
     needs to reproduce the §9.2 ten-row agent table precisely.

2. **The crowd builder** — `build_crowd`: config -> roster -> N trained / evaluated /
   initialized / pruned agents (the W2-02 machinery, untouched) -> a `CrowdManifest`
   recording per-agent features, eval metrics, and the pruned list.

The budget+revenue **sanity agent is structurally unreachable from this path** (spec §10.9,
forbidden-shortcut #6): every crowd config rejects the leaky feature set at *validation*
time (so a config naming `revenue` cannot even load), and `build_crowd` re-checks the roster
before training. The canary has its own constructor (`build_sanity_agent`, W2-02); it is
never reached by dealing features.

This module calls NO RNG of its own (`numpy.random.*` is barred outside the harness — the
W0-04 guard): the seeded policy only *advances* the `Generator` handed to it, via
`rng.choice`, a method on that Generator.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal, Protocol, runtime_checkable

import numpy as np
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from wocbots.agents.agent import ConfidenceWeights
from wocbots.agents.classifier import ClassifierSpec, LabeledData, MLPAgentClassifier
from wocbots.agents.training import LEAKY_FEATURES, PruneResult, TrainedAgent, train_crowd

# Spec §5.1: "1–4 highly correlated features shared with all agents." The anchor set is the
# crowd's shared knowledge base; its size is bounded here so a mis-sized config fails loudly.
_MIN_ANCHORS = 1
_MAX_ANCHORS = 4

# A roster is a tuple of per-agent feature tuples — the ONLY thing assignment produces. No
# agents, no classifiers: assignment is not entangled with agent internals (ticket forbidden
# shortcut). Feature order within an agent is anchors-first, then dealt/explicit remainder.
Roster = tuple[tuple[str, ...], ...]


def _reject_leaky(features: Sequence[str], *, where: str) -> None:
    """Raise if any feature is in `LEAKY_FEATURES` (spec §10.9).

    `revenue` essentially encodes the label; an agent that sees it is the sanity canary,
    which MUST NOT be constructible by dealing features (forbidden-shortcut #6). The guard
    is tied to the single source of truth in `training.LEAKY_FEATURES`, so widening the
    barred set is a one-line change there, honoured everywhere.
    """
    leaked = sorted(LEAKY_FEATURES.intersection(features))
    if leaked:
        raise ValueError(
            f"{where}: features {leaked} leak the label and are barred from crowd "
            f"construction (spec §10.9); the budget+revenue sanity agent is reachable only "
            f"via build_sanity_agent, never by dealing features"
        )


# --------------------------------------------------------------------- config models


class AgentGroup(BaseModel):
    """A block of `count` agents, each dealt `n_features` features total (anchors included).

    The §9.3 compositions are expressed as a sequence of these: the 26-agent mix is
    `[(1, 5), (5, 4), (10, 3), (10, 2)]` — one 5-feature agent, five 4-feature, ten
    3-feature, ten 2-feature. `n_features` is the WHOLE agent's feature count (anchors +
    dealt remainder), so it reads exactly like the spec's "agents at N features".
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    count: Annotated[int, Field(ge=1)]
    n_features: Annotated[int, Field(ge=1)]


class SeededAssignmentConfig(BaseModel):
    """The spec §5.1 policy as config: anchors shared by all, remainder dealt randomly.

    Frozen + ``extra="forbid"`` (the O3 ruling): a typo'd key is a `ValidationError`, not a
    silent default. Validation encodes the spec: 1–4 anchors (§5.1), anchors disjoint from
    the pool, every group's dealt remainder (`n_features - len(anchors)`) fits in the pool,
    and NO leaky feature anywhere (§10.9).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy: Literal["seeded"]
    anchors: tuple[str, ...]
    """The shared anchor set every agent receives (spec §5.1); in practice `budget`."""
    pool: tuple[str, ...] = ()
    """Non-anchor features dealt randomly across agents. Empty ⇒ every agent is anchors-only."""
    groups: tuple[AgentGroup, ...]
    """The crowd composition: blocks of (count, n_features). Their sum is the agent count."""

    @model_validator(mode="after")
    def _validate(self) -> SeededAssignmentConfig:
        if not (_MIN_ANCHORS <= len(self.anchors) <= _MAX_ANCHORS):
            raise ValueError(
                f"anchors must be {_MIN_ANCHORS}–{_MAX_ANCHORS} features (spec §5.1), "
                f"got {len(self.anchors)}: {list(self.anchors)}"
            )
        if len(set(self.anchors)) != len(self.anchors):
            raise ValueError(f"duplicate anchor features: {list(self.anchors)}")
        if len(set(self.pool)) != len(self.pool):
            raise ValueError(f"duplicate pool features: {list(self.pool)}")
        overlap = sorted(set(self.anchors).intersection(self.pool))
        if overlap:
            raise ValueError(f"features {overlap} appear in BOTH anchors and pool; keep them disjoint")
        if not self.groups:
            raise ValueError("a crowd needs at least one agent group")
        _reject_leaky(self.anchors, where="seeded anchors")
        _reject_leaky(self.pool, where="seeded pool")
        for group in self.groups:
            if group.n_features < len(self.anchors):
                raise ValueError(
                    f"group n_features={group.n_features} is below the anchor count "
                    f"{len(self.anchors)}: every agent must at least carry the anchors (spec §5.1)"
                )
            dealt = group.n_features - len(self.anchors)
            if dealt > len(self.pool):
                raise ValueError(
                    f"group n_features={group.n_features} needs {dealt} pool features but the "
                    f"pool has only {len(self.pool)}; cannot deal distinct features to one agent"
                )
        return self

    @property
    def n_agents(self) -> int:
        return sum(group.count for group in self.groups)


class ExplicitAssignmentConfig(BaseModel):
    """Exact feature sets per agent, verbatim — the roster W2-04 pins for the §9.2 table.

    ``anchors`` is optional documentation-and-invariant: if given, EVERY listed agent must
    contain all of them (validated), which is how an explicit Hollywood roster still asserts
    the "budget in every agent" property (§5.1) without dealing. No leaky feature anywhere.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy: Literal["explicit"]
    agents: tuple[tuple[str, ...], ...]
    """Each inner tuple is one agent's exact feature set, in the order given."""
    anchors: tuple[str, ...] = ()
    """Optional: if set, every agent MUST contain these (the §5.1 shared-anchor invariant)."""

    @model_validator(mode="after")
    def _validate(self) -> ExplicitAssignmentConfig:
        if not self.agents:
            raise ValueError("an explicit roster needs at least one agent")
        for i, agent in enumerate(self.agents):
            if not agent:
                raise ValueError(f"agent {i} has no features; an agent needs at least one (spec §5.2)")
            if len(set(agent)) != len(agent):
                raise ValueError(f"agent {i} has duplicate features: {list(agent)}")
            _reject_leaky(agent, where=f"explicit agent {i}")
            missing = [a for a in self.anchors if a not in agent]
            if missing:
                raise ValueError(
                    f"agent {i} {list(agent)} is missing declared anchor(s) {missing}: an "
                    f"explicit roster with anchors must carry them in every agent (spec §5.1)"
                )
        return self

    @property
    def n_agents(self) -> int:
        return len(self.agents)


# Discriminated on `policy`: pydantic picks the variant from the tag, so a YAML block with
# `policy: seeded` is validated against exactly SeededAssignmentConfig and vice versa.
AssignmentConfig = Annotated[
    SeededAssignmentConfig | ExplicitAssignmentConfig,
    Field(discriminator="policy"),
]


class CrowdConfig(BaseModel):
    """One crowd, fully as config: assignment + the per-agent classifier + confidence weights.

    This is the whole of "crowd composition is config" (the acceptance criterion). The
    §9.3 compositions ship as named YAML files loaded through `from_yaml`. `confidence_weights`
    is required and per-problem (spec §5.4) — never defaulted to a dataset's bias.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = "crowd"
    assignment: AssignmentConfig
    classifier: ClassifierSpec = ClassifierSpec()
    confidence_weights: ConfidenceWeights

    @classmethod
    def from_yaml(cls, path: Path | str) -> CrowdConfig:
        """Load + validate a crowd config from YAML via `yaml.safe_load`.

        Any unknown key raises `pydantic.ValidationError` naming it; a `revenue` anywhere in
        the assignment raises at load time (§10.9). A config that loads is a config that is
        safe to build.
        """
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if raw is None:
            raw = {}
        return cls.model_validate(raw)


# ------------------------------------------------------------------- the assignment seam


@runtime_checkable
class AssignmentPolicy(Protocol):
    """The feature-assignment seam (spec §11: policies are seams).

    `assign` returns a roster — a tuple of per-agent feature-name tuples — from the harness
    `Generator`. It is the ONE stochastic entry point of assignment (the explicit policy
    ignores the Generator; the seeded policy advances it). Crucially it returns FEATURE
    NAMES, never agents or classifiers: assignment stays decoupled from agent internals.
    """

    def assign(self, rng: np.random.Generator) -> Roster: ...


class ExplicitAssignment:
    """Return the config's exact roster, verbatim (order preserved). Ignores the Generator —
    an explicit roster is deterministic by construction, which is what W2-04 needs to pin the
    §9.2 table exactly."""

    def __init__(self, config: ExplicitAssignmentConfig) -> None:
        self._roster: Roster = tuple(tuple(agent) for agent in config.agents)

    def assign(self, rng: np.random.Generator) -> Roster:
        return self._roster


class SeededRandomAssignment:
    """Spec §5.1: every agent gets the anchor set; the remainder is dealt randomly from the
    pool WITHOUT replacement within an agent (so an agent never gets a feature twice), but
    INDEPENDENTLY across agents (so duplicate feature sets are allowed — neither limited nor
    encouraged). Deterministic under the Generator: same seed ⇒ byte-identical roster.

    Groups are dealt in order, agents within a group in order, so the draw sequence — and
    therefore the roster — is fixed by the seed. The Generator is only *advanced* (via
    `rng.choice`, a method call), never reseeded, so it threads on to classifier seeding
    exactly as the single-RNG rule requires (preamble §2)."""

    def __init__(self, config: SeededAssignmentConfig) -> None:
        self._anchors: tuple[str, ...] = tuple(config.anchors)
        self._pool: tuple[str, ...] = tuple(config.pool)
        self._groups = config.groups

    def assign(self, rng: np.random.Generator) -> Roster:
        roster: list[tuple[str, ...]] = []
        n_pool = len(self._pool)
        for group in self._groups:
            n_dealt = group.n_features - len(self._anchors)
            for _ in range(group.count):
                if n_dealt == 0:
                    dealt: tuple[str, ...] = ()
                else:
                    # Draw distinct pool INDICES (typed int) rather than strings, so the seam
                    # stays cleanly typed and never depends on numpy's string dtype behaviour.
                    indices = rng.choice(n_pool, size=n_dealt, replace=False)
                    dealt = tuple(self._pool[int(i)] for i in indices)
                roster.append(self._anchors + dealt)
        return tuple(roster)


def build_assignment_policy(config: AssignmentConfig) -> AssignmentPolicy:
    """Factory: the reference policy for `config`. The discriminated union makes any other
    shape unconstructible, so the trailing raise is defensive, not reachable."""
    if isinstance(config, ExplicitAssignmentConfig):
        return ExplicitAssignment(config)
    if isinstance(config, SeededAssignmentConfig):
        return SeededRandomAssignment(config)
    raise ValueError(f"unknown assignment policy config: {type(config).__name__}")  # pragma: no cover


# ------------------------------------------------------------------------ crowd manifest


class AgentRecord(BaseModel):
    """One kept agent in the crowd manifest: its dealt features, eval metrics, and the §2
    state those metrics initialized. This is a REPORTING record (not the §6.5 arena-facing
    public profile), so it may carry the eval metrics and fitted architecture."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    features: tuple[str, ...]
    eval_accuracy: float
    eval_precision: float
    eval_recall: float
    certainty: float
    trust_score: float
    confidence: float
    architecture: tuple[int, ...] | None = None
    """Fitted MLP hidden-layer sizes (None for non-MLP internals) — for the W2-04 table."""


class PrunedAgentRecord(BaseModel):
    """One pruned agent, carried through from `training.PrunedRecord` (spec §5.3)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    features: tuple[str, ...]
    eval_accuracy: float
    reason: str


class CrowdComposition(BaseModel):
    """The roster's shape at a glance: counts and a feature-size histogram over the WHOLE
    assigned roster (before pruning). The §9.3 26-agent mix has histogram {2: 10, 3: 10,
    4: 5, 5: 1}; test req 2 pins exactly this."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    n_assigned: int
    n_kept: int
    n_pruned: int
    size_histogram: dict[int, int]


class CrowdManifest(BaseModel):
    """The complete record of one crowd build: the full assigned roster, the kept agents with
    their metrics, the pruned list, and the composition summary (ticket S2). Serialises to
    canonical JSON — the crowd's evidence, re-readable and diffable.

    A deliberately-bad agent being pruned must NOT disturb this record: the pruned agent
    appears in `pruned`, the survivors in `agents`, and `composition` reconciles the counts
    (test req 3). Frozen + ``extra="forbid"`` for the strict-both-sides contract."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1
    name: str
    policy: Literal["seeded", "explicit"]
    anchors: tuple[str, ...]
    roster: Roster
    agents: tuple[AgentRecord, ...]
    pruned: tuple[PrunedAgentRecord, ...]
    composition: CrowdComposition


@dataclass(frozen=True)
class BuiltCrowd:
    """The crowd builder's deliverable: the KEPT trained agents (the ones later phases use)
    plus the `CrowdManifest`. Pruned agents are not returned as usable agents — their record
    lives in `manifest.pruned`. `sanity_free` is a standing True: nothing on this path can
    build the budget+revenue canary (spec §10.9)."""

    agents: tuple[TrainedAgent, ...]
    manifest: CrowdManifest

    @property
    def sanity_free(self) -> bool:
        return all(not agent.is_sanity for agent in self.agents)


def _size_histogram(roster: Roster) -> dict[int, int]:
    histogram: dict[int, int] = {}
    for agent in roster:
        histogram[len(agent)] = histogram.get(len(agent), 0) + 1
    return dict(sorted(histogram.items()))


def _agent_record(trained: TrainedAgent) -> AgentRecord:
    agent = trained.agent
    architecture = (
        trained.classifier.architecture if isinstance(trained.classifier, MLPAgentClassifier) else None
    )
    return AgentRecord(
        features=agent.features,
        eval_accuracy=agent.eval_accuracy,
        eval_precision=agent.eval_precision,
        eval_recall=agent.eval_recall,
        certainty=agent.certainty,
        trust_score=agent.trust_score,
        confidence=agent.confidence,
        architecture=architecture,
    )


def _build_manifest(config: CrowdConfig, roster: Roster, result: PruneResult) -> CrowdManifest:
    return CrowdManifest(
        name=config.name,
        policy=config.assignment.policy,
        anchors=tuple(config.assignment.anchors),
        roster=roster,
        agents=tuple(_agent_record(t) for t in result.kept),
        pruned=tuple(
            PrunedAgentRecord(features=p.features, eval_accuracy=p.eval_accuracy, reason=p.reason)
            for p in result.pruned
        ),
        composition=CrowdComposition(
            n_assigned=len(roster),
            n_kept=len(result.kept),
            n_pruned=len(result.pruned),
            size_histogram=_size_histogram(roster),
        ),
    )


def build_crowd(
    *,
    config: CrowdConfig,
    train_data: LabeledData,
    eval_data: LabeledData,
    rng: np.random.Generator,
) -> BuiltCrowd:
    """Config -> roster -> trained/evaluated/initialized/pruned agents + a crowd manifest (S2).

    The single `Generator` threads through: the seeded policy advances it to deal features,
    then the SAME Generator seeds each agent's classifier in `train_crowd` (order-fixed, so
    the whole crowd is reproducible from one master seed — preamble §2). `eval_data` MUST be
    a held-out slice of the TRAINING split (spec §10.5, enforced upstream by keeping it a
    separate argument).

    The roster is re-checked against the leak barrier before training: even though every
    crowd config rejects `revenue` at validation, `build_crowd` refuses a leaky roster too —
    defense in depth for "the sanity agent is not constructible through this path" (§10.9).
    """
    policy = build_assignment_policy(config.assignment)
    roster = policy.assign(rng)
    for agent_features in roster:
        _reject_leaky(agent_features, where="assigned roster")

    result = train_crowd(
        feature_sets=roster,
        train_data=train_data,
        eval_data=eval_data,
        spec=config.classifier,
        confidence_weights=config.confidence_weights,
        rng=rng,
    )
    manifest = _build_manifest(config, roster, result)
    return BuiltCrowd(agents=result.kept, manifest=manifest)


def write_crowd_manifest(manifest: CrowdManifest, path: Path | str) -> Path:
    """Write `manifest` as canonical JSON (`sort_keys=True`, UTF-8, trailing newline) — the
    same canonical form the experiment manifest uses, so crowd evidence diffs cleanly."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = manifest.model_dump(mode="json")
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def read_crowd_manifest(path: Path | str) -> CrowdManifest:
    """Read + validate a crowd manifest JSON file back into a `CrowdManifest`."""
    return CrowdManifest.model_validate_json(Path(path).read_text(encoding="utf-8"))
