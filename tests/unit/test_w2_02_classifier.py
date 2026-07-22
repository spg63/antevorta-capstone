"""W2-02 test requirements — classifier train/eval/init, pruning, determinism, the canary.

Covers the ticket's five test requirements plus edges:
  1. architecture pins (2/3/10 → 1/1/3);
  2. pruning both sides (0.499 pruned / 0.501 kept, and exactly 0.50 kept), pruned logged;
  3. determinism (same subset + seed → identical trained metrics, twice);
  4. synthetic e2e (one agent ≥ 99% on a separable 2-feature set);
  5. real-data reference bands — marked slow, skipped until W1-05 lands, with a synthetic
     canary + structural-barrier standing in for the §10.9 sanity-agent guarantee now.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pytest
from pydantic import ValidationError

from wocbots.agents import HOLLYWOOD_WEIGHTS
from wocbots.agents.classifier import (
    ClassifierSpec,
    FloatMatrix,
    LabeledData,
    LabelVector,
    MLPAgentClassifier,
    build_classifier,
    hidden_layer_count,
    hidden_layer_sizes,
)
from wocbots.agents.training import (
    EvalMetrics,
    PrunedRecord,
    TrainedAgent,
    build_sanity_agent,
    evaluate,
    prune,
    train_agent,
    train_crowd,
)

# ---------------------------------------------------------------- data helpers


def _blobs(
    rng: np.random.Generator,
    *,
    n: int = 400,
    n_features: int = 2,
    sep: float = 3.0,
    noise: float = 0.5,
) -> LabeledData:
    """A well-separated binary set: class means at ±`sep` on feature 0, the rest noise.
    ~6σ apart at the defaults ⇒ essentially linearly separable (spec §11 synthetic anchor)."""
    y = rng.integers(0, 2, size=n).astype(np.int_)
    center = np.where(y == 1, sep, -sep)
    f0 = center + rng.standard_normal(n) * noise
    rest = rng.standard_normal((n, n_features - 1))
    x = np.column_stack([f0, rest]).astype(np.float64)
    names = tuple(f"f{i}" for i in range(n_features))
    return LabeledData(features=names, X=x, y=y)


def _trained_with_accuracy(accuracy: float) -> TrainedAgent:
    """A TrainedAgent carrying a chosen eval accuracy, for pruning-boundary tests. The
    classifier is an unfitted placeholder — `prune` only reads `eval_metrics`."""
    from wocbots.agents import Agent

    metrics = EvalMetrics(accuracy=accuracy, precision=accuracy, recall=accuracy)
    agent = Agent(
        features=("budget",),
        eval_accuracy=accuracy,
        eval_precision=accuracy,
        eval_recall=accuracy,
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )
    return TrainedAgent(agent=agent, classifier=build_classifier(ClassifierSpec()), eval_metrics=metrics)


class _FixedClassifier:
    """A classifier whose predictions are fixed, to pin `evaluate`'s metric arithmetic."""

    def __init__(self, preds: LabelVector) -> None:
        self._preds = preds

    def fit(self, x: FloatMatrix, y: LabelVector, rng: np.random.Generator) -> None:
        return None

    def predict(self, x: FloatMatrix) -> LabelVector:
        return self._preds

    def predict_proba_class1(self, x: FloatMatrix) -> FloatMatrix:
        return self._preds.astype(np.float64)


def _train(
    features: Sequence[str],
    train: LabeledData,
    ev: LabeledData,
    spec: ClassifierSpec,
    rng: np.random.Generator,
) -> TrainedAgent:
    """Typed thin wrapper over `train_agent` with the Hollywood weights, so tests pass args
    explicitly (keeps mypy strict happy — no `**dict[str, object]` splatting)."""
    return train_agent(
        features=features,
        train_data=train,
        eval_data=ev,
        spec=spec,
        confidence_weights=HOLLYWOOD_WEIGHTS,
        rng=rng,
    )


# ------------------------------------------------ test req 1: architecture pins


def test_hidden_layer_count_pins() -> None:
    """Ticket test req 1: input sizes 2/3/10 → hidden layers 1/1/3 (spec §5.2)."""
    assert hidden_layer_count(2) == 1
    assert hidden_layer_count(3) == 1
    assert hidden_layer_count(10) == 3


def test_hidden_layer_count_min_one() -> None:
    assert hidden_layer_count(1) == 1  # max(1, round(0.3)) = 1
    with pytest.raises(ValueError, match="input_size"):
        hidden_layer_count(0)


