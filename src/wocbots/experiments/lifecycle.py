"""W4-01 — per-sample lifecycle loop (spec §3 phases 2–4, §6.6).

Wires participant selection, certainty reset, optional interaction (ARENA/W3),
and aggregation. Ground-truth feedback is W4-02 (`apply_ground_truth`).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal, Protocol

import numpy as np

from wocbots.agents import Agent
from wocbots.aggregation.voting import UWMAggregator, certainty_weighted_vote
from wocbots.experiments.feedback import FeedbackState, apply_ground_truth, record_degenerate_crowd
from wocbots.protocols import Aggregator
from wocbots.types import Prediction

_DEGENERATE_THRESHOLD = 3
_LOW_CONFIDENCE_TIER = "low"


class InteractionPeriodRunner(Protocol):
    """W3 delivers the real arena; tests and early integration use a stub."""

    def run(self, participants: Sequence[Agent], *, rng: np.random.Generator) -> None: ...


class NoOpInteractionRunner:
    """Stub: predictions unchanged (for loop-semantics tests before W3 lands)."""

    def run(self, participants: Sequence[Agent], *, rng: np.random.Generator) -> None:
        del participants, rng


@dataclass(frozen=True)
class SampleFeatures:
    """Feature values for one test row; missing keys mean sit-out for agents needing them."""

    values: Mapping[str, float | int]


@dataclass
class SampleResult:
    """One sample's outcome for manifest accounting."""

    participant_count: int
    prediction: Prediction
    used_degenerate_path: bool
    skipped_agents: int


@dataclass
class LifecycleRunState:
    """Accumulated state across a test-set pass."""

    sample_results: list[SampleResult] = field(default_factory=list)
    feedback: FeedbackState = field(default_factory=FeedbackState)


def select_participants(
    agents: Sequence[Agent],
    sample: SampleFeatures,
    *,
    pruned: set[int] | None = None,
) -> tuple[list[Agent], int]:
    """Exclude pruned agents and any agent missing a required feature (spec §3)."""
    pruned_ids = pruned or set()
    selected: list[Agent] = []
    skipped = 0
    for agent in agents:
        if id(agent) in pruned_ids:
            skipped += 1
            continue
        if any(feature not in sample.values for feature in agent.features):
            skipped += 1
            continue
        selected.append(agent)
    return selected, skipped


def interaction_round_count(participant_count: int) -> int:
    """spec §6.4: max(10, round(0.1 × N))."""
    return max(10, round(0.1 * participant_count))


def arena_cell_count(participant_count: int) -> int:
    """spec §6.1: 2 × N spaces (near-square layout computed elsewhere in W3-01)."""
    return 2 * participant_count


def infer_participants(participants: Sequence[Agent], predictions: Mapping[int, Literal[0, 1]]) -> None:
    """Phase 2: set fresh predictions and reset certainty (spec §6.6)."""
    for agent in participants:
        key = id(agent)
        if key not in predictions:
            raise KeyError(f"no prediction supplied for agent {key!r}")
        agent.current_prediction = predictions[key]
        agent.reset_certainty()


def run_sample(
    agents: Sequence[Agent],
    sample: SampleFeatures,
    predictions: Mapping[int, Literal[0, 1]],
    *,
    rng: np.random.Generator,
    aggregator: Aggregator | None = None,
    interaction: InteractionPeriodRunner | None = None,
    pruned: set[int] | None = None,
    label: int | None = None,
    state: LifecycleRunState | None = None,
) -> SampleResult:
    """Execute phases 2–4 for one sample; optional label triggers W4-02 feedback."""
    run_state = state or LifecycleRunState()
    participants, skipped = select_participants(agents, sample, pruned=pruned)
    infer_participants(participants, predictions)

    agg = aggregator or UWMAggregator()
    runner = interaction or NoOpInteractionRunner()

    if len(participants) < _DEGENERATE_THRESHOLD:
        record_degenerate_crowd(run_state.feedback)
        outcome = certainty_weighted_vote(participants)
        prediction = Prediction(
            class_label=outcome.class_label,
            tier=_LOW_CONFIDENCE_TIER,
            margin=None,
        )
        result = SampleResult(
            participant_count=len(participants),
            prediction=prediction,
            used_degenerate_path=True,
            skipped_agents=skipped,
        )
    else:
        # W3-01..04 own geometry, movement, scoring inside `runner`.
        _ = arena_cell_count(len(participants))
        _ = interaction_round_count(len(participants))
        runner.run(participants, rng=rng)
        prediction = agg.aggregate(participants, rng)
        result = SampleResult(
            participant_count=len(participants),
            prediction=prediction,
            used_degenerate_path=False,
            skipped_agents=skipped,
        )

    apply_ground_truth(participants, label, run_state.feedback)
    run_state.sample_results.append(result)
    return result
