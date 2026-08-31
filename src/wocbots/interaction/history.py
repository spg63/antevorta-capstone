"""W3-04 — Interaction history store and query interface (spec §6.5).

Records directed interaction history per (agent, partner, sample) and provides
querying, b_percCorrect computation, and Phase-4 ground truth backfilling.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import pandas as pd

if TYPE_CHECKING:
    from wocbots.agents import Agent


@dataclass
class HistoryRecord:
    """A single directed interaction record (spec §6.5).

    Represents `agent`'s perspective of an encounter with `partner`.
    """

    sample_id: int | str
    round_num: int
    agent: Agent
    partner: Agent
    agent_prediction: Literal[0, 1]
    partner_prediction: Literal[0, 1]
    agreement: bool
    certainty_before: float
    certainty_after: float
    certainty_delta: float
    prediction_flipped: bool
    partner_correct: bool | None = None
    ground_truth: Literal[0, 1] | None = None


class HistoryStore:
    """Queryable in-memory store for directed interaction histories."""

    def __init__(self) -> None:
        self._records: list[HistoryRecord] = []
        self._by_pair: dict[tuple[Agent, Agent], list[HistoryRecord]] = defaultdict(list)
        self._by_sample: dict[int | str, list[HistoryRecord]] = defaultdict(list)

    def record(self, record: HistoryRecord) -> None:
        """Append a directed history record and update indices."""
        self._records.append(record)
        self._by_pair[(record.agent, record.partner)].append(record)
        self._by_sample[record.sample_id].append(record)

    def get_interactions(
        self,
        *,
        agent: Agent | None = None,
        partner: Agent | None = None,
        sample_id: int | str | None = None,
    ) -> Sequence[HistoryRecord]:
        """Query interactions matching the given filters."""
        if agent is not None and partner is not None:
            records = self._by_pair.get((agent, partner), [])
            if sample_id is not None:
                return [r for r in records if r.sample_id == sample_id]
            return list(records)
        if sample_id is not None:
            records = self._by_sample.get(sample_id, [])
            if agent is not None:
                records = [r for r in records if r.agent == agent]
            if partner is not None:
                records = [r for r in records if r.partner == partner]
            return list(records)
        if agent is not None:
            return [r for r in self._records if r.agent == agent]
        if partner is not None:
            return [r for r in self._records if r.partner == partner]
        return list(self._records)

    def get_perc_correct(self, agent: Agent, partner: Agent) -> float | None:
        """Compute b_percCorrect: fraction of scored past interactions where partner was correct.

        Returns None if no scored past interactions exist between agent and partner (spec §6.5).
        """
        records = self._by_pair.get((agent, partner), [])
        scored = [r for r in records if r.partner_correct is not None]
        if not scored:
            return None
        correct_count = sum(1 for r in scored if r.partner_correct is True)
        return correct_count / len(scored)

    def backfill_correctness(self, sample_id: int | str, ground_truth: Literal[0, 1]) -> int:
        """Backfill ground truth correctness for all interactions in sample_id (spec §6.7).

        Returns the number of records updated.
        """
        records = self._by_sample.get(sample_id, [])
        for record in records:
            record.ground_truth = ground_truth
            record.partner_correct = record.partner_prediction == ground_truth
        return len(records)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert all records to a tidy pandas DataFrame."""
        rows: list[dict[str, Any]] = [
            {
                "sample_id": r.sample_id,
                "round": r.round_num,
                "agent": r.agent,
                "partner": r.partner,
                "agent_prediction": r.agent_prediction,
                "partner_prediction": r.partner_prediction,
                "agreement": r.agreement,
                "certainty_before": r.certainty_before,
                "certainty_after": r.certainty_after,
                "certainty_delta": r.certainty_delta,
                "prediction_flipped": r.prediction_flipped,
                "partner_correct": r.partner_correct,
                "ground_truth": r.ground_truth,
            }
            for r in self._records
        ]
        return pd.DataFrame(rows)

    def __len__(self) -> int:
        return len(self._records)
