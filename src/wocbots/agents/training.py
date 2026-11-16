"""W2-02 §5.3 / §9.2 / §10.9 — train → evaluate → initialize → prune, and the sanity agent.

This is the agent's lifecycle glue: train each agent's small classifier (§5.2) on its
feature subset, measure it on the held-out EVAL SLICE, feed those metrics into the W2-01
`Agent` state (§2 init formulas), and drop the hopeless (§5.3). It also builds the one
agent that is allowed to cheat — the budget+revenue sanity agent (§9.2/§10.9), the pipeline
canary — down a path the normal crowd can structurally never reach.

Where the eval metrics come from is load-bearing (spec §10.5, forbidden-shortcut #1):
`evaluate` reads a caller-supplied `eval_data` that MUST be a held-out slice of the TRAINING
split. The test split never appears in this module. Keeping train and eval as separate
arguments makes leakage a deliberate act rather than an accident.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score

from wocbots.agents.agent import Agent, ConfidenceWeights
from wocbots.agents.classifier import (
    AgentClassifier,
    ClassifierSpec,
    LabeledData,
    LabelVector,
    build_classifier,
)

_log = logging.getLogger("wocbots.agents.training")

# Spec §5.3: agents whose held-out eval accuracy is BELOW this are excluded from every
# later phase. The boundary is strict `<` — exactly 0.50 is KEPT (pinned both sides).
PRUNE_ACCURACY_THRESHOLD = 0.50

# Spec §9.2 / §10.9: with `revenue`, an agent can essentially see the label (~100%). Such
# an agent is the pipeline canary and MUST NOT enter a reported crowd — its perfect trust
# and 100 votes would dominate every aggregation (§10.9). `revenue` is therefore barred
# from normal construction; only `build_sanity_agent` may use it, on its own path.
LEAKY_FEATURES = frozenset({"revenue"})


@dataclass(frozen=True)
class EvalMetrics:
    """Accuracy / precision / recall on the eval slice (spec §9.1). These are the inputs to
    the §2 init formulas (certainty, trust_score, confidence) and to pruning (§5.3)."""

    accuracy: float
    precision: float
    recall: float


@dataclass(frozen=True)
class TrainedAgent:
    """W2-02's per-agent deliverable: the W2-01 `Agent` (state, already initialized from the
    eval metrics), its bound `classifier`, and those metrics.

    The classifier lives HERE, never on the `Agent` — the §6.5 public profile deliberately
    exposes no classifier (the W8 meta-swarm privacy boundary). W4-01's per-sample loop
    calls `predict` to set `agent.current_prediction`. `is_sanity` marks the canary so
    aggregation can keep it out of reported runs (§10.9).
    """

    agent: Agent
    classifier: AgentClassifier
    eval_metrics: EvalMetrics
    is_sanity: bool = False

    def predict(self, data: LabeledData) -> LabelVector:
        """Labels for `data`, using this agent's own feature subset (spec §5.1)."""
        return self.classifier.predict(data.select(self.agent.features))


@dataclass(frozen=True)
class PrunedRecord:
    """One pruned agent, logged (spec §5.3 — "log what was pruned")."""

    features: tuple[str, ...]
    eval_accuracy: float
    reason: str = "eval_accuracy < 0.50 (spec §5.3)"


@dataclass(frozen=True)
class PruneResult:
    """Survivors plus the pruned log. A config that prunes half its crowd is telling you the
    feature assignment is bad (spec §5.3) — hence the log is a first-class result, not a
    side effect."""

    kept: tuple[TrainedAgent, ...]
    pruned: tuple[PrunedRecord, ...] = field(default_factory=tuple)


def evaluate(
    classifier: AgentClassifier,
    eval_data: LabeledData,
    features: Sequence[str],
) -> EvalMetrics:
    """Measure a trained classifier on the held-out eval slice (spec §10.5).

    `eval_data` MUST be a slice of the TRAINING split, never the test split (spec §10.5,
    forbidden-shortcut #1). Precision/recall are for the positive class (label 1);
    `zero_division=0.0` keeps a degenerate slice (no positive predictions) from raising —
    it scores 0, which is the honest reading.
    """
    x = eval_data.select(features)
    y_true = eval_data.y
    y_pred = classifier.predict(x)
    return EvalMetrics(
        accuracy=float(accuracy_score(y_true, y_pred)),
        precision=float(precision_score(y_true, y_pred, pos_label=1, zero_division=0.0)),
        recall=float(recall_score(y_true, y_pred, pos_label=1, zero_division=0.0)),
    )


