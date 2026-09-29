"""W4-02 — ground-truth feedback and track-record evolution (spec §6.7, §3 degenerate)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal, Protocol

from wocbots.agents import Agent

_COLD_START_THRESHOLD = 5
_PRIOR_PERF_SLOPE = 0.6
_PRIOR_PERF_MIN = 0.7
_PRIOR_PERF_MAX = 1.3


class HistoryCorrectnessHook(Protocol):
    """W3-04 back-fill surface; stub until the history store lands."""

    def mark_prediction_correctness(
        self,
        agent: Agent,
        *,
        prediction: Literal[0, 1],
        was_correct: bool,
    ) -> None: ...


@dataclass
class AgentInferenceRecord:
    """Per-agent inference counters (spec §6.7 running accuracy)."""

    scored_count: int = 0
    correct_count: int = 0

    @property
    def running_accuracy(self) -> float:
        if self.scored_count == 0:
            return 0.0
        return self.correct_count / self.scored_count


@dataclass
class FeedbackState:
    """Crowd-level feedback bookkeeping for one evaluation run."""

    records: dict[int, AgentInferenceRecord] = field(default_factory=dict)
    degenerate_crowd_count: int = 0

    def record_for(self, agent: Agent) -> AgentInferenceRecord:
        key = id(agent)
        if key not in self.records:
            self.records[key] = AgentInferenceRecord()
        return self.records[key]


def prior_performance_from_running_acc(running_acc: float, *, scored_count: int) -> float:
    """§6.7 priorPerf mapping; held at 1.0 until ≥ 5 scored predictions."""
    if scored_count < _COLD_START_THRESHOLD:
        return 1.0
    raw = 1.0 + _PRIOR_PERF_SLOPE * (running_acc - 0.5)
    return max(_PRIOR_PERF_MIN, min(_PRIOR_PERF_MAX, raw))


def apply_ground_truth(
    participants: Sequence[Agent],
    label: int | None,
    state: FeedbackState,
    *,
    history: HistoryCorrectnessHook | None = None,
) -> None:
    """Update track records after a labeled sample (spec §6.7). Unlabeled → no-op."""
    if label is None:
        return
    if label not in (0, 1):
        raise ValueError(f"label must be 0 or 1, got {label!r}")

    for agent in participants:
        if agent.current_prediction is None:
            continue
        prediction = agent.current_prediction
        was_correct = prediction == label
        record = state.record_for(agent)
        record.scored_count += 1
        if was_correct:
            record.correct_count += 1

        if history is not None:
            history.mark_prediction_correctness(agent, prediction=prediction, was_correct=was_correct)

        if record.scored_count >= _COLD_START_THRESHOLD:
            agent.prior_accuracy = record.running_accuracy
            agent.prior_performance = prior_performance_from_running_acc(
                record.running_accuracy,
                scored_count=record.scored_count,
            )


def record_degenerate_crowd(state: FeedbackState) -> None:
    """Increment manifest counter when N < 3 (spec §3)."""
    state.degenerate_crowd_count += 1
