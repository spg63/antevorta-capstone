"""W4-01 / W4-04 — test-set evaluation and mechanism comparison helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal, cast

import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score

from wocbots.agents import Agent
from wocbots.agents.classifier import LabeledData
from wocbots.agents.training import TrainedAgent
from wocbots.aggregation import TrustWeightedAggregator, UWMAggregator, WVMAggregator
from wocbots.aggregation.voting import certainty_weighted_vote
from wocbots.experiments.arena_interaction import ArenaRoundInteractionRunner
from wocbots.experiments.feedback import FeedbackState, apply_ground_truth, record_degenerate_crowd
from wocbots.experiments.lifecycle import (
    InteractionPeriodRunner,
    LifecycleRunState,
    SampleFeatures,
    SampleResult,
    backfill_arena_history,
    infer_participants,
    prepare_arena_runner,
    run_sample,
    select_participants,
)
from wocbots.protocols import Aggregator
from wocbots.types import Prediction

_DEGENERATE_THRESHOLD = 3
_LOW_CONFIDENCE_TIER = "low"
_MECHANISM_KEYS = ("uwm", "wvm", "trust")
_ALL_TIER_NAMES = (
    "near-certain",
    "very-high",
    "high",
    "medium",
    "low",
    "coin-flip",
)


@dataclass(frozen=True)
class ClassificationMetrics:
    """Accuracy / precision / recall on a labeled pass (spec §9.1)."""

    accuracy: float
    precision: float
    recall: float


@dataclass
class EvaluationSummary:
    """One evaluation pass over a test set."""

    metrics: ClassificationMetrics
    participant_counts: list[int]
    degenerate_crowd_count: int
    sample_results: list[SampleResult] = field(default_factory=list)


@dataclass
class MechanismComparisonSummary:
    """Three-mechanism pass with per-tier stats for trust-weighted (W4-04 S2)."""

    metrics: dict[str, ClassificationMetrics]
    participant_counts: list[int]
    degenerate_crowd_count: int
    tier_accuracy: dict[str, float]
    tier_coverage: dict[str, float]


def _slice_row(data: LabeledData, index: int) -> LabeledData:
    return LabeledData(
        features=data.features,
        X=data.X[index : index + 1],
        y=data.y[index : index + 1],
    )


def row_features(data: LabeledData, index: int) -> SampleFeatures:
    values = {name: float(data.X[index, col]) for col, name in enumerate(data.features)}
    return SampleFeatures(values=values)


def agent_predictions(
    trained: Sequence[TrainedAgent],
    data: LabeledData,
    index: int,
) -> dict[int, Literal[0, 1]]:
    row = _slice_row(data, index)
    preds: dict[int, Literal[0, 1]] = {}
    for item in trained:
        label = int(item.predict(row)[0])
        if label not in (0, 1):
            raise ValueError(f"agent prediction must be 0 or 1, got {label!r}")
        preds[id(item.agent)] = cast(Literal[0, 1], label)
    return preds


def _classification_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> ClassificationMetrics:
    return ClassificationMetrics(
        accuracy=float(accuracy_score(y_true, y_pred)),
        precision=float(precision_score(y_true, y_pred, zero_division=0)),
        recall=float(recall_score(y_true, y_pred, zero_division=0)),
    )


def run_test_set(
    trained: Sequence[TrainedAgent],
    test_data: LabeledData,
    *,
    rng: np.random.Generator,
    aggregator: Aggregator | None = None,
    interaction: InteractionPeriodRunner | None = None,
    pruned: set[int] | None = None,
) -> EvaluationSummary:
    """Run the W4-01 infer → arena → aggregate loop over every test row."""
    agents = [item.agent for item in trained]
    agg = aggregator or UWMAggregator()
    runner = interaction or ArenaRoundInteractionRunner()
    state = LifecycleRunState()
    y_pred: list[int] = []

    for index in range(test_data.X.shape[0]):
        result = run_sample(
            agents,
            row_features(test_data, index),
            agent_predictions(trained, test_data, index),
            rng=rng,
            aggregator=agg,
            interaction=runner,
            pruned=pruned,
            label=int(test_data.y[index]),
            state=state,
        )
        y_pred.append(result.prediction.class_label)

    metrics = _classification_metrics(test_data.y, np.array(y_pred, dtype=np.int_))
    return EvaluationSummary(
        metrics=metrics,
        participant_counts=[r.participant_count for r in state.sample_results],
        degenerate_crowd_count=state.feedback.degenerate_crowd_count,
        sample_results=list(state.sample_results),
    )


def _aggregate_all_mechanisms(
    participants: Sequence[Agent],
    *,
    rng: np.random.Generator,
    degenerate: bool,
) -> dict[str, Prediction]:
    if degenerate:
        outcome = certainty_weighted_vote(participants)
        base = outcome.to_prediction()
        shared = Prediction(
            class_label=base.class_label,
            tier=_LOW_CONFIDENCE_TIER,
            margin=base.margin,
        )
        return dict.fromkeys(_MECHANISM_KEYS, shared)

    uwm = UWMAggregator().aggregate(participants, rng)
    wvm = WVMAggregator().aggregate(participants, rng)
    trust = TrustWeightedAggregator().aggregate(participants, rng)
    return {"uwm": uwm, "wvm": wvm, "trust": trust}


def run_mechanism_comparison(
    trained: Sequence[TrainedAgent],
    test_data: LabeledData,
    *,
    rng: np.random.Generator,
    interaction: InteractionPeriodRunner | None = None,
    pruned: set[int] | None = None,
) -> MechanismComparisonSummary:
    """One labeled pass; all three aggregators on identical participant snapshots (W4-04 S2)."""
    agents = [item.agent for item in trained]
    runner = interaction or ArenaRoundInteractionRunner()
    feedback = FeedbackState()
    participant_counts: list[int] = []

    predictions: dict[str, list[int]] = {key: [] for key in _MECHANISM_KEYS}
    tier_totals: dict[str, int] = {}
    tier_correct: dict[str, int] = {}

    for index in range(test_data.X.shape[0]):
        sample = row_features(test_data, index)
        preds = agent_predictions(trained, test_data, index)
        participants, _skipped = select_participants(agents, sample, pruned=pruned)
        infer_participants(participants, preds)
        participant_counts.append(len(participants))
        prepare_arena_runner(runner, index)

        degenerate = len(participants) < _DEGENERATE_THRESHOLD
        if degenerate:
            record_degenerate_crowd(feedback)
        else:
            runner.run(participants, rng=rng)

        mechanism_preds = _aggregate_all_mechanisms(participants, rng=rng, degenerate=degenerate)
        label = int(test_data.y[index])
        apply_ground_truth(participants, label, feedback)
        backfill_arena_history(runner, index, label)

        for key, prediction in mechanism_preds.items():
            predictions[key].append(prediction.class_label)
            if key == "trust" and prediction.tier is not None:
                tier = prediction.tier
                tier_totals[tier] = tier_totals.get(tier, 0) + 1
                if prediction.class_label == label:
                    tier_correct[tier] = tier_correct.get(tier, 0) + 1

    n_samples = test_data.X.shape[0]
    metrics = {
        key: _classification_metrics(
            test_data.y,
            np.array(predictions[key], dtype=np.int_),
        )
        for key in _MECHANISM_KEYS
    }
    tier_accuracy = {tier: tier_correct.get(tier, 0) / tier_totals[tier] for tier in tier_totals}
    tier_coverage = {tier: count / n_samples for tier, count in tier_totals.items()}

    return MechanismComparisonSummary(
        metrics=metrics,
        participant_counts=participant_counts,
        degenerate_crowd_count=feedback.degenerate_crowd_count,
        tier_accuracy=tier_accuracy,
        tier_coverage=tier_coverage,
    )


def _participant_manifest_metrics(counts: list[int]) -> dict[str, float]:
    """Per-sample participant counts + summary stats for manifest recording (W4-01 S3)."""
    if not counts:
        return {
            "mean_participants": 0.0,
            "min_participants": 0.0,
            "max_participants": 0.0,
            "n_test_samples": 0.0,
        }
    arr = np.array(counts, dtype=float)
    out: dict[str, float] = {
        "mean_participants": float(arr.mean()),
        "min_participants": float(arr.min()),
        "max_participants": float(arr.max()),
        "n_test_samples": float(len(counts)),
    }
    for index, count in enumerate(counts):
        out[f"participant_count_s{index:03d}"] = float(count)
    return out


def evaluation_summary_to_dict(summary: EvaluationSummary) -> Mapping[str, float]:
    """Flatten an evaluation pass for manifest recording."""
    out: dict[str, float] = {
        "accuracy": summary.metrics.accuracy,
        "precision": summary.metrics.precision,
        "recall": summary.metrics.recall,
        "degenerate_crowd_count": float(summary.degenerate_crowd_count),
    }
    out.update(_participant_manifest_metrics(summary.participant_counts))
    return out


def metrics_to_dict(summary: MechanismComparisonSummary) -> Mapping[str, float]:
    """Flatten a mechanism comparison for manifest recording."""
    out: dict[str, float] = {
        "degenerate_crowd_count": float(summary.degenerate_crowd_count),
    }
    out.update(_participant_manifest_metrics(summary.participant_counts))
    for key in _MECHANISM_KEYS:
        m = summary.metrics[key]
        out[f"{key}_accuracy"] = m.accuracy
        out[f"{key}_precision"] = m.precision
        out[f"{key}_recall"] = m.recall
    for tier in _ALL_TIER_NAMES:
        safe = tier.replace("-", "_")
        out[f"trust_tier_{safe}_accuracy"] = summary.tier_accuracy.get(tier, 0.0)
        out[f"trust_tier_{safe}_coverage"] = summary.tier_coverage.get(tier, 0.0)
    return out
