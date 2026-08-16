# W3-03 — The interaction kernel: certainty update and prediction flip - IMPLEMENTATION PLAN

> **STATUS: DRAFT**
>
> **About this plan.** This is the per-ticket execution plan for
> `W3-03_certainty-update-flip.md`, following the W3 plan skeleton
> (`WX-YY_template_PLAN.md`), mirroring `W3-02_movement-rounds_PLAN.md`'s
> conventions (Decisions with rejected alternatives, execution-path maps,
> exact-pin test plans).

**Ticket:** [`W3-03_certainty-update-flip.md`](./W3-03_certainty-update-flip.md)

**Precedence:** the spec > this plan > the ticket.

**Wave:** W3

**Blocked by:** W2-01, W3-02

**Blocks:** W3-04, W4-01, W6-02

**Binding spec sections:** [§6.5 The interaction (certainty & trust
updates)](../docs/WoC-Bots_Implementation_Spec.md#65-the-interaction-certainty--trust-updates)
(in full — equations, worked example, clamp ruling, compute-then-apply
symmetry ruling), §10 pitfall 1 (the ticket's "§10.1" — certainty explosion /
the clamp ruling; the spec has no numbered `### 10.1` heading, §10 is a
flat numbered pitfalls list and item 1 is the clamp pitfall — confirmed by
reading the section, see §4 below).

**Binding preamble sections:** `01_MANDATORY_PREAMBLE.md` applies in full.

**Severity of getting it wrong:** high. This is the single most
consequences-per-line piece of math in the project (ticket's own words) —
every later wave (W3-04 trust, W4-01 the full loop, W6-02 confidence ladder,
all §9.2 reference-number reproductions) sits downstream of this exact
arithmetic. A sign error, a wrong clamp bound, or an order-dependent
side-effect here is silent and compounds invisibly across an entire arena
run.

**Ruling authority:** stakeholder (spg63) for anything this plan flags as
open; independent reviewer (preamble §8) for the close.

---

## 1. Metadata

Re-read this session, in full, before writing this plan: `01_MANDATORY_PREAMBLE.md`;
`tickets/00_INDEX.md` (current statuses, blocked-by/blocks for W2-01/W3-02/W3-03/W3-04/W4-01);
`tickets/W3-03_certainty-update-flip.md`; spec §2 (state table), §6.1–§6.7 (arena +
interaction, read in full for context even though only §6.5 and pitfall-1 are
binding), §3 (lifecycle, for where this ticket sits), §10 (all ten pitfalls);
`src/wocbots/protocols.py`, `src/wocbots/types.py` (locked seams — read in
full, not summarized); `src/wocbots/agents/agent.py` (the actual landed
`Agent` class and `public_profile()` — W2-01); `src/wocbots/arena/arena.py`,
`movement_policy.py`, `round_engine.py` (the actual landed W3-02 code, not
its plan's description of intended behavior); `tickets/W3-02_movement-rounds_PLAN.md`
and its `_CLOSING-REPORT.md`; `tickets/WX-YY_template_PLAN.md`;
`tickets/W3-04_history-trust.md` and `tickets/W4-01_participant-selection-loop.md`
(read to scope W3-03's boundary correctly — see §3 D2 below); `AGENT_HANDOFF.md`
(current + relevant PRIOR entries); `pyproject.toml` (mypy strict, ruff
config); `tests/unit/test_w2_01_agent_state.py`, `test_round_engine.py`
(existing test conventions — local `make_agent()` helpers, no shared
conftest). Self-contained: an implementer following §9 and pinning §10 ships
the ticket without inventing a convention this plan didn't name.

---

## 2. Why this ticket exists (system meaning)

The social mechanism's kernel — how evidence held by well-trained,
confident agents propagates through the crowd and flips weaker opinions.
Every quantity in §6.5 is specified exactly, down to a hand-worked example
with 8-decimal precision; the job here is faithful, pinned implementation,
not interpretation. It is isolated in its own ticket, separate from trust
(W3-04) and the per-sample loop (W4-01), because it is the highest
consequences-per-line piece of math in the project — one clamp bound, one
negation, or one profile-read-after-mutation bug here silently distorts
every later wave that consumes it.

---

## 3. Decisions

- **D1 — Scope boundary: process ONE encounter, not the encounter-log
  iteration loop.** The ticket's S3 says the kernel "consumes W3-02's
  encounter log entries" — i.e. `RoundEngine.encounter_log`'s shape,
  `dict[int, list[tuple[tuple[Agent, Agent], Cell]]]`, is this ticket's
  actual input contract, and the mandatory-pin test 5 ("swap encounter
  processing order → byte-identical outcomes") requires exercising the
  *processing of one encounter tuple*, both directions, symmetrically.
  What this ticket does **not** own: iterating `RoundEngine.encounter_log`
  round-by-round to drive a whole arena period. That loop is chartered to
  W4-01 (`tickets/W4-01_participant-selection-loop.md` S2: "W3 arena +
  interactions" lives in its per-sample loop), and W3-04 needs to inject a
  history-store write into the same per-encounter step without touching the
  certainty math (`W3-04` S1: "one encounter... exactly TWO directed history
  rows"). So this ticket's deliverable is the **atomic per-encounter
  processor** — a single function that takes one `(Agent, Agent)` pair (one
  entry from one round's encounter-log list) and applies both directions —
  not a round-log walker. W4-01's loop will call this once per
  `(a, b), cell` tuple it pulls out of `encounter_log[round]`; W3-04 extends
  it (or wraps it) to also write history rows and swap in the real
  `update_trust`. Rejected alternative: build a `process_round(encounter_log[round], ...)`
  helper here too — rejected because it would (a) presuppose how W4-01
  wants to drive rounds (it might interleave per-sample bookkeeping between
  encounters that this ticket has no visibility into), and (b) give W3-04 a
  wider surface to either duplicate or awkwardly wrap. The single-encounter
  function is the smallest unit that satisfies every S1–S3 requirement and
  every test in §34.

- **D2 — File layout inside `src/wocbots/interaction/`** (currently empty
  except `__init__.py`'s placeholder docstring — verified by reading it).
  Three new files, mirroring the arena package's one-class-per-file
  convention (`movement_policy.py`, `round_engine.py`):
  - `src/wocbots/interaction/scoring.py` — `CertaintyFlipScoringPolicy`
    (the `ScoringPolicy` seam impl; §6.5's receiving-side equations).
  - `src/wocbots/interaction/policy.py` — `ReferenceInteractionPolicy` (the
    `InteractionPolicy` seam impl; always-willing/always-truthful reference
    behavior; `update_trust` a no-op stub per ticket S3 — W3-04 replaces the
    body, not the class or its call sites).
  - `src/wocbots/interaction/encounter.py` — `process_encounter()`, the D1
    atomic processor gluing the two policies together for one encounter.
  - `src/wocbots/interaction/_util.py` — a private `clamp(value, lo, hi)`
    helper. Genuine MAY-choice (documented per preamble §0.2): the spec
    names a clamp ruling but not where the helper lives. Rejected
    alternative: inline `max(lo, min(hi, x))` at each of the two call sites
    in `scoring.py` — rejected because W3-04 needs the *same* clamp shape
    for trust ([0, 1], spec §6.5's trust paragraph) and duplicating a
    two-line function across two tickets is exactly the kind of drift the
    preamble's "policies are seams" principle warns about; a shared private
    helper costs nothing now and saves W3-04 a decision later. Leading
    underscore signals "internal to the package, not part of any locked
    seam" — never exported in `__all__`.
  - `src/wocbots/interaction/__init__.py` — updated from its current
    one-line placeholder docstring to export `CertaintyFlipScoringPolicy`,
    `ReferenceInteractionPolicy`, `process_encounter`, matching the
    `arena/__init__.py` pattern (`from wocbots.arena.arena import ...` +
    explicit `__all__` — verified by reading that file).

- **D3 — `partner_profile: Mapping[str, object]` is read defensively, not
  trusted.** `protocols.py`'s `ScoringPolicy.update_prediction` types the
  partner argument as `Mapping[str, object]` specifically so a scoring
  policy can never widen it back to `Agent` (verified by reading the
  docstring on that Protocol — "Typing it as `Agent` is the exact hole the
  boundary closes"). Under mypy strict this means every field pulled out of
  `partner_profile` is statically `object` and must be narrowed before use.
  Two small private extractors in `scoring.py`:
  - `_require_float(profile, key) -> float` — `isinstance` check
    (excluding `bool`, since `bool` is an `int` subclass and every §6.5
    field here is a genuine float/rate), raises `TypeError` naming the key
    on mismatch.
  - `_require_prediction(profile, key) -> Literal[0, 1]` — checks
    `value in (0, 1)`, raises `ValueError` naming the key on mismatch, then
    `typing.cast(Literal[0, 1], value)` (the check makes the cast true;
    `cast` is the correct tool here, not a bare `# type: ignore`, since
    nothing is actually being silenced — mypy just can't follow the runtime
    `in` check).
  This also gives the ticket's "degenerate input" test discipline
  requirement (preamble §4-(c)) a natural home: a malformed or missing-key
  profile is a real caller bug (e.g. an encounter fed a partner that never
  ran Phase-2 inference) and should fail loudly, not silently propagate a
  `None` into arithmetic. Rejected alternative: trust the `Mapping` and let
  a bad value surface as a `TypeError: unsupported operand` deep inside the
  arithmetic — rejected, because that failure would point at the wrong
  line and give a future debugger no idea which field or which agent was
  malformed.

- **D4 — `agent.current_prediction: Literal[0, 1] | None` is asserted
  non-`None` at the top of `update_prediction`, not defended against
  silently.** W2-01's docstring on `Agent` states the invariant directly:
  "Never `None` during an arena round." A `None` here means a caller
  invoked the kernel outside Phase 2/3 (spec §3) — i.e. before that
  agent's classifier ran for this sample. Raise `ValueError` naming the
  agent's identity is not useful (no name field), so the message names the
  violated invariant instead. This single `if agent.current_prediction is
  None: raise ...` at the top also gives mypy's narrowing what it needs:
  every subsequent read of `agent.current_prediction` in the function body
  is statically `Literal[0, 1]`, so the flip line (`agent.current_prediction
  = 1 - agent.current_prediction`) type-checks under strict mode without a
  cast. (Verified this narrowing pattern is uncomplicated here: no
  intervening call that could reassign the attribute sits between the
  guard and its uses within the function body.)

- **D5 — Symmetry is a call-order-independence property of the CALLER
  (`process_encounter`), not of `update_prediction` itself.** §6.5's
  compute-then-apply ruling ("using $a$'s pre-update state... compute both
  deltas, then apply") is satisfied by capturing **both** `public_profile()`
  snapshots before calling `update_prediction` in either direction:
  ```python
  profile_a = a.public_profile()
  profile_b = b.public_profile()
  scoring_policy.update_prediction(a, profile_b)
  scoring_policy.update_prediction(b, profile_a)
  ```
  Because each call only reads its passed-in (already-frozen) profile
  argument and only ever mutates its own `agent` argument, swapping the two
  `update_prediction` call lines produces byte-identical results — this is
  what test 5 (§10 below) actually pins. Rejected alternative: have
  `update_prediction` itself call `partner.public_profile()` internally
  given a live `Agent` reference — rejected on two independent grounds: (a)
  it re-widens the exact `Agent`-vs-`Mapping` hole `protocols.py`'s
  docstring says the typed seam closes; (b) it reintroduces the forbidden
  "sequential-apply" bug by construction — whichever direction runs second
  would read the FIRST direction's already-mutated certainty.

---

## 4. Verified grounding facts (re-verify before coding)

- **§6.5, receiving side** (spec, quoted structure, re-derived not
  paraphrased from memory):
  ```
  acceptance  = 1.0 - a.certainty
  influence   = b.confidence * acceptance * (b.trust_score * b.certainty)
  corrected   = influence * b.prior_performance
  if a.current_prediction != b.current_prediction: corrected = -corrected
  a.certainty = clamp(a.certainty + corrected, 0.01, 0.99)
  if a.certainty < 0.50:
      a.current_prediction = 1 - a.current_prediction
      a.certainty = 1.0 - a.certainty
  ```
  Six public-profile fields read from the partner: `current_prediction`,
  `certainty`, `confidence`, `trust_score`, `prior_performance`, `features`
  (this ticket doesn't touch `features`). Confirmed identical to
  `Agent.public_profile()`'s six keys — no drift between the spec's list
  and the actually-landed `_PROFILE_FIELDS` tuple in `agent.py`.
- **§6.5 worked example**, hand-recomputed independently (not copied from
  the ticket) to confirm the ticket's pin is faithful to the spec, not just
  internally self-consistent: a(cert 0.62, pred 1) meets b(pred 0, conf
  0.71, trust 0.78, cert 0.80, priorPerf 1.1). acceptance = 1 − 0.62 = 0.38.
  influence = 0.71 × 0.38 × (0.78 × 0.80) = 0.71 × 0.38 × 0.624 =
  0.1683552. corrected = 0.1683552 × 1.1 = 0.18519072; negated (predictions
  differ, 1 ≠ 0) → −0.18519072. a.certainty = 0.62 − 0.18519072 =
  0.43480928, within [0.01, 0.99] (clamp is a no-op here), < 0.50 → flips:
  current_prediction = 1 − 1 = 0, certainty = 1 − 0.43480928 = 0.56519072.
  **Matches the ticket's stated pin exactly** (corrected = −0.18519072,
  final certainty = 0.56519072). No drift found between ticket and spec on
  this example.
- **§6.5 clamp ruling**, read in full: `[0.01, 0.99]`, added specifically so
  (a) certainty can't escape `[0, 1]` after an agreement streak and (b)
  `acceptance` (`1 − certainty`) never hits exactly 0, so an agent never
  goes fully deaf. This is spec-labeled pitfall #1 in §10 ("Certainty
  explosion... If the arena phase never changes any opinion, check this
  first") — this is what the ticket's "§10.1" citation refers to; the spec
  has no `### 10.1` sub-heading, §10 is a flat ten-item numbered list under
  one `## 10.` heading, confirmed by grepping the file for section markers
  before writing this plan. **Flagging, not silently reconciling** per
  preamble §0.2: this is the ticket's numbering being loose, not a
  ticket/spec conflict — the content referenced is unambiguous (the clamp
  pitfall), so nothing here escalates to the stakeholder; noted for the
  record only.
- **§6.5 compute-then-apply ruling**, read in full: "using $a$'s pre-update
  state for symmetry — compute both deltas, then apply; or accept the tiny
  asymmetry and document it. Reference behavior: compute-then-apply is
  cleaner; pick one." The spec itself presents this as a MAY with a stated
  reference preference. **This plan picks compute-then-apply** — the ticket
  text ("COMPUTE-THEN-APPLY (both deltas from pre-update state)") already
  makes this a MUST at the ticket level, consistent with the spec's stated
  reference behavior, so there's no discrepancy to report; just a
  documented choice (D5) implementing the spec's own preferred branch of a
  MAY.
- **Trust update math and the history MUST**, read in full: explicitly out
  of scope here — the ticket's S3 says "Trust updating is a no-op stub here
  — W3-04 owns it," and W3-04's own ticket (S2) confirms it "Replaces
  W3-03's no-op stub in `InteractionPolicy.update_trust`." Confirmed the
  `InteractionPolicy` Protocol signature this ticket must satisfy:
  `should_interact(self, a: Agent, b: Agent) -> bool`, `truth(self, a:
  Agent, b: Agent) -> bool`, `update_trust(self, a: Agent, b: Agent) ->
  None` — read directly from `protocols.py`, not assumed.
- **`ScoringPolicy` Protocol signature**, read directly from
  `protocols.py`: `update_prediction(self, agent: Agent, partner_profile:
  Mapping[str, object]) -> None`. This is a **locked contract** — W3-03
  implements against it, does not redeclare or widen it.
- **`Agent.public_profile()`**, read directly from `agent.py`: returns a
  `MappingProxyType` snapshot of exactly six fields (list above), fresh on
  every call (not cached) — confirms `process_encounter` capturing two
  snapshots up front (D5) is both correct and necessary; calling
  `public_profile()` again after a mutation would return the *mutated*
  state, silently breaking compute-then-apply if the orchestration called
  it lazily instead.
- **`Agent.current_prediction: Literal[0, 1] | None`**, read directly from
  `agent.py`: `None` until Phase-2 inference sets it (W2-01 scope); the
  class docstring states "Never `None` during an arena round" as the
  caller-side invariant this ticket's kernel sits inside, not something
  this ticket enforces upstream — hence D4's defensive raise rather than
  silent coercion.
- **`RoundEngine.encounter_log` shape**, read directly from
  `round_engine.py` (the landed W3-02 code, not its plan's prose
  description): `dict[int, list[tuple[tuple[Agent, Agent], Cell]]]` — round
  number → list of `((mover, other), cell)` tuples, one entry per encounter
  *first-detected-this-round* (confirmed via `round()`: the log entry is
  appended right after `arena.move_to()` when the destination cell now
  holds 2 occupants; the stationary partner is **not** guaranteed to still
  share that cell by the time the round finishes, since `RoundEngine`
  calls `movement_policy.move()` for every agent every round, including one
  that was just "the other" in an encounter a few iterations earlier in the
  same round — so **the encounter-log entry, not later arena state, is the
  only authoritative record of who met whom this round**). This confirms
  D1's framing is correct: a consumer (W4-01) must process each
  `((a, b), cell)` tuple *as it's produced or shortly after*, using exactly
  the pair recorded in the log, not by re-querying the arena.
- **Movement policy's own `_encounter()` bookkeeping** (in
  `movement_policy.py`) is a **separate, unrelated mechanism** — it's the
  anti-clique pair-history the movement policy uses to decide legal moves,
  keyed by `frozenset[Agent]`, nothing to do with certainty/trust. Verified
  by reading it so as not to confuse it with anything this ticket owns.
- **`Agent` hashability**: `Agent` has no `__eq__`/`__hash__` override
  (confirmed by reading `agent.py` in full), so it hashes/compares by
  identity — already relied on by `Arena._agents_cell: dict[Agent, Cell]`
  and the movement policy's `frozenset[Agent]` pair keys. This ticket does
  not need `Agent` to be hashable, but confirms it's safe to hold live
  `Agent` references in test fixtures and dict/set structures if needed.
- **mypy strict, no relaxations** (`pyproject.toml`, `[tool.mypy] strict =
  true`, no per-module override touches `wocbots.interaction`), confirming
  D3/D4's defensive-narrowing approach is required, not optional style.
- **PR #24 / W3-02 review status — checked live per the person's
  instruction, not trusted from their message.** The zip's git history
  (branch `ticket/w3-03`, checked out from a snapshot dated 2026-08-10) shows
  commit `4bb6804` — `Merge pull request #24 from spg63/ticket/w3-02`,
  authored by `Rutu <rootwij@...>` — as an ancestor of `develop`, confirmed
  via `git merge-base --is-ancestor`. `rootwij` is a different person from
  the implementer recorded in `AGENT_HANDOFF.md` (Samuel Gauthier) and is
  the same person who reviewed W3-01 (`00_INDEX.md` row: "✅ (reviewed:
  @rootwij, 2026-08-01)"), so the merge is plausibly by an independent
  party per preamble §8's definition. **However:** I could not reach GitHub
  directly (this tool's web-fetch only allows URLs already surfaced by a
  prior search, and a targeted search for the PR didn't return the actual
  GitHub page — likely a private repo not indexed) — so "PR #24 is
  reviewed" is confirmed only via the merge itself and the merger's
  identity, not via an explicit approval/review record on the PR. More
  importantly: **`tickets/00_INDEX.md` and `AGENT_HANDOFF.md`, as they
  exist right now in this tree, are stale on this point** — I diffed the
  merge commit's parents and the index still reads `W3-02 | ... | W3-01 —
  **◐ implemented, pending independent review**` (no `✅ (reviewed: ...,
  date)` line), and `AGENT_HANDOFF.md`'s CURRENT STATE header is still
  dated 2026-08-07 with "In flight / blocked: W3-02 awaiting independent
  review sign-off... before W3-03/W4-01 can treat it as landed." Neither
  file was updated as part of merging PR #24. This is the **exact failure
  mode `AGENT_HANDOFF.md`'s own 2026-08-01 PRIOR entry names** ("Reviewer
  didn't update `00_INDEX.md` nor pull request checklist nor PLAN's DoD")
  recurring on W3-02. **Conclusion for this plan:** the code W3-03 depends
  on (`RandomMovementPolicy`, `RoundEngine.encounter_log`) is merged to
  `develop` and its shape is stable enough to build against — the person's
  framing that this mirrors W3-02 starting before W3-01's review fully
  landed is accurate. But two bookkeeping items are **owed, independent of
  W3-03's own work**, and are named here rather than fixed silently: (1)
  `00_INDEX.md`'s W3-02 row should be flipped to `✅ (reviewed: @rootwij,
  <merge date>)` — I did not make this edit; it is not this ticket's diff
  to carry, and per preamble §6-item 4 it belongs to W3-02's own close; (2)
  `AGENT_HANDOFF.md`'s CURRENT STATE is stale and should be refreshed
  before or alongside opening the W3-03 PR, so the next session (or
  reviewer) isn't reading a state that already contradicts `git log`. **Risk
  carried forward into §12**, and named explicitly in Decision-adjacent
  form here since it's a fact-finding result, not a judgment call this plan
  is making.

---

## 5. Execution-path map(s)

Per-encounter processing (this ticket's actual deliverable):

```text
RoundEngine.round() appends ((a, b), cell) to encounter_log[round]
  -> (W4-01's loop, not this ticket) pulls one ((a, b), cell) tuple
  -> Encounter(a, b, scoring_policy, interaction_policy).process():
       profile_a = self._a.public_profile()  # frozen six-field snapshot
       profile_b = self._b.public_profile()  # frozen six-field snapshot,
                                              # captured BEFORE either mutation
       self._scoring_policy.update_prediction(self._a, profile_b)
         -> _require_float/_require_prediction narrow profile_b's fields
         -> acceptance/influence/corrected computed per §6.5
         -> a.certainty, possibly a.current_prediction, mutated in place
       self._scoring_policy.update_prediction(self._b, profile_a)
         -> same, using the OTHER pre-captured snapshot
         -> b.certainty, possibly b.current_prediction, mutated in place
       self._interaction_policy.update_trust(self._a, self._b)  # no-op, W3-04 replaces
       self._interaction_policy.update_trust(self._b, self._a)  # no-op, W3-04 replaces
  -> both agents' post-interaction state is now visible to the NEXT
     encounter either of them enters, later in the same round or a later
     round — this is intentional per §6.5 (opinions really do propagate
     encounter-by-encounter within a round, not just round-by-round)
```

Full-arena context (owned by later tickets, shown so W3-03's slot is clear —
this box is NOT part of this ticket's diff):

```text
(W4-01, not yet built)
  for each round until RoundEngine.finished():
      engine.round()
      for (a, b), cell in engine.encounter_log[this round]:
          Encounter(a, b, scoring_policy, interaction_policy).process()  # <- W3-03
  aggregate participants' final current_prediction (W4-03/W6-02)
```

---

## 6. Pre-code gates

1. Confirm W2-01 and W3-02 are both landed on `develop` (done — §4 above;
   note the bookkeeping gap named there, which does not block starting per
   the person's own framing, but is flagged, not silently ignored).
2. Confirm `src/wocbots/interaction/` exists and is empty except its
   placeholder `__init__.py` (done — verified).
3. Confirm the baseline check suite is green **before** touching anything,
   so any later failure is attributable to this ticket's diff:
   `uv sync && uv run ruff check . && uv run ruff format --check . && uv run mypy src tests && uv run pytest`
   — run and confirmed green this session: **208 passed, 11 skipped, 1
   xfailed** (no failures), `ruff check` clean, `ruff format --check` 67
   files already formatted, `mypy src tests` clean on 67 source files. This
   is the number to diff against at close.
4. Re-read `protocols.py`'s `ScoringPolicy`/`InteractionPolicy` Protocol
   bodies immediately before writing the two implementing classes (done as
   part of this plan — §4).

---

## 7. Specification

### S1 — `src/wocbots/interaction/_util.py` (new)

```python
"""Small private helpers shared across the interaction kernel (W3-03) and
its future extensions (W3-04's trust clamp uses the same [lo, hi] shape).
Not part of any locked seam — nothing here is exported from the package.
"""

from __future__ import annotations


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp `value` into [lo, hi] (spec §6.5's certainty ruling; also used
    by trust's [0, 1] clamp, spec §6.5's trust paragraph)."""
    return max(lo, min(hi, value))
```

### S2 — `src/wocbots/interaction/scoring.py` (new)

```python
"""W3-03 — the certainty/flip kernel (spec §6.5, receiving side).

Implements the ScoringPolicy seam (protocols.py). Every equation under its
spec name (acceptance, influence, corrected), pinned by the worked example
in the ticket and re-derived independently in the plan (§4).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, cast

from wocbots.agents import Agent
from wocbots.interaction._util import clamp


class CertaintyFlipScoringPolicy:
    """Reference ScoringPolicy: spec §6.5's receiving-side equations, exact.

    Consumes a read-only partner_profile (the §6.5 privacy boundary) — never
    reaches into the partner Agent. Trust is untouched here (W3-04's seam).
    """

    CERTAINTY_LO = 0.01
    CERTAINTY_HI = 0.99
    FLIP_THRESHOLD = 0.50

    def update_prediction(self, agent: Agent, partner_profile: Mapping[str, object]) -> None:
        if agent.current_prediction is None:
            raise ValueError(
                "update_prediction called on an agent with no current_prediction "
                "set — an arena-round invariant violation (spec §3 Phase 2 must "
                "run first)"
            )

        b_prediction = self._require_prediction(partner_profile, "current_prediction")
        b_certainty = self._require_float(partner_profile, "certainty")
        b_confidence = self._require_float(partner_profile, "confidence")
        b_trust_score = self._require_float(partner_profile, "trust_score")
        b_prior_performance = self._require_float(partner_profile, "prior_performance")

        acceptance = 1.0 - agent.certainty
        influence = b_confidence * acceptance * (b_trust_score * b_certainty)
        corrected = influence * b_prior_performance
        if agent.current_prediction != b_prediction:
            corrected = -corrected

        new_certainty = clamp(agent.certainty + corrected, self.CERTAINTY_LO, self.CERTAINTY_HI)
        if new_certainty < self.FLIP_THRESHOLD:
            agent.current_prediction = cast(Literal[0, 1], 1 - agent.current_prediction)
            new_certainty = 1.0 - new_certainty
        agent.certainty = new_certainty

    def _require_float(profile: Mapping[str, object], key: str) -> float:
        value = profile[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"public_profile()[{key!r}] must be a float, got {type(value).__name__}")
        return float(value)

    def _require_prediction(profile: Mapping[str, object], key: str) -> Literal[0, 1]:
        value = profile[key]
        if value not in (0, 1):
            raise ValueError(
                f"public_profile()[{key!r}] must be 0 or 1 for an interaction "
                f"partner (never None — partner must have inferred already), "
                f"got {value!r}"
            )
        return value
```

*(Note on the `cast` in the flip line: after the top-of-function `is None`
guard, mypy narrows `agent.current_prediction` to `Literal[0, 1]` for
reads, but `1 - agent.current_prediction` widens back to `int` at the
type-checker level since `Literal[0, 1]` isn't closed under subtraction —
the `cast` re-asserts what's arithmetically guaranteed (0→1 or 1→0, never
anything else). This is the one spot verified against `mypy --strict`
output before considering the file done, not assumed to type-check from
reading it.)*

### S3 — `src/wocbots/interaction/policy.py` (new)

```python
"""W3-03 — reference InteractionPolicy (spec §6.5): always-willing,
always-truthful. `update_trust` is an explicit no-op stub — W3-04 replaces
its body per that ticket's S2 ("Replaces W3-03's no-op stub"); the class
and its call sites do not change.
"""

from __future__ import annotations

from wocbots.agents import Agent


class ReferenceInteractionPolicy:
    def should_interact(self, a: Agent, b: Agent) -> bool:
        return True

    def truth(self, a: Agent, b: Agent) -> bool:
        return True

    def update_trust(self, a: Agent, b: Agent) -> None:
        """No-op stub (ticket S3). W3-04 owns the real §6.5 trust math."""
        return None
```

### S4 — `src/wocbots/interaction/encounter.py` (new)

```python
"""W3-03 — the atomic per-encounter processor (plan §3 D1).

Consumes ONE entry of the shape RoundEngine.encounter_log[round] produces:
an (Agent, Agent) pair. Does not iterate the log itself — that's W4-01's
per-sample loop (plan §3 D1 names the ownership boundary explicitly).
"""

from __future__ import annotations

from wocbots.agents import Agent
from wocbots.protocols import InteractionPolicy, ScoringPolicy


class Encounter:
    def __init__(
        self, a: Agent, b: Agent, scoring_policy: ScoringPolicy, interaction_policy: InteractionPolicy
    ):
        self._a = a
        self._b = b
        self._scoring_policy = scoring_policy
        self._interaction_policy = interaction_policy

    def process(self) -> None:
        """Both directions, compute-then-apply (spec §6.5 symmetry ruling).

        Both profiles are snapshotted before either update_prediction call, so
        the two update_prediction calls below may run in either order with
        byte-identical results (pinned by test 5, plan §10).
        """
        profile_a = self._a.public_profile()
        profile_b = self._b.public_profile()

        self._scoring_policy.update_prediction(self._a, profile_b)
        self._scoring_policy.update_prediction(self._b, profile_a)

        self._interaction_policy.update_trust(self._a, self._b)
        self._interaction_policy.update_trust(self._b, self._a)
```

### S5 — `src/wocbots/interaction/__init__.py` (edited)

```python
from wocbots.interaction.encounter import process_encounter
from wocbots.interaction.policy import ReferenceInteractionPolicy
from wocbots.interaction.scoring import CertaintyFlipScoringPolicy

__all__ = ["CertaintyFlipScoringPolicy", "ReferenceInteractionPolicy", "Encounter"]
```

---

## 8. Observability

Pure-mechanism ticket, same as W3-01/W3-02's math pieces — no experiment
kind, no results manifest (nothing here is stochastic; `CertaintyFlipScoringPolicy`
and `ReferenceInteractionPolicy` take no `rng`). Observability is entirely
the test suite: every §6.5 equation pinned exactly, the worked example
landing as a permanent regression test per the ticket's acceptance
criteria.

---

## 9. Sequenced implementation steps

1. Run pre-code gates in §6 (baseline check suite green, confirmed).
2. Add `src/wocbots/interaction/_util.py` (S1).
3. Add `src/wocbots/interaction/scoring.py` (S2) — build incrementally:
   write `_require_float`/`_require_prediction` first, run `mypy --strict`
   on the file alone, then add `CertaintyFlipScoringPolicy.update_prediction`.
4. Add `src/wocbots/interaction/policy.py` (S3).
5. Add `src/wocbots/interaction/encounter.py` (S4).
6. Edit `src/wocbots/interaction/__init__.py` (S5).
7. Add `tests/unit/test_interaction_kernel.py` (§10) — write the
   worked-example pin FIRST and get it green before writing the other four
   ticket-required tests, then the two added-for-discipline tests (§10's
   "beyond the ticket" items).
8. Run the full check suite locally; fix anything red before moving on.
9. Write `tickets/W3-03_certainty-update-flip_CLOSING-REPORT.md` (touched
   paths, decisions cross-referenced to plan §3, check-suite output,
   before/after pytest counts).
10. Do **not** edit `tickets/00_INDEX.md`'s W3-02 row or `AGENT_HANDOFF.md`'s
    stale W3-02 entry as part of this ticket's diff (§4's finding is a
    W3-02 bookkeeping debt, not W3-03's to silently absorb) — flag it in the
    PR description instead, separately from W3-03's own status flip.
11. Flip W3-03's own row in `00_INDEX.md` to `◐ implemented, pending
    independent review` (matching the pattern already used for W3-02) —
    NOT `✅` — and update `AGENT_HANDOFF.md`'s CURRENT STATE per its own
    five-part format, demoting the current one to `## PRIOR`.


---

## 10. Test plan (exact pins)

All tests live in `tests/unit/test_interaction_kernel.py`, following
the file's existing local-helper convention (no shared conftest exists in
this repo — verified) — a module-level `make_agent(...)` mirroring
`test_w2_01_agent_state.py`'s, plus a `make_partner_profile(...)` builder
for constructing a bare `Mapping[str, object]` directly (some tests need to
drive `CertaintyFlipScoringPolicy.update_prediction` with a hand-built
profile, not a full second `Agent`, to isolate the math from
`public_profile()`/`Encounter` plumbing).

**1. Ticket-mandatory: the §6.5 worked-example pin (exact, 1e-9).**
`a`: certainty=0.62, current_prediction=1. `b` profile: current_prediction=0,
confidence=0.71, trust_score=0.78, certainty=0.80, prior_performance=1.1.
Call `CertaintyFlipScoringPolicy().update_prediction(a, b_profile)`.
Assert `a.current_prediction == 0` and `abs(a.certainty - 0.56519072) < 1e-9`.
This is the ticket's own value, independently re-derived in plan §4 — not
copied without verification.

**2. Ticket-mandatory: agreement mirror (exact, 1e-9).** Same numbers as
test 1, but `b_profile["current_prediction"] = 1` (agrees with `a`). Assert
`a.current_prediction == 1` (unchanged) and `abs(a.certainty - 0.80519072)
< 1e-9`, no flip.

**3. Ticket-mandatory: flip boundary, both sides (exact, 1e-9).**
Derived algebraically in this plan (not copied from the ticket's prose,
since the ticket only names the target post-update values, not the
inputs that produce them):
- 3a (→ flip): `a`: certainty=0.6, current_prediction=1. `b_profile`:
  current_prediction=0 (disagree), confidence=1.0, trust_score=1.0,
  certainty=0.2525, prior_performance=1.0. Pre-clamp certainty = 0.6 −
  (0.4 × 1.0 × (1.0 × 0.2525) × 1.0) = 0.6 − 0.101 = 0.499 < 0.50. Assert
  `a.current_prediction == 0` and `abs(a.certainty - 0.501) < 1e-9`.
- 3b (→ no flip): same shape, `b_profile["certainty"] = 0.2475`. Pre-clamp
  certainty = 0.6 − 0.099 = 0.501, not < 0.50. Assert
  `a.current_prediction == 1` (unchanged) and `abs(a.certainty - 0.501) <
  1e-9`.

**4. Ticket-mandatory: clamp saturation (ten consecutive agreements).**
`a`: certainty=0.62, current_prediction=1. `b_profile`: current_prediction=1
(agrees every time), confidence=1.0, trust_score=1.0, certainty=0.99,
prior_performance=1.3 (the §2 table's upper bound). Call
`update_prediction(a, b_profile)` ten times in a loop. Hand-computation
(plan §4-adjacent, shown so the test isn't a black box): round 1 pushes
`a.certainty` from 0.62 to (uncapped) 1.10906, clamped to 0.99; every
subsequent round's `corrected` (= `(1 − 0.99) × 1.287` = 0.01287) still
overflows past 0.99, so it stays clamped at exactly 0.99 for rounds 2–10.
Assert after the loop `a.certainty == 0.99` exactly (not approximately —
clamp is an exact `min()`, no floating drift possible) and, on every
iteration, `1.0 - a.certainty >= 0.01` (acceptance never reaches 0) —
asserted inside the loop, not just at the end, since the requirement is
"never reaches 0" across all ten, not just the final state.

**5. Ticket-mandatory: symmetry under swapped processing order (byte-identical).**
Build two fresh, identically-initialized `(a, b)` pairs from the same
seed values (certainty/current_prediction/etc. on both sides, chosen to be
a real interaction — e.g. reuse test 1's numbers as two full `Agent`s, not
a profile stub, since this test exercises `Encounter.process`, not
`update_prediction` directly). Run A: `Encounter(a1, b1,
CertaintyFlipScoringPolicy(), ReferenceInteractionPolicy()).process()`.
Run B: `Encounter(b2, a2, CertaintyFlipScoringPolicy(),
ReferenceInteractionPolicy()).process()` on the mirror pair (constructor
argument order swapped) — this is exactly "swap the two `update_prediction`
call sites" since `Encounter`'s constructor argument order only determines
*label order*, not which snapshot `process()` captures first — both
snapshots are always taken, inside `process()`, before either mutation.
Assert `(a1.certainty, a1.current_prediction, b1.certainty,
b1.current_prediction) == (a2.certainty, a2.current_prediction,
b2.certainty, b2.current_prediction)` exactly (`==`, not a tolerance — this
is proving determinism, not re-deriving a formula, so exact equality is
the correct assertion, unlike tests 1–4 which re-derive arithmetic and so
need a tolerance for legitimate float rounding in the *computation itself*).

**6. Added, beyond the ticket — degenerate input, agent side (preamble
§4-(c)).** `a.current_prediction = None` (the construction-time default,
before any classifier ran). Call `update_prediction(a, valid_profile)`.
Assert it raises `ValueError` (not a silent no-op, not an unrelated
`TypeError` from arithmetic on `None`).

**7. Added, beyond the ticket — degenerate input, partner-profile side.**
A profile with `current_prediction` set to something other than `0`/`1`/`None`
(e.g. a stray `2`, simulating a corrupted upstream producer) and, in a
second case, a non-numeric `certainty` (e.g. a string). Assert each raises
`ValueError`/`TypeError` respectively, naming the offending key in the
message (asserted via `pytest.raises(..., match=...)`), not a bare
arithmetic crash several lines later.

**8. Added, beyond the ticket — `ReferenceInteractionPolicy` reference
behavior.** `should_interact` and `truth` both return `True` for an
arbitrary pair; `update_trust` is callable with two `Agent`s and returns
`None` while leaving both agents' `trust_score` completely unchanged
(asserted before/after equality) — locking in "no-op stub" as an actual
behavioral guarantee this ticket's tests defend, not just a docstring
claim W3-04 could quietly violate by accident.

---

## 11. Blast radius (forward commitments)

- **W3-04** needs: `ReferenceInteractionPolicy` (to replace its
  `update_trust` body, not the class), `Encounter`'s shape (plan §3 D1b:
  the expected hook is `class EncounterWithHistory(Encounter)` overriding
  `process()` — `Encounter.__init__`'s signature and `process()`'s "both
  profiles captured up front" invariant are now load-bearing for W3-04
  too, since a subclass overriding `process()` must preserve that
  ordering if it calls `super().process()`), and the `clamp()` helper in
  `_util.py`.
- **W4-01** needs: `CertaintyFlipScoringPolicy`, `Encounter` (or whatever
  W3-04 subclasses it into), instantiated and `.process()`-called once per
  `((a, b), cell)` tuple pulled from `RoundEngine.encounter_log[round]`.
- **W6-02** needs the certainty/flip mechanism as a black box (it builds
  the confidence ladder on top of post-arena certainty values) — no direct
  code dependency beyond `Agent.certainty`/`current_prediction` already
  being correctly maintained.
- Widening `_PROFILE_FIELDS` on `Agent` (six fields) or the `ScoringPolicy`/
  `InteractionPolicy` Protocol signatures in `protocols.py` are OUT of this
  ticket's blast radius — both are locked contracts per `protocols.py`'s
  own docstring ("renaming or loosening a seam is a cross-ticket contract
  change routed through the index"). This plan makes no changes to either
  file.

---

## 12. Risks, alternatives, open questions FOR THE STAKEHOLDER

- **R1 — W3-02 bookkeeping debt (see §4's grounding-fact finding).**
  `00_INDEX.md` and `AGENT_HANDOFF.md` both still describe W3-02 as
  "pending independent review" despite PR #24 being merged (by a person
  distinct from the implementer) into `develop`. This plan does not fix it
  as part of W3-03's diff (§9 step 10) but flags it for the stakeholder /
  whoever merged #24: the index row and handoff should be updated with a
  `reviewed: @rootwij, <date>` line (or, if the merge was NOT in fact an
  independent review — e.g. a mechanical merge without a real diff read —
  that needs surfacing explicitly, since starting W3-03 against
  unreviewed, potentially-still-changing contracts is a real risk this
  plan is knowingly accepting, matching the person's own framing).
  Recommend confirming directly with whoever merged #24 whether preamble
  §8's actual review steps (read the full diff, check the forbidden-
  shortcut register, verify test pins) were performed, since the merge
  alone doesn't prove it happened.
- **R2 — `RoundEngine.encounter_log`'s stability.** Per R1, W3-02's
  contracts are merged but not confirmably reviewed. If review surfaces a
  change to `encounter_log`'s shape (e.g. deduplication, a different tuple
  ordering, or adding a round-relative sequence number), `Encounter`'s
  constructor (`(Agent, Agent, ScoringPolicy, InteractionPolicy) -> None`)
  is actually insulated from most plausible shape changes — it takes two
  `Agent`s directly, not an encounter-log tuple — so the risk is contained
  to whoever calls it (W4-01), not to this ticket's own code. Named here so
  it's visible, not because this plan believes it needs to hedge further.
- **R3 — `_require_float`'s `bool` exclusion.** `isinstance(True, int)` is
  `True` in Python, so a stray `bool` value in a profile field would
  silently pass a naive `isinstance(value, (int, float))` check and
  arithmetic-corrupt every downstream computation (`True` behaving as
  `1.0`, `False` as `0.0`). Excluded explicitly (S2's `isinstance(value,
  bool) or not isinstance(...)` guard). This is defensive coding, not a
  spec requirement — flagged as a MAY-choice, not something needing
  stakeholder sign-off, but named so a reviewer sees it as deliberate.
- **Open question — does `Encounter` belong in `interaction/` at all, or
  should W4-01 write its own per-encounter orchestration inline in its
  per-sample loop?** This plan's position (D1) is that a shared,
  independently-tested unit is worth the small extra surface because
  W3-04 needs the identical "capture both profiles, apply both directions"
  shape for history-writing, and duplicating that shape between W3-03's
  tests and W4-01's loop risks the two drifting (e.g. W4-01 accidentally
  reading a live profile instead of a pre-captured one). If the stakeholder
  disagrees and wants W4-01 to own all per-encounter orchestration, the
  only change needed is deleting `encounter.py` and its export — the
  `ScoringPolicy`/`InteractionPolicy` implementations are unaffected either
  way. Flagging for confirmation before or during review, not blocking
  implementation on it (this plan's default is to build it, since it's
  directly required by test 5 as specified). (D1a is settled — the
  class-vs-function shape of this unit is decided; this open question is
  only about whether the unit belongs in this package at all.)

---

## 13. Definition of Done (preamble §6, instantiated)

1. [X] W2-01 and W3-02 confirmed landed (done — §4/§6); W3-02's own
   bookkeeping gap (R1) reported, not silently fixed inside this ticket's
   diff.
2. [X] `CertaintyFlipScoringPolicy` exists, implements `ScoringPolicy`
   exactly, every §6.5 receiving-side equation present under its spec name.
3. [X] `ReferenceInteractionPolicy` exists, implements `InteractionPolicy`
   exactly, `update_trust` is a no-op (test 8).
4. [X] `Encounter` exists (class, plan §3 D1a), `.process()`'s
   both-directions compute-then-apply proven by test 5, not just
   implemented.
5. [X] All 10 tests in §10 land in the same change set (5 ticket-mandatory +
   3 added-for-discipline, clearly distinguishable in the test file's own
   comments/docstrings).
6. [X] `ruff check .` passes.
7. [X] `ruff format --check .` passes.
8. [X] `mypy src tests` passes (strict, no new relaxations — confirm
   `wocbots.interaction` does not appear in any `[[tool.mypy.overrides]]`
   block added by this diff).
9. [X] `pytest` passes; new total compared against the confirmed baseline
   (2018 passed, 11 skipped, 1 xfailed) — expect +10 passed, skip/xfail
   counts unchanged (nothing in this ticket touches the pre-existing skips).
10. [X] Results manifest: N/A (pure-mechanism ticket, no experiment kind —
    per §8).
11. [X] Touched paths listed project-root-relative in the closing report.
12. [X] `00_INDEX.md`'s W3-03 row flipped to `◐ implemented, pending
    independent review` (not `✅`) — full `✅ (reviewed: <who>, <date>)`
    only after preamble §8 sign-off.
13. [X] `AGENT_HANDOFF.md` updated: old CURRENT STATE demoted to `## PRIOR`,
    fresh CURRENT STATE with all five parts, header line refreshed.
14. [ ] Independent review signed off (preamble §8) — reviewer independent
    of whoever drives this implementation session; findings adjudicated by
    the stakeholder before `✅`.
15. [X] R1 (W3-02's stale bookkeeping) and the open question in §12
    explicitly surfaced in the PR description, not left for a reviewer to
    discover unprompted.