def _fit_and_initialize(
    features: Sequence[str],
    train_data: LabeledData,
    eval_data: LabeledData,
    spec: ClassifierSpec,
    confidence_weights: ConfidenceWeights,
    rng: np.random.Generator,
    *,
    is_sanity: bool,
) -> TrainedAgent:
    """Internal train → eval → initialize, WITHOUT the leak guard. Both the public crowd
    path (guarded) and the sanity path (deliberately unguarded) funnel through here so the
    train/eval/init sequence has exactly one implementation."""
    feats = tuple(features)
    if not feats:
        raise ValueError("an agent must have at least one feature")

    classifier = build_classifier(spec)
    classifier.fit(train_data.select(feats), train_data.y, rng)
    metrics = evaluate(classifier, eval_data, feats)

    # Spec §2 initialization: the Agent computes certainty/trust/confidence from these eval
    # metrics (W2-01 owns the exact formulas; W2-02 only supplies the numbers).
    agent = Agent(
        features=feats,
        eval_accuracy=metrics.accuracy,
        eval_precision=metrics.precision,
        eval_recall=metrics.recall,
        confidence_weights=confidence_weights,
    )
    return TrainedAgent(agent=agent, classifier=classifier, eval_metrics=metrics, is_sanity=is_sanity)


def train_agent(
    *,
    features: Sequence[str],
    train_data: LabeledData,
    eval_data: LabeledData,
    spec: ClassifierSpec,
    confidence_weights: ConfidenceWeights,
    rng: np.random.Generator,
) -> TrainedAgent:
    """Train one crowd agent: fit on its feature subset → evaluate on the eval slice →
    initialize its §2 state (ticket S2).

    The normal crowd path. It refuses any leaky feature (spec §10.9): you cannot build a
    revenue-seeing agent here, which is what "structurally unreachable from normal crowd
    construction" means in code. The sanity canary has its own entry point below.
    """
    leaked = LEAKY_FEATURES.intersection(features)
    if leaked:
        raise ValueError(
            f"features {sorted(leaked)} leak the label and are barred from crowd construction "
            f"(spec §10.9); build the canary via build_sanity_agent instead"
        )
    return _fit_and_initialize(
        features, train_data, eval_data, spec, confidence_weights, rng, is_sanity=False
    )


def train_crowd(
    *,
    feature_sets: Sequence[Sequence[str]],
    train_data: LabeledData,
    eval_data: LabeledData,
    spec: ClassifierSpec,
    confidence_weights: ConfidenceWeights,
    rng: np.random.Generator,
) -> PruneResult:
    """Train one agent per feature set, then prune (spec §5.3).

    Feature ASSIGNMENT is the caller's policy (W2-03), not this function's — it takes the
    subsets as given. Every agent draws its seed from the ONE threaded Generator in order,
    so the whole crowd is reproducible from a single master seed (spec §9.1).
    """
    trained = [
        train_agent(
            features=fs,
            train_data=train_data,
            eval_data=eval_data,
            spec=spec,
            confidence_weights=confidence_weights,
            rng=rng,
        )
        for fs in feature_sets
    ]
    return prune(trained)


def build_sanity_agent(
    *,
    train_data: LabeledData,
    eval_data: LabeledData,
    rng: np.random.Generator,
    spec: ClassifierSpec | None = None,
    confidence_weights: ConfidenceWeights,
) -> TrainedAgent:
    """Build the budget+revenue sanity agent — the pipeline canary (spec §9.2 / §10.9).

    A DEDICATED path, distinct from `train_agent`/`train_crowd`: it is the only constructor
    that touches `revenue`, and the crowd path can never reach it (the leak guard there
    raises). Its ~100% accuracy validates the data pipeline; if it is NOT ~100%, the ETL is
    broken (spec §9.2). It is flagged `is_sanity=True` so it sits out every reported run
    (§10.9, forbidden-shortcut #6). Requires both `budget` and `revenue` in the data.
    """
    features = ("budget", "revenue")
    missing = [f for f in features if f not in train_data.features]
    if missing:
        raise ValueError(f"sanity agent needs {sorted(missing)} in the data, which is absent")
    resolved_spec = spec if spec is not None else ClassifierSpec()
    return _fit_and_initialize(
        features, train_data, eval_data, resolved_spec, confidence_weights, rng, is_sanity=True
    )


def prune(agents: Sequence[TrainedAgent]) -> PruneResult:
    """Exclude agents with eval_accuracy < 0.50 from all later phases; log them (spec §5.3).

    The boundary is strict: exactly 0.50 is KEPT. The pruned log carries each agent's
    feature set and accuracy so a bad feature assignment is visible, not silent.
    """
    kept: list[TrainedAgent] = []
    pruned: list[PrunedRecord] = []
    for trained in agents:
        accuracy = trained.eval_metrics.accuracy
        if accuracy < PRUNE_ACCURACY_THRESHOLD:
            record = PrunedRecord(features=trained.agent.features, eval_accuracy=accuracy)
            pruned.append(record)
            _log.info(
                "pruned agent %s: eval_accuracy=%.4f (< %.2f)",
                record.features,
                accuracy,
                PRUNE_ACCURACY_THRESHOLD,
            )
        else:
            kept.append(trained)
    return PruneResult(kept=tuple(kept), pruned=tuple(pruned))
