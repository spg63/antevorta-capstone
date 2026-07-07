# W0-02 — Shared types and the five policy seams — IMPLEMENTATION PLAN

> **STATUS: ✅ APPROVED (stakeholder, 2026-07-07) — with review amendments applied.** Authored by Codex
> under the preamble §9 invocation; independently reviewed by Claude (different-AI-system discipline, applied
> at plan stage — the set's first AI→AI plan review). Findings dispositioned 2026-07-07: D2 ruled as an
> explicit AMENDMENT to the wave plan §7-S2 stub rule (constructor-only stubs; the wave plan and its §10.8
> pin were updated to match, same day); §11 gained the tighten-never-loosen line; §10 test 7 reworded from an
> untestable absence-claim to a static pin. Do not implement W0-02 until W0-01 is ✅ (blocked-by).
>
> **About this plan.** This is the per-ticket execution plan for `W0-02_types-policy-seams.md`, following the
> W0 plan skeleton. The current tree has no implementation files yet, so "read all related functions" resolves
> to the full reads of the binding control documents, the W0 wave plan §7-S2, and spec §11/§6.5. There are no
> uflogs to cross-check for this ticket: no results manifests beyond `.gitkeep`, no encounter logs, and no
> swarm traces exist before W0-04.

**Ticket:** `W0-02_types-policy-seams.md`. **Precedence:** spec > this plan > ticket.  
**Wave:** W0. **Blocked by:** W0-01. **Blocks:** W2-01 and W3-01.  
**Binding spec sections:** §11 (policy protocols), §6.5 (public-profile boundary rationale).  
**Binding plan section:** `W0-WAVE_scaffold-experiment-harness_PLAN.md` §7-S2.  
**Binding preamble sections:** §2 (policies are seams), §4 (tests land with feature), §7 (exact vocabulary and
generality), §8 (independent review).
**Severity of getting it wrong:** foundational. These names and signatures become the contracts consumed by
the agent, arena, interaction, aggregation, and meta-swarm tickets.

---

## 1. Metadata

This plan is self-contained for W0-02. It assumes W0-01 has already created the package skeleton, `pyproject`,
lockfile, pytest/mypy/ruff configuration, and importable empty package directories. If W0-01 has not landed,
implementation stops before any code edit.

Current live-tree check at plan time: only `.gitkeep` placeholders exist under `src/` and `tests/`; no
`pyproject.toml`, no package `__init__.py`, no tests, and no implementation modules are present.

---

## 2. Why This Ticket Exists

W0-02 creates the narrow contracts that later tickets grow into instead of refactoring apart. The method's
extensibility claims depend on these seams staying small: initialization, movement, interaction/trust,
scoring, and aggregation must be swappable without exposing private internals or dataset-specific details.

The highest-risk boundary is `ScoringPolicy.update_prediction`: it receives a read-only partner profile, not
an `Agent`. That preserves spec §6.5's privacy boundary and keeps W8-03's external-agent audit possible.

---

## 3. Decisions Made by This Plan

- **D1 - Import strategy for protocols.** Use `from __future__ import annotations` plus `TYPE_CHECKING`
  imports for `Agent` and `Arena`. This preserves the exact public signatures while avoiding runtime circular
  imports as W2-01 and W3-01 replace stub internals.
- **D2 - Stub surface.** `Agent` and `Arena` are constructor-only stubs in this ticket. Their `__init__`
  raises `NotImplementedError("W2-01 owns Agent")` and `NotImplementedError("W3-01 owns Arena")`,
  respectively. No speculative methods such as `public_profile`, `place`, `move`, or state fields land here.
  **Ruled as an AMENDMENT to the wave plan §7-S2 stub rule (review, 2026-07-07):** the wave plan's "every
  method body raises" wording is superseded by constructor-only; the wave plan text and its §10.8 pin were
  updated to match. (Process note: this plan originally framed the deviation as a free choice — binding-doc
  deviations must be flagged as amendments, per the review disposition.)
- **D3 - `Prediction.margin` validation.** W0-02 does not range-check `margin`. The field exists to carry
  later vote-margin or swarm-band output; W4-04/W6-02 own the semantics and boundary tests.
- **D4 - Protocol return shape.** `Aggregator.aggregate` returns `Prediction`, matching spec §11 and the W0
  wave plan. It does not return raw tuples or method-specific result objects.

D1/D3/D4 needed no ruling; D2 was ruled at review (above).

---

## 4. Verified Grounding Facts

- Spec §11 lists the five policy seams: `InitPolicy.place`, `MovementPolicy.move`,
  `InteractionPolicy.should_interact`, `InteractionPolicy.truth`, `InteractionPolicy.update_trust`,
  `ScoringPolicy.update_prediction`, and `Aggregator.aggregate`.
- Spec §6.5 says partner reads must go through a public profile containing only `current_prediction`,
  `certainty`, `confidence`, `trust_score`, `prior_performance`, and features. Private classifier internals,
  raw data, and full history must not be exposed.
- The W0 wave plan §7-S2 pins `Cell`, `Prediction`, the five `@runtime_checkable` protocols, and the stub
  rule as W0-02's entire scope.
- The ticket forbids typing `partner_profile` as `Agent` and forbids speculative future fields or methods.
- W0-02 is pure interface code. It produces no results manifest, encounter log, or swarm trace.

---

## 5. Execution-Path Map

There is no runtime experiment path in this ticket. The contract path is:

```text
later ticket config/runtime code
  -> chooses a concrete policy implementation
  -> type-checks against one of W0-02's Protocols
  -> calls only the small seam method
  -> receives or mutates only the data permitted by that seam
```

Specific downstream binding paths:

```text
W3-01 random arena initialization -> InitPolicy.place(agent, arena, rng) -> Cell
W3-02 movement rounds             -> MovementPolicy.move(agent, arena, rng) -> Cell
W3-03 certainty update            -> ScoringPolicy.update_prediction(agent, partner_profile)
W3-04 trust update                -> InteractionPolicy.update_trust(a, b)
W4-03 voting / W6-02 swarm        -> Aggregator.aggregate(participants, rng) -> Prediction
```

The privacy path is:

```text
Agent.public_profile() (W2-01)
  -> read-only Mapping[str, object]
  -> ScoringPolicy.update_prediction(...)
  -> no access to classifier, raw training data, or full history
```

---

## 6. Pre-Code Gates

1. Confirm W0-01 is ✅ in `tickets/00_INDEX.md` with independent review sign-off.
2. Confirm W0-01 artifacts exist: `pyproject.toml`, `uv.lock`, importable package directories, `pytest`
   configuration, and the check-suite commands.
3. Confirm the W0 wave STEP-0 RESULT block has O1-O6 filled, because the wave plan marks it as shared.
4. Re-read this ticket, this plan, spec §11, spec §6.5, and `W0-WAVE_scaffold-experiment-harness_PLAN.md`
   §7-S2 before editing.
5. If W0-01 changed package layout, mypy strictness, pydantic choice, or test paths in a way that conflicts
   with this plan, stop and update this plan for approval before implementation.

---

## 7. Specification

### S1 - `src/wocbots/types.py`

Exact contents, modulo imports and docstrings:

```python
from typing import Literal

from pydantic import BaseModel

Cell = tuple[int, int]


class Prediction(BaseModel, frozen=True, extra="forbid"):
    class_label: Literal[0, 1]
    tier: str | None = None
    margin: float | None = None
```

Notes:
- `Cell` is a coordinate primitive only: `(row, col)`.
- `Prediction` is deliberately generic. No dataset names, method names, or confidence-tier enum lands here.
- `tier` and `margin` remain optional until W4-04/W6-02 fills them.

### S2 - `src/wocbots/protocols.py`

Exact contract, using forward references for `Agent` and `Arena`:

```python
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import numpy as np

from wocbots.types import Cell, Prediction

if TYPE_CHECKING:
    from wocbots.agents import Agent
    from wocbots.arena import Arena


@runtime_checkable
class InitPolicy(Protocol):
    def place(self, agent: Agent, arena: Arena, rng: np.random.Generator) -> Cell: ...


@runtime_checkable
class MovementPolicy(Protocol):
    def move(self, agent: Agent, arena: Arena, rng: np.random.Generator) -> Cell: ...


@runtime_checkable
class InteractionPolicy(Protocol):
    def should_interact(self, a: Agent, b: Agent) -> bool: ...
    def truth(self, a: Agent, b: Agent) -> bool: ...
    def update_trust(self, a: Agent, b: Agent) -> None: ...


@runtime_checkable
class ScoringPolicy(Protocol):
    def update_prediction(self, agent: Agent, partner_profile: Mapping[str, object]) -> None: ...


@runtime_checkable
class Aggregator(Protocol):
    def aggregate(self, participants: Sequence[Agent], rng: np.random.Generator) -> Prediction: ...
```

Docstrings cite the owning spec sections and downstream tickets:
- `InitPolicy`: spec §6.2, W3-01.
- `MovementPolicy`: spec §6.3, W3-02.
- `InteractionPolicy`: spec §6.5, W3-04.
- `ScoringPolicy`: spec §6.5, W3-03, and the public-profile privacy boundary.
- `Aggregator`: spec §7/§8, W4-03/W6-02.

### S3 - `src/wocbots/agents/__init__.py`

```python
class Agent:
    """Placeholder Agent shell. W2-01 owns Agent state and behavior."""

    def __init__(self) -> None:
        raise NotImplementedError("W2-01 owns Agent")
```

No fields, methods, classifier handles, public-profile method, or state names land in W0-02. W2-01 replaces
the internals and may tighten types without renaming W0-02 seams.

### S4 - `src/wocbots/arena/__init__.py`

```python
class Arena:
    """Placeholder Arena shell. W3-01 owns Arena geometry and behavior."""

    def __init__(self) -> None:
        raise NotImplementedError("W3-01 owns Arena")
```

No geometry, occupancy, movement, or encounter logic lands in W0-02.

---

## 8. Observability

W0-02 has no runtime observability artifact. Its observability is structural:
- tests prove the public contracts exist and reject invalid data;
- mypy strict proves downstream fakes can bind to the protocols;
- the close report states no manifest is expected because no experiment runs.

No logs, manifests, traces, or debug hooks are added in this ticket.

---

## 9. Sequenced Implementation Steps

1. Run pre-code gates in §6.
2. Add `src/wocbots/types.py`.
3. Add `src/wocbots/protocols.py` with protocol docstrings and forward-reference import strategy.
4. Replace `src/wocbots/agents/__init__.py` contents with the `Agent` stub.
5. Replace `src/wocbots/arena/__init__.py` contents with the `Arena` stub.
6. Add `tests/unit/test_types_policy_seams.py`.
7. Run targeted tests: `pytest tests/unit/test_types_policy_seams.py`.
8. Run full check suite: `ruff check .`, `ruff format --check .`, `mypy src tests`, `pytest`.
9. If checks fail because W0-01 tooling differs from this plan, stop and report the drift rather than
   changing contracts opportunistically.
10. Close per preamble §6 only after independent review: no manifest expected, touched paths listed,
    `AGENT_HANDOFF.md` updated, and `00_INDEX.md` flipped only with reviewer identity/date.

---

## 10. Test Plan

All tests live in `tests/unit/test_types_policy_seams.py`.

1. **Prediction accepts valid labels.** Construct `Prediction(class_label=0)` and
   `Prediction(class_label=1)`. Assert fields are preserved and optional fields default to `None`.
2. **Prediction rejects invalid labels.** `Prediction(class_label=2)` raises pydantic validation error.
3. **Prediction rejects unknown keys.** `Prediction(class_label=1, extra_field="x")` raises pydantic
   validation error, proving `extra="forbid"`.
4. **Prediction is frozen.** Assigning to `prediction.class_label` is rejected by pydantic frozen-model
   enforcement.
5. **Runtime protocol conformance.** Define one trivial fake class per seam and assert:
   - `isinstance(fake_init, InitPolicy)`
   - `isinstance(fake_move, MovementPolicy)`
   - `isinstance(fake_interaction, InteractionPolicy)`
   - `isinstance(fake_scoring, ScoringPolicy)`
   - `isinstance(fake_aggregator, Aggregator)`
6. **Static protocol conformance.** In the same test module, assign each fake to a variable typed as its
   protocol so `mypy src tests` checks method signatures, not just runtime attribute presence.
7. **Profile boundary (statically enforced).** The scoring fake's signature is
   `partner_profile: Mapping[str, object]` and it is assigned to a `ScoringPolicy`-typed variable — mypy
   strict enforces the boundary. (Reworded at review: a runtime test cannot prove an absence; the static
   check is the pin.)
8. **Aggregator returns Prediction.** The aggregator fake returns `Prediction(class_label=1)`, proving the
   protocol shape and the shared return model.
9. **Agent stub ownership.** `Agent()` raises `NotImplementedError` and the message contains `W2-01 owns
   Agent`.
10. **Arena stub ownership.** `Arena()` raises `NotImplementedError` and the message contains `W3-01 owns
    Arena`.

No slow tests and no fixtures requiring data are added.

---

## 11. Blast Radius

- W2-01 consumes `Agent` and may replace internals, but must preserve the public seam names unless an
  index-logged contract change is approved.
- W2-01/W3-01 may TIGHTEN protocol parameter types when replacing stub internals; renaming a seam or
  LOOSENING a type is an index-logged cross-ticket contract change (the wave plan §7-S2 rule — added at
  review).
- W3-01 consumes `Arena` and `InitPolicy`.
- W3-02 consumes `MovementPolicy`.
- W3-03 consumes `ScoringPolicy` and relies on `partner_profile: Mapping[str, object]`.
- W3-04 consumes `InteractionPolicy`.
- W4-03 and W6-02 consume `Aggregator` and `Prediction`.
- W8-03 depends on the profile boundary staying narrow for the external-agent privacy audit.

Changing any W0-02 protocol name, parameter order, or return type after landing is a cross-ticket contract
change.

---

## 12. Risks, Alternatives, Open Items

**Risks**
- **R1 - Circular imports as stubs become real classes.** Mitigated by `TYPE_CHECKING` imports and postponed
  annotations in `protocols.py`.
- **R2 - Runtime-checkable protocols give false confidence.** Mitigated by combining `isinstance` tests with
  typed fake assignments that mypy checks.
- **R3 - Premature abstraction growth.** Mitigated by landing only the five spec seams and no optional fields
  beyond the pinned `Prediction` model.
- **R4 - Stub behavior becoming accidental API.** Mitigated by constructor-only stubs that fail loudly and
  name the owning tickets.

**Alternatives Rejected**
- Typing `partner_profile` as `Agent`: rejected because it violates spec §6.5's privacy boundary.
- Adding `PublicProfile` as a model now: rejected because W2-01 owns agent state/profile construction and the
  W0 plan pins `Mapping[str, object]`.
- Adding enums for `tier`: rejected because W4-04/W6-02 own confidence tiers and swarm bands.
- Adding concrete no-op policies: rejected because W3/W4/W6 own policy behavior.

**Open Items**
- None for W0-02 itself. The only blocker is W0-01 completion.

---

## 13. Definition of Done

1. ☐ W0-01 is ✅ before implementation starts.
2. ☐ `Cell`, `Prediction`, all five protocols, `Agent` stub, and `Arena` stub exist exactly as specified.
3. ☐ Tests in §10 land in the same change set.
4. ☐ `ruff check .` passes.
5. ☐ `ruff format --check .` passes.
6. ☐ `mypy src tests` passes.
7. ☐ `pytest` passes.
8. ☐ No results manifest is claimed or expected for this pure interface ticket.
9. ☐ Touched paths are listed in close report.
10. ☐ Independent review signs off and `tickets/00_INDEX.md` is flipped with
    `✅ (reviewed: <who/what>, <date>)`.
11. ☐ `AGENT_HANDOFF.md` is updated with the new CURRENT STATE.