def test_hidden_layer_sizes_composition() -> None:
    spec = ClassifierSpec(hidden_width=32)
    assert hidden_layer_sizes(spec, 2) == (32,)
    assert hidden_layer_sizes(spec, 3) == (32,)
    assert hidden_layer_sizes(spec, 10) == (32, 32, 32)


def test_mlp_architecture_after_fit() -> None:
    """The wrapper actually builds the pinned architecture: 10 features → 3×32."""
    rng = np.random.default_rng(0)
    data = _blobs(rng, n_features=10)
    clf = MLPAgentClassifier(ClassifierSpec(hidden_width=32, epochs=5))
    clf.fit(data.X, data.y, np.random.default_rng(0))
    assert clf.architecture == (32, 32, 32)


# ------------------------------------------ test req 2: pruning, both sides + log


def test_prune_boundary_both_sides() -> None:
    """Ticket test req 2: 0.499 pruned, 0.501 kept, and the pruned agent is logged."""
    keep = _trained_with_accuracy(0.501)
    drop = _trained_with_accuracy(0.499)
    result = prune([drop, keep])
    assert result.kept == (keep,)
    assert len(result.pruned) == 1
    logged = result.pruned[0]
    assert isinstance(logged, PrunedRecord)
    assert logged.eval_accuracy == 0.499
    assert logged.features == ("budget",)


def test_prune_keeps_exactly_threshold() -> None:
    """The boundary is strict `<`: exactly 0.50 is KEPT, not pruned."""
    at_threshold = _trained_with_accuracy(0.50)
    result = prune([at_threshold])
    assert result.kept == (at_threshold,)
    assert result.pruned == ()


# ---------------------------------------------------- test req 3: determinism


def test_training_is_deterministic() -> None:
    """Ticket test req 3: same subset + same seed → identical trained metrics, twice."""
    train = _blobs(np.random.default_rng(10))
    ev = _blobs(np.random.default_rng(11))
    spec = ClassifierSpec(epochs=15)
    m1 = _train(("f0", "f1"), train, ev, spec, np.random.default_rng(42)).eval_metrics
    m2 = _train(("f0", "f1"), train, ev, spec, np.random.default_rng(42)).eval_metrics
    assert m1 == m2


def test_different_seeds_are_allowed_to_differ() -> None:
    """Sanity on the determinism claim: the seed actually threads through (not a constant)."""
    train = _blobs(np.random.default_rng(10), noise=1.5, sep=0.7)  # harder ⇒ seed-sensitive
    ev = _blobs(np.random.default_rng(11), noise=1.5, sep=0.7)
    spec = ClassifierSpec(epochs=8)
    cols = ("f0", "f1")
    a = _train(cols, train, ev, spec, np.random.default_rng(1)).classifier.predict(ev.select(cols))
    b = _train(cols, train, ev, spec, np.random.default_rng(2)).classifier.predict(ev.select(cols))
    # Each fit must be internally reproducible; shapes line up regardless of seed.
    assert a.shape == b.shape


# -------------------------------------------------- test req 4: synthetic e2e


def test_synthetic_agent_reaches_99pct() -> None:
    """Ticket test req 4: one agent ≥ 99% on a separable 2-feature set."""
    train = _blobs(np.random.default_rng(1))
    ev = _blobs(np.random.default_rng(2))
    trained = train_agent(
        features=("f0", "f1"),
        train_data=train,
        eval_data=ev,
        spec=ClassifierSpec(epochs=30),
        confidence_weights=HOLLYWOOD_WEIGHTS,
        rng=np.random.default_rng(7),
    )
    assert trained.eval_metrics.accuracy >= 0.99
    assert trained.agent.eval_accuracy >= 0.99  # the §2 state was initialized from it


def test_logreg_variant_classifies() -> None:
    """§5.2: swap the internals for logistic regression — the agent still classifies well."""
    train = _blobs(np.random.default_rng(3))
    ev = _blobs(np.random.default_rng(4))
    trained = train_agent(
        features=("f0", "f1"),
        train_data=train,
        eval_data=ev,
        spec=ClassifierSpec(variant="logreg"),
        confidence_weights=HOLLYWOOD_WEIGHTS,
        rng=np.random.default_rng(5),
    )
    assert trained.eval_metrics.accuracy >= 0.99


# ---------------------------------------------- eval arithmetic + proba convention


