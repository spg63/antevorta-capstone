# W3-04 — Interaction history store and trust updates — IMPLEMENTATION PLAN

> **STATUS: DRAFT**
>
> **About this plan.** This is the per-ticket execution plan for
> `W3-04_history-trust.md`, following the W3 plan skeleton
> (`WX-YY_template_PLAN.md`), mirroring `W3-03_certainty-update-flip_PLAN.md`'s
> and `W3-02_movement-rounds_PLAN.md`'s conventions (Decisions with rejected
> alternatives, execution-path maps, exact-pin test plans).

**Ticket:** [`W3-04_history-trust.md`](./W3-04_history-trust.md)

**Precedence:** the spec > this plan > the ticket.

**Wave:** W3

**Blocked by:** W3-03

**Blocks:** W4-01

**Binding spec sections:**
- [§6.5 The interaction (certainty & trust
  updates)](../docs/WoC-Bots_Implementation_Spec.md#65-the-interaction-certainty--trust-updates)
  (trust update equation, $b_{percCorrect}$, $doAgree$, $[0, 1]$ clamp, history
  requirement, queryability, backfill hook)
- [§2 Vocabulary & Agent
  State](../docs/WoC-Bots_Implementation_Spec.md#2-vocabulary--agent-state)
  (`trust_score`, interaction history persistence across samples, the two
  performance scales)
- [§10.2 Pitfall 2: Conflated performance
  scales](../docs/WoC-Bots_Implementation_Spec.md#10-pitfalls-read-before-debugging)
  (`prior_performance` multiplier in $[0.7, 1.3]$ vs `prior_accuracy` rate in
  $[0, 1]$)

**Binding preamble sections:** `01_MANDATORY_PREAMBLE.md` applies in full.

**Severity of getting it wrong:** high. Trust dynamics govern the social
aggregation and long-term memory of the crowd. A bug in trust updating (e.g.,
updating on first contact, confusing `prior_performance` with `prior_accuracy`,
unclamped trust drift, or broken history cardinality) corrupts social influence
propagation in W3/W4, distorts vote weighting in W4-03, and breaks downstream
swarm fitness and tiering in W6.

**Ruling authority:** stakeholder (spg63) for anything this plan flags as
open; independent reviewer (preamble §8) for the close.

---

## 1. Metadata

Re-read this session, in full, before writing this plan:
- `01_MANDATORY_PREAMBLE.md` (all 10 sections)
- `tickets/00_INDEX.md` (statuses, stream ownership, W3 wave boundaries)
- `tickets/W3-04_history-trust.md` (the ticket file in full)
- `tickets/W3-03_certainty-update-flip.md`,
  `tickets/W3-03_certainty-update-flip_PLAN.md`,
  `tickets/W3-03_certainty-update-flip_CLOSING-REPORT.md` (upstream interaction
  kernel contracts)
- Spec §2 (Agent state table), §6.5 (Interaction, trust updates, history MUST),
  §6.6 (Per-sample reset semantics), §6.7 (Ground-truth feedback), §10.2
  (Conflated performance scales)
- `src/wocbots/protocols.py`, `src/wocbots/types.py` (locked seams)
- `src/wocbots/agents/agent.py` (`Agent` state, `trust_score`,
  `public_profile()`)
- `src/wocbots/interaction/` (`scoring.py`, `policy.py`, `encounter.py`,
  `_util.py`)
- `src/wocbots/arena/` (`arena.py`, `round_engine.py`, `movement_policy.py`)
- `tickets/W4-01_participant-selection-loop.md`,
  `tickets/W4-02_ground-truth-feedback.md` (downstream consumers of history
  store and trust)
- `AGENT_HANDOFF.md` (current state and baseline checks)
- Check suite status: baseline verified green (218 passed, 11 skipped, 1
  xfailed; ruff and mypy strict clean).

---

## 2. Why this ticket exists (system meaning)

The crowd's long-term social memory: who told whom what, and — once ground truth
arrives — who was right. The interaction history store is both the substrate
for the trust mechanism and the primary scientific analysis instrument for
tracing opinion flow, influence chains, and persuasion accuracy across the
swarm.

In Phase 3 (the arena), when agents interact, their trust in each other evolves
based on past track records. When ground truth is revealed in Phase 4 (W4-02),
the history store is back-filled with correctness outcomes. This ticket builds
the history store, query interfaces, correctness back-fill hook, and the exact
§6.5 trust update mechanism.

---

## 3. Decisions

- **D1 — History Storage and Query Model (`HistoryRecord` & `HistoryStore`).**
  The history store must be queryable without archaeological effort (spec §6.5:
  "a tidy DataFrame or SQLite table beats nested dicts"). We define an immutable
  `HistoryRecord` dataclass capturing the directed view of an encounter, and a
  dedicated `HistoryStore` managing in-memory directed records with fast lookup
  indices `(agent, partner)` and `(sample_id)`. `HistoryStore` exposes:
  1. `record(record: HistoryRecord) -> None`
  2. `get_interactions(agent=..., partner=..., sample_id=...) -> Sequence[HistoryRecord]`
  3. `get_perc_correct(agent: Agent, partner: Agent) -> float | None` (the exact $b_{percCorrect}$ needed by §6.5)
  4. `backfill_correctness(sample_id: int | str, ground_truth: int) -> int`
  5. `to_dataframe() -> pd.DataFrame` producing a tidy, analysis-ready DataFrame.
  *Rationale:* Dataclass-backed storage with specialized index mappings gives
  $O(1)$ append, $O(1)$ partner-history retrieval during interactions, and
  instant tidy DataFrame serialization via `pd.DataFrame.from_records()` for
  scientific analysis and debugging.
  *Rejected alternative:* Storing directly in an on-disk SQLite table during
  every encounter. Rejected because writing to disk inside the inner arena loop
  adds I/O overhead without algorithmic benefit; an in-memory store with tidy
  DataFrame export fulfills both speed and queryability requirements.

- **D2 — Cardinality and Directed History Capture.**
  Per the 2026-07-07 control plane ruling and ticket S1: one physical encounter
  in `RoundEngine.encounter_log` produces exactly **ONE undirected encounter log
  row** and exactly **TWO directed history records** in `HistoryStore` (one per
  receiving side).
  - Record 1: Agent $a$ observing partner $b$ ($a$'s perspective).
  - Record 2: Agent $b$ observing partner $a$ ($b$'s perspective).
  Both records capture: `sample_id`, `round`, `agent`, `partner`, `agent_prediction`
  (at encounter time), `partner_prediction` (at encounter time), `agreement`
  (`agent_prediction == partner_prediction`), `certainty_before`, `certainty_after`,
  `certainty_delta` (`certainty_after - certainty_before`), `prediction_flipped`
  (`agent_prediction != agent_prediction_after`), `partner_correct` (`None` initially),
  and `ground_truth` (`None` initially).
  *Rationale:* Trust is asymmetric: $a$'s history of advice received from $b$
  is independent of $b$'s history of advice received from $a$. Storing directed
  records aligns with §6.5's evaluation of $b_{percCorrect}$.
  *Rejected alternative:* Storing one undirected row with `agent1` and `agent2`
  columns. Rejected because querying $a$'s perspective of $b$ would require
  compound `(agent1 == a AND agent2 == b) OR (agent1 == b AND agent2 == a)`
  filtering and conditional perspective reversal on every query.

- **D3 — Trust Update Equation and Cold-Start / Unscored History Guard.**
  In `ReferenceInteractionPolicy.update_trust(a: Agent, b: Agent) -> None`:
  1. $a$ queries $b_{percCorrect}$ from `HistoryStore`.
  2. If $a$ has **no prior scored history** with $b$ (i.e. 0 encounters between $a$
     and $b$ have ground truth available, or first contact), **no update occurs**
     (spec §6.5: "NO update if $a$ has no prior history with $b$"). `b.trust_score`
     remains untouched.
  3. If scored history exists:
     $$b_{trust} \mathrel{+}= 0.05 \cdot (b_{percCorrect} \cdot b_{priorPerf}) \cdot doAgree$$
     where $doAgree = +1$ if $a$ and $b$ agree at encounter time, $-1$ if they disagree.
  4. Clamp $b_{trust}$ into $[0.0, 1.0]$ using `_util.clamp(b.trust_score, 0.0, 1.0)`.
  *Rationale:* Protects cold-start encounters from uncalibrated trust swings.
  Uses `b.prior_performance` (multiplier in $[0.7, 1.3]$), strictly avoiding
  `prior_accuracy` (rate in $[0, 1]$), satisfying forbidden-shortcut #2 and §10.2.
  *Rejected alternative:* Defaulting $b_{percCorrect} = 0.5$ or $1.0$ on first
  contact. Rejected because spec §6.5 explicitly mandates NO update without
  prior history.

- **D4 — `Encounter` Orchestration and Backward Compatibility.**
  Extend `Encounter`'s constructor in `src/wocbots/interaction/encounter.py`:
  ```python
  class Encounter:
      def __init__(
          self,
          a: Agent,
          b: Agent,
          scoring_policy: ScoringPolicy,
          interaction_policy: InteractionPolicy,
          *,
          history_store: HistoryStore | None = None,
          sample_id: int | str = 0,
          round_num: int = 0,
      ) -> None:
  ```
  In `Encounter.process()`:
  1. Snapshot pre-update public profiles for both agents (`profile_a`, `profile_b`).
  2. Run `scoring_policy.update_prediction(a, profile_b)` and
     `scoring_policy.update_prediction(b, profile_a)` (compute-then-apply).
  3. Run `interaction_policy.update_trust(a, b)` and
     `interaction_policy.update_trust(b, a)` (using encounter-time agreement
     from pre-update snapshots).
  4. If `history_store is not None`, construct and record the two directed
     `HistoryRecord` entries with deltas and flip flags.
  *Rationale:* Keeps `Encounter` as the atomic processor, preserves all W3-03
  guarantees, and maintains full backward compatibility for existing callers and
  tests where `history_store=None`.
  *Rejected alternative:* Creating a separate `EncounterWithHistory` subclass.
  Rejected because history recording is a standard capability of the reference
  encounter execution, not a divergent policy branch; an optional parameter
  avoids redundant class hierarchies.

- **D5 — Back-Fill Hook Semantics.**
  `HistoryStore.backfill_correctness(sample_id: int | str, ground_truth: int) -> int`
  locates all directed records matching `sample_id` and updates:
  - `record.ground_truth = ground_truth`
  - `record.partner_correct = (record.partner_prediction == ground_truth)`
  All other fields (`agent`, `partner`, `round`, `predictions`, `certainty_delta`, etc.)
  remain strictly unmodified.
  *Rationale:* Fulfills the W4-02 contract hook for Phase 4 ground-truth feedback.

- **D6 — Package Layout in `src/wocbots/interaction/`.**
  - `src/wocbots/interaction/history.py` (new): `HistoryRecord`, `HistoryStore`.
  - `src/wocbots/interaction/policy.py` (modified): `ReferenceInteractionPolicy`
    implements §6.5 trust update using `HistoryStore`.
  - `src/wocbots/interaction/encounter.py` (modified): `Encounter` records
    history if `history_store` provided.
  - `src/wocbots/interaction/__init__.py` (modified): export `HistoryRecord`,
    `HistoryStore`, `ReferenceInteractionPolicy`, `CertaintyFlipScoringPolicy`,
    `Encounter`.

---

## 4. Verified Grounding Facts

- **Spec §6.5 Trust Update Formula:** $$b_{trust} \mathrel{+}= 0.05 \cdot
  (b_{percCorrect} \cdot b_{priorPerf}) \cdot doAgree$$
  - $doAgree = +1$ on agreement, $-1$ on disagreement.
  - $b_{percCorrect}$ = fraction of past encounters between $a$ and $b$ where
    $b$'s prediction matched revealed ground truth.
  - $b_{priorPerf} \in [0.7, 1.3]$ (neutral $1.0$ at cold start).
  - Clamp trust to $[0.0, 1.0]$.
  - No update if $a$ has no prior history with $b$.
- **Spec §2 Vocabulary & State:**
  - `trust_score`: initialized to `eval_precision`, modified during interaction
    (§6.5).
  - `prior_performance`: multiplier $[0.7, 1.3]$, initialized to $1.0$.
  - `prior_accuracy`: rate $[0, 1]$, initialized to `eval_accuracy` (used in
    voting, NOT trust).
  - `trust_score`, `prior_performance`, `prior_accuracy`, and `history`
    **persist across samples** (spec §6.6).
- **Cardinality Ruling (2026-07-07 Codex Review):** One encounter in
  `RoundEngine.encounter_log` produces 1 undirected row in the arena log and
  exactly 2 directed rows in `HistoryStore`.
- **Pre-existing Utilities:** `src/wocbots/interaction/_util.py` contains
  `clamp(value, lo, hi)`.

---

## 5. Execution-Path Map(s)

```text
Phase 2/3 (Arena Round Interaction):
  RoundEngine.round() -> encounter_log[round].append(((a, b), cell))
    -> W4-01 / Test harness pulls ((a, b), cell)
    -> Encounter(a, b, scoring_policy, interaction_policy, history_store=store, sample_id=s, round_num=r).process()
         |
         +--> profile_a = a.public_profile()
         +--> profile_b = b.public_profile()
         |
         +--> scoring_policy.update_prediction(a, profile_b)  # updates a.certainty / a.current_prediction
         +--> scoring_policy.update_prediction(b, profile_a)  # updates b.certainty / b.current_prediction
         |
         +--> interaction_policy.update_trust(a, b)
         |      |
         |      +--> perc_correct = history_store.get_perc_correct(a, b)
         |      +--> if perc_correct is None: return (no-op)
         |      +--> do_agree = +1 if profile_a["current_prediction"] == profile_b["current_prediction"] else -1
         |      +--> delta = 0.05 * (perc_correct * b.prior_performance) * do_agree
         |      +--> b.trust_score = clamp(b.trust_score + delta, 0.0, 1.0)
         |
         +--> interaction_policy.update_trust(b, a)
         |      |
         |      +--> perc_correct = history_store.get_perc_correct(b, a)
         |      +--> ... updates a.trust_score ...
         |
         +--> history_store.record(HistoryRecord(a, b, ...))  # directed record a -> b
         +--> history_store.record(HistoryRecord(b, a, ...))  # directed record b -> a

Phase 4 (Ground-Truth Feedback — W4-02):
  Ground truth label y revealed for sample_id s
    -> history_store.backfill_correctness(sample_id=s, ground_truth=y)
         |
         +--> for each record matching sample_id s:
                record.ground_truth = y
                record.partner_correct = (record.partner_prediction == y)
```

---

## 6. Pre-Code Gates

1. Verify check suite is 100% green before touching code: `uv sync && uv run
   ruff check . && uv run ruff format --check . && uv run mypy src tests && uv
   run pytest` (Confirmed: 218 passed, 11 skipped, 1 xfailed; 0 errors).
2. Confirm `src/wocbots/interaction/` contains W3-03 deliverables (`scoring.py`,
   `policy.py`, `encounter.py`, `_util.py`).
3. Re-verify `protocols.py` `InteractionPolicy` Protocol: `should_interact(a, b)
   -> bool`, `truth(a, b) -> bool`, `update_trust(a, b) -> None`.

---

## 7. Specification

### S1 — `src/wocbots/interaction/history.py` (new)

```python
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
            return records
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
            record.partner_correct = (record.partner_prediction == ground_truth)
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
```

### S2 — `src/wocbots/interaction/policy.py` (modified)

```python
"""W3-03 / W3-04 — Reference InteractionPolicy (spec §6.5).

Implements the InteractionPolicy seam: always-willing, always-truthful,
and the spec §6.5 trust update math backed by HistoryStore.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from wocbots.agents import Agent
from wocbots.interaction._util import clamp

if TYPE_CHECKING:
    from wocbots.interaction.history import HistoryStore


class ReferenceInteractionPolicy:
    """Reference InteractionPolicy: always-willing, always-truthful, §6.5 trust updates."""

    def __init__(self, history_store: HistoryStore | None = None) -> None:
        self._history_store = history_store

    def should_interact(self, a: Agent, b: Agent) -> bool:
        return True

    def truth(self, a: Agent, b: Agent) -> bool:
        return True

    def update_trust(
        self,
        a: Agent,
        b: Agent,
        *,
        a_prediction: int | None = None,
        b_prediction: int | None = None,
    ) -> None:
        """Update b's trust score from a's perspective per spec §6.5.

        b_trust += 0.05 * (b_percCorrect * b_priorPerf) * doAgree
        NO update if a has no prior scored history with b.
        Clamped to [0.0, 1.0].
        """
        if self._history_store is None:
            return

        perc_correct = self._history_store.get_perc_correct(a, b)
        if perc_correct is None:
            # Spec §6.5: NO update if a has no prior history with b
            return

        # Encounter-time predictions (fall back to current_prediction if not explicitly supplied)
        pred_a = a.current_prediction if a_prediction is None else a_prediction
        pred_b = b.current_prediction if b_prediction is None else b_prediction

        if pred_a is None or pred_b is None:
            raise ValueError("update_trust called on agents with uninitialized predictions")

        do_agree = 1 if pred_a == pred_b else -1
        delta = 0.05 * (perc_correct * b.prior_performance) * do_agree
        b.trust_score = clamp(b.trust_score + delta, 0.0, 1.0)
```

### S3 — `src/wocbots/interaction/encounter.py` (modified)

```python
"""W3-03 / W3-04 — Atomic per-encounter processor (plan §3 D4).

Consumes one encounter pair (a, b), executes compute-then-apply prediction updates,
evaluates trust updates, and records directed history rows in HistoryStore.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

from wocbots.agents import Agent
from wocbots.interaction.history import HistoryRecord
from wocbots.protocols import InteractionPolicy, ScoringPolicy

if TYPE_CHECKING:
    from wocbots.interaction.history import HistoryStore


class Encounter:
    def __init__(
        self,
        a: Agent,
        b: Agent,
        scoring_policy: ScoringPolicy,
        interaction_policy: InteractionPolicy,
        *,
        history_store: HistoryStore | None = None,
        sample_id: int | str = 0,
        round_num: int = 0,
    ) -> None:
        self._a = a
        self._b = b
        self._scoring_policy = scoring_policy
        self._interaction_policy = interaction_policy
        self._history_store = history_store
        self._sample_id = sample_id
        self._round_num = round_num

    def process(self) -> None:
        """Both directions, compute-then-apply (spec §6.5 symmetry ruling)."""
        profile_a = self._a.public_profile()
        profile_b = self._b.public_profile()

        pred_a_before = cast(Literal[0, 1], profile_a["current_prediction"])
        pred_b_before = cast(Literal[0, 1], profile_b["current_prediction"])
        cert_a_before = cast(float, profile_a["certainty"])
        cert_b_before = cast(float, profile_b["certainty"])

        # 1. Update predictions (compute-then-apply)
        self._scoring_policy.update_prediction(self._a, profile_b)
        self._scoring_policy.update_prediction(self._b, profile_a)

        # 2. Update trust (using encounter-time predictions)
        self._interaction_policy.update_trust(self._a, self._b)
        self._interaction_policy.update_trust(self._b, self._a)

        # 3. Record directed history in HistoryStore if present
        if self._history_store is not None:
            pred_a_after = self._a.current_prediction
            pred_b_after = self._b.current_prediction
            cert_a_after = self._a.certainty
            cert_b_after = self._b.certainty

            rec_a = HistoryRecord(
                sample_id=self._sample_id,
                round_num=self._round_num,
                agent=self._a,
                partner=self._b,
                agent_prediction=pred_a_before,
                partner_prediction=pred_b_before,
                agreement=(pred_a_before == pred_b_before),
                certainty_before=cert_a_before,
                certainty_after=cert_a_after,
                certainty_delta=cert_a_after - cert_a_before,
                prediction_flipped=(pred_a_before != pred_a_after),
            )
            rec_b = HistoryRecord(
                sample_id=self._sample_id,
                round_num=self._round_num,
                agent=self._b,
                partner=self._a,
                agent_prediction=pred_b_before,
                partner_prediction=pred_a_before,
                agreement=(pred_b_before == pred_a_before),
                certainty_before=cert_b_before,
                certainty_after=cert_b_after,
                certainty_delta=cert_b_after - cert_b_before,
                prediction_flipped=(pred_b_before != pred_b_after),
            )
            self._history_store.record(rec_a)
            self._history_store.record(rec_b)
```

### S4 — `src/wocbots/interaction/__init__.py` (modified)

```python
from wocbots.interaction.encounter import Encounter
from wocbots.interaction.history import HistoryRecord, HistoryStore
from wocbots.interaction.policy import ReferenceInteractionPolicy
from wocbots.interaction.scoring import CertaintyFlipScoringPolicy

__all__ = [
    "CertaintyFlipScoringPolicy",
    "ReferenceInteractionPolicy",
    "Encounter",
    "HistoryRecord",
    "HistoryStore",
]
```

---

## 8. Observability

- **Tidy DataFrame serialization:** `HistoryStore.to_dataframe()` returns a
  complete, tabular representation of all encounters with columns:
  `["sample_id", "round", "agent", "partner", "agent_prediction",
  "partner_prediction", "agreement", "certainty_before", "certainty_after",
  "certainty_delta", "prediction_flipped", "partner_correct", "ground_truth"]`.
- **Pure-mechanism ticket:** No stochastic experiment or manifest required. All
  mechanisms verified via deterministic unit test pins.

---

## 9. Sequenced Implementation Steps

1. **Pre-code check:** Run baseline test suite to confirm green state.
2. **Create `src/wocbots/interaction/history.py`:** Implement `HistoryRecord`
   dataclass and `HistoryStore` with indices, query methods, $b_{percCorrect}$
   calculation, backfill hook, and `to_dataframe()`.
3. **Update `src/wocbots/interaction/policy.py`:** Implement the §6.5 trust
   update formula in `ReferenceInteractionPolicy.update_trust()`.
4. **Update `src/wocbots/interaction/encounter.py`:** Wire `history_store`,
   `sample_id`, and `round_num` into `Encounter.process()`.
5. **Update `src/wocbots/interaction/__init__.py`:** Export `HistoryRecord` and
   `HistoryStore`.
6. **Create `tests/unit/test_history_trust.py`:** Implement all pinned tests
   (Tests 1–8 in §10).
7. **Run check suite:** `ruff check .`, `ruff format --check .`, `mypy src
   tests`, `pytest`.
8. **Draft Closing Report:** `tickets/W3-04_history-trust_CLOSING-REPORT.md`.

---

## 10. Test Plan (Exact Pins)

All tests in `tests/unit/test_history_trust.py`:

- **Test 1 — Ticket Req 1: No-history encounter → no trust update.**
  - Fresh agents $a$ and $b$ meet with empty `HistoryStore`.
  - Initial `b.trust_score = 0.78`.
  - `policy.update_trust(a, b)` called.
  - Assert `b.trust_score == 0.78` (exact, no change).
  - Also test when un-scored records exist (current sample, `partner_correct is
    None`): assert `b.trust_score` remains unchanged.

- **Test 2 — Ticket Req 2: Capped movement & clamp boundaries (both signs).**
  - Setup: $a$ has 1 scored encounter with $b$ where $b$ was correct
    ($percCorrect = 1.0$). $b.prior\_performance = 1.0$.
  - 2a: Agreement ($doAgree = +1$): $\Delta trust = 0.05 \times (1.0 \times 1.0)
    \times 1 = +0.05$. Initial $0.50 \to 0.55$. Assert `abs(b.trust_score -
    0.55) < 1e-9`.
  - 2b: Disagreement ($doAgree = -1$): $\Delta trust = -0.05$. Initial $0.50 \to
    0.45$. Assert `abs(b.trust_score - 0.45) < 1e-9`.
  - 2c: Upper clamp saturation: initial $0.98 \to 0.98 + 0.05 = 1.03 \to$
    clamped to $1.0$. Assert `b.trust_score == 1.0`.
  - 2d: Lower clamp saturation: initial $0.02 \to 0.02 - 0.05 = -0.03 \to$
    clamped to $0.0$. Assert `b.trust_score == 0.0`.

- **Test 3 — Ticket Req 3: $percCorrect$ over scripted history (hand-computed
  pin, 1e-9).**
  - Scripted history: $a$ met $b$ in 4 past samples with ground truth:
    1. Sample 0: $b$ predicted 1, label 1 $\to$ correct (1)
    2. Sample 1: $b$ predicted 0, label 1 $\to$ incorrect (0)
    3. Sample 2: $b$ predicted 1, label 1 $\to$ correct (1)
    4. Sample 3: $b$ predicted 0, label 0 $\to$ correct (1)
  - Hand computation: $percCorrect = 3 / 4 = 0.75$.
  - Given $b.prior\_performance = 1.1$, initial $b.trust\_score = 0.50$:
    - $\Delta trust = 0.05 \times (0.75 \times 1.1) \times (+1) = 0.05 \times
      0.825 = 0.04125$.
    - New $b.trust\_score = 0.50 + 0.04125 = 0.54125$.
  - Assert `abs(store.get_perc_correct(a, b) - 0.75) < 1e-9`.
  - Call `policy.update_trust(a, b)`.
  - Assert `abs(b.trust_score - 0.54125) < 1e-9`.

- **Test 4 — Ticket Req 4: Store completeness and cardinality (scripted arena run).**
  - Scripted arena run with 5 agents across 2 rounds producing $K$ encounters.
  - Assert `RoundEngine.encounter_log` contains $K$ entries.
  - Process all encounters with `Encounter(..., history_store=store)`.
  - Assert `len(store) == 2 * K` exactly (cardinality ruling).
  - Assert for every $((a, b), cell)$ encounter in the log,
    `store.get_interactions(agent=a, partner=b)` has 1 record and
    `store.get_interactions(agent=b, partner=a)` has 1 record.

- **Test 5 — Ticket Req 4: Back-fill hook isolation.**
  - Execute encounters for `sample_id=1`.
  - Verify all records for `sample_id=1` have `partner_correct is None` and
    `ground_truth is None`.
  - Call `store.backfill_correctness(sample_id=1, ground_truth=1)`.
  - Assert `partner_correct == (partner_prediction == 1)` for all records.
  - Assert `ground_truth == 1` for all records.
  - Assert no other columns (`sample_id`, `round`, `predictions`,
    `certainty_delta`, `agreement`) were modified.

- **Test 6 — Queryable tidy DataFrame:**
  - Call `df = store.to_dataframe()`.
  - Assert `isinstance(df, pd.DataFrame)`.
  - Assert `len(df) == len(store)`.
  - Assert all mandatory column names exist and have valid types.

- **Test 7 — Separation of `prior_performance` vs `prior_accuracy` (forbidden shortcut guard):**
  - Verify that `update_trust` reads `b.prior_performance` and ignores
    `b.prior_accuracy`.
  - Set `b.prior_performance = 1.2` and `b.prior_accuracy = 0.6`.
  - Hand computation: with $percCorrect = 1.0, doAgree = +1$:
    $\Delta trust = 0.05 \times (1.0 \times 1.2) = 0.06$ (if using
    `prior_accuracy`, it would erroneously be $0.05 \times 0.6 = 0.03$).
  - Assert `abs(b.trust_score - (initial + 0.06)) < 1e-9`.

- **Test 8 — Degenerate & defensive inputs:**
  - `update_trust` called on agent with `current_prediction = None` raises
    `ValueError`.
  - Querying `get_perc_correct` for unknown agent pair returns `None`.

---

## 11. Blast Radius

- **W4-01 (`participant-selection-loop`):** Consumes `HistoryStore` and passes
  it to `Encounter(..., history_store=store, sample_id=s, round_num=r)` in the
  per-sample arena loop.
- **W4-02 (`ground-truth-feedback`):** Calls
  `history_store.backfill_correctness(sample_id, true_label)` when ground truth
  arrives in Phase 4.
- **W4-03 (`voting-aggregators`):** Reads persisted `trust_score` and
  `prior_accuracy` for weighted voting models.
- **W6-01 / W6-02 (`swarm-rounds`, `confidence-ladder`):** Uses trust scores and
  history traces for swarm fitness and ladder validation.

---

## 12. Risks, Alternatives, Open Questions

- **R1 — Unscored History Handling:** If agents interact multiple times within
  the same sample before ground truth is revealed, those within-sample
  interactions have `partner_correct = None`. `get_perc_correct` explicitly
  filters for `partner_correct is not None`, preventing unscored within-sample
  interactions from polluting or dividing-by-zero the historical accuracy rate.
- **R2 — DataFrame Performance:** `to_dataframe()` constructs a list of dicts
  before calling `pd.DataFrame()`. For full experiment sweeps with thousands of
  encounters, this is fast and avoids repeated DataFrame concatenation overhead.

---

## 13. Definition of Done

- [X] `src/wocbots/interaction/history.py` created with `HistoryRecord` and `HistoryStore`.
- [X] `src/wocbots/interaction/policy.py` updated with §6.5 trust update formula.
- [X] `src/wocbots/interaction/encounter.py` updated with history recording.
- [X] `src/wocbots/interaction/__init__.py` exports new classes.
- [X] `tests/unit/test_history_trust.py` created with all 8 tests green.
- [X] Check suite clean: `ruff check .`, `ruff format --check .`, `mypy src tests`, `pytest`.
- [X] Closing report written in `tickets/W3-04_history-trust_CLOSING-REPORT.md`.