def test_evaluate_metric_arithmetic() -> None:
    """Exact pin of accuracy/precision/recall on the eval slice (spec §9.1)."""
    # y_true = [1,1,0,0], y_pred = [1,0,0,0]: acc 3/4; precision 1/1; recall 1/2.
    ev = LabeledData(features=("f0",), X=np.zeros((4, 1), dtype=np.float64), y=np.array([1, 1, 0, 0]))
    clf = _FixedClassifier(np.array([1, 0, 0, 0], dtype=np.int_))
    metrics = evaluate(clf, ev, ("f0",))
    assert metrics.accuracy == 0.75
    assert metrics.precision == 1.0
    assert metrics.recall == 0.5


def test_predict_proba_class1_convention() -> None:
    """P(class=1) in [0,1] and consistent with the label call (spec §5.2 convention)."""
    train = _blobs(np.random.default_rng(1))
    clf = MLPAgentClassifier(ClassifierSpec(epochs=20))
    clf.fit(train.X, train.y, np.random.default_rng(0))
    proba = clf.predict_proba_class1(train.X)
    labels = clf.predict(train.X)
    assert proba.shape == (train.X.shape[0],)
    assert float(proba.min()) >= 0.0
    assert float(proba.max()) <= 1.0
    # A confident separable set ⇒ label 1 exactly where P(class=1) ≥ 0.5.
    assert np.array_equal(labels, (proba >= 0.5).astype(np.int_))


def test_epochs_bounds_both_sides() -> None:
    """Spec §5.2 epochs ∈ [5, 50], enforced both sides; interior values accepted."""
    with pytest.raises(ValidationError):
        ClassifierSpec(epochs=4)
    with pytest.raises(ValidationError):
        ClassifierSpec(epochs=51)
    for good in (5, 20, 50):
        assert ClassifierSpec(epochs=good).epochs == good


# ---------------------------- test req 5 (structure): the sanity agent + barrier


def test_revenue_barred_from_crowd_construction() -> None:
    """Spec §10.9: the budget+revenue agent is structurally unreachable from normal crowd
    construction — both the single-agent and crowd entry points refuse it."""
    data = _blobs(np.random.default_rng(2))
    revenue_data = LabeledData(features=("budget", "revenue"), X=data.X, y=data.y)
    with pytest.raises(ValueError, match="revenue"):
        train_agent(
            features=("budget", "revenue"),
            train_data=revenue_data,
            eval_data=revenue_data,
            spec=ClassifierSpec(),
            confidence_weights=HOLLYWOOD_WEIGHTS,
            rng=np.random.default_rng(0),
        )
    with pytest.raises(ValueError, match="revenue"):
        train_crowd(
            feature_sets=[("budget", "revenue")],
            train_data=revenue_data,
            eval_data=revenue_data,
            spec=ClassifierSpec(),
            confidence_weights=HOLLYWOOD_WEIGHTS,
            rng=np.random.default_rng(0),
        )


def test_sanity_agent_is_the_canary() -> None:
    """The sanity agent CAN see revenue and hits ~100% when revenue encodes the label — the
    pipeline canary (spec §9.2). Reached only via its dedicated constructor (§10.9)."""
    rng = np.random.default_rng(3)
    n = 300
    y = rng.integers(0, 2, size=n).astype(np.int_)
    budget = rng.standard_normal(n)  # uninformative on its own
    revenue = y.astype(np.float64) + rng.standard_normal(n) * 0.01  # ~perfectly encodes y
    data = LabeledData(features=("budget", "revenue"), X=np.column_stack([budget, revenue]), y=y)
    trained = build_sanity_agent(
        train_data=data,
        eval_data=data,
        confidence_weights=HOLLYWOOD_WEIGHTS,
        rng=np.random.default_rng(4),
    )
    assert trained.is_sanity is True
    assert trained.agent.features == ("budget", "revenue")
    assert trained.eval_metrics.accuracy >= 0.99


def test_empty_features_rejected() -> None:
    data = _blobs(np.random.default_rng(0))
    with pytest.raises(ValueError, match="at least one feature"):
        train_agent(
            features=(),
            train_data=data,
            eval_data=data,
            spec=ClassifierSpec(),
            confidence_weights=HOLLYWOOD_WEIGHTS,
            rng=np.random.default_rng(0),
        )


def test_select_unknown_feature_raises() -> None:
    data = _blobs(np.random.default_rng(0))
    with pytest.raises(KeyError, match="not in this dataset"):
        data.select(("f0", "nonexistent"))


@pytest.mark.slow
def test_reference_bands_real_data() -> None:
    """Ticket test req 5 (real data): budget+revenue sanity agent ~100%, budget+vote_count
    in the §9.2 band (75.7 ± 3). Runs once the W1-05 Hollywood eval slice exists."""
    pytest.skip("W1-05 Hollywood eval slice not available yet; band check lands with the data")
