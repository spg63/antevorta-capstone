# W2-01 Mini-Plan — Agent state and the public profile

**Author:** Rutvij (AGENTS stream). **Date:** 2026-07-16. **Session mode:** PLAN.
**Status: DRAFT — presented for review (preamble §0.1c). No code until approved and W0-01 + W0-02 are ✅.**
**Reviewer path:** CORE (consumer-reviews-producer, index streams table), or the stakeholder.

**Read for this plan (in full):** `CLAUDE.md`, `01_MANDATORY_PREAMBLE.md`, `AGENT_HANDOFF.md`,
`W2-01_agent-state-profile.md`, spec §2 / §5.4 / §6.5 (+ §6.6, §6.7 context), `W0-02_types-policy-seams.md`
+ its approved plan §7 (S2/S3 — the seams and the constructor-only `Agent` stub this ticket replaces).

**Blockers at plan time:** W0-02 not landed (blocked by W0-01, not landed). This plan binds to the
APPROVED W0-02 plan's §7 signatures; if what lands differs, this plan re-reviews before implementation.

---

## 1. Scope

Make the spec §2 state table executable and pinned, plus the §6.5 `public_profile()` boundary.
State only — no classifier (W2-02), no arena mechanics (W3), no update rules (W3-03/W3-04/W4-02 own the
mechanics that later mutate this state). Nothing stochastic lands here: no RNG anywhere in this ticket.

## 2. Sequenced steps

1. **S0 — preconditions.** Confirm W0-01 ✅ and W0-02 ✅ in `00_INDEX.md`; diff the landed
   `protocols.py`/`agents/__init__.py` against the W0-02 plan §7; re-read this plan's §6 open
   questions and confirm each has a recorded ruling.
2. **S1 — `ConfidenceWeights`.** Frozen pydantic model (`extra="forbid"`): `w_acc, w_prec, w_rec`,
   each in [0, 1], sum == 1 within 1e-9 (validator). Named Hollywood default (0.3, 0.5, 0.2) as a
   module constant, not baked into `Agent` (spec §5.4: weights are per-problem config).
3. **S2 — `Agent`.** Implement in `src/wocbots/agents/agent.py`; re-export from
   `src/wocbots/agents/__init__.py` (replacing the W0-02 constructor-only stub) so the W0-02
   TYPE_CHECKING import path `from wocbots.agents import Agent` is unchanged. Exactly the §2 names —
   no synonyms (preamble §7).
4. **S3 — `public_profile()`.** Read-only snapshot `Mapping[str, object]` (MappingProxyType over a
   fresh dict per call), exactly six keys, `features` exposed as `tuple` so no mutable internal leaks.
   Matches the W0-02 `ScoringPolicy.update_prediction(partner_profile: Mapping[str, object])` seam —
   tightened value semantics, no seam rename (tighten-never-loosen).
5. **S4 — tests** (`tests/unit/test_w2_01_agent_state.py`), same change set as the feature (§4 below).
6. **S5 — check suite** green: `ruff check .` / `ruff format --check .` / `mypy src tests` (strict on
   the tightened types) / `pytest`.
7. **S6 — close checklist** (preamble §6): results manifest N/A (pure-code ticket, no experiment) —
   state so explicitly; index status flip with independent-review sign-off (§8: CORE teammate or a
   different AI system than the implementer); `AGENT_HANDOFF.md` updated. Humans commit.

## 3. Files to touch

- `src/wocbots/agents/agent.py` — new: `ConfidenceWeights`, `Agent`.
- `src/wocbots/agents/__init__.py` — replace stub internals, re-export `Agent` (+ `__all__`).
- `tests/unit/test_w2_01_agent_state.py` — new.
- Nothing outside `agents/` + tests (one-writer rule; no protocol/seam edits).

## 4. Interfaces / signatures (proposed)

```python
class ConfidenceWeights(BaseModel, frozen=True, extra="forbid"):
    w_acc: float; w_prec: float; w_rec: float   # each [0,1]; sum == 1 (±1e-9)

HOLLYWOOD_WEIGHTS = ConfidenceWeights(w_acc=0.3, w_prec=0.5, w_rec=0.2)

class Agent:
    def __init__(self, *, features: Sequence[str],
                 eval_accuracy: float, eval_precision: float, eval_recall: float,
                 confidence_weights: ConfidenceWeights) -> None: ...
    # Init (spec §2 / §5.4, pinned):
    #   certainty         = (eval_accuracy + eval_precision) / 2
    #   trust_score       = eval_precision
    #   confidence        = w_acc*acc + w_prec*prec + w_rec*rec   (fixed after init)
    #   prior_performance = 1.0
    #   prior_accuracy    = eval_accuracy
    #   current_prediction: Literal[0, 1] | None = None   (set at Phase-2 inference — Q3)
    #   _certainty_train retained for the §6.6 per-sample reset (Q4)
    # Validation: eval metrics in [0,1] else ValueError; features non-empty (Q6), stored as tuple.
    # Mutability: certainty / trust_score / prior_performance / prior_accuracy / current_prediction
    #   mutable (W3-03, W3-04, W4-02 own those updates); confidence + eval metrics read-only
    #   properties (spec §2: "fixed after training").

    def public_profile(self) -> Mapping[str, object]:
        # exactly: current_prediction, certainty, confidence, trust_score,
        #          prior_performance, features        (spec §6.5; key name — Q1)
        # never: classifier, data, history, eval metrics, prior_accuracy

    def reset_certainty(self) -> None: ...   # §6.6 hook; caller is W4-01's loop (Q4)
```

Takes eval metrics as inputs — where they come from is W2-02's business (ticket S1).

## 5. Test list (what each asserts)

1. **Ticket pin (exact, 1e-12):** metrics (0.8, 0.7, 0.6) + Hollywood weights → certainty 0.75,
   trust_score 0.7, confidence 0.71, prior_performance 1.0, prior_accuracy 0.8.
2. **Second hand-computed case** (guards against hard-coding pin 1): metrics (0.62, 0.71, 0.58) →
   certainty 0.665, confidence 0.657, trust_score 0.71, prior_accuracy 0.62 — recomputed from the
   formulas in the test, not pinned as rounded literals (v1.2 lesson: never pin rounded intermediates).
3. **Weights validation, both sides:** sum 0.99999 and 1.00001 rejected; exact 1.0 accepted; negative
   weight rejected; frozen; unknown keys rejected.
4. **Eval-metric bounds, both sides:** −0.01 and 1.01 raise; 0.0 and 1.0 accepted.
5. **Profile exact fields:** key set == the six §6.5 fields, nothing else.
6. **Profile immutability:** item assignment raises; `features` value is a tuple; underlying Agent
   state unreachable through the mapping.
7. **Profile privacy:** no classifier / history / eval-metric / prior_accuracy key present (the W8
   meta-swarm audit boundary).
8. **Profile freshness:** externally set `certainty` (simulating W3-03), a new `public_profile()`
   call reflects it (snapshot-per-call semantics documented).
9. **Reset semantics:** mutate certainty → `reset_certainty()` restores the training-time value;
   trust_score / priors untouched (persistence split per §6.6).
10. **Degenerate input:** `features=[]` raises (pending Q6 ruling).
11. **Seam compatibility:** `from wocbots.agents import Agent` still imports; mypy strict green on
    the tightened types (suite-level gate).

## 6. Open questions (need rulings at review, before implementation)

- **Q1 — profile key name (ticket-vs-spec discrepancy, REPORTED per preamble §0.2).** Ticket S2 says
  "prediction"; spec §6.5 and the §7 exact-names rule say `current_prediction`. Spec wins — propose
  the profile key is `current_prediction` and the ticket wording is flagged as a ticket bug at close.
- **Q2 — interaction history.** Spec §2 lists it (init: empty), but W3-04 owns the history store
  (with the v1.11 cardinality ruling). Propose: W2-01 lands no history attribute; W3-04 attaches its
  store. Alternative: an empty placeholder here that W3-04 replaces — wasted churn in my view.
- **Q3 — `current_prediction` before first inference.** No classifier exists in this ticket. Propose
  `Literal[0,1] | None`, `None` until Phase-2 inference sets it (never `None` during an arena round).
- **Q4 — the §6.6 reset hook.** Propose W2-01 stores the training-time certainty and ships
  `reset_certainty()`; W4-01's per-sample loop is the caller. Alternative: W4-01 implements reset
  externally — weaker encapsulation of state W2-01 owns.
- **Q5 — `ConfidenceWeights` placement.** Propose it lives in `agents/` (AGENTS-owned value type)
  and W0-03's experiment-config models embed it. Needs a nod from CORE (W0-03 owner).
- **Q6 — empty feature list.** Propose constructor rejects 0 features; how many features agents
  actually get is W2-03's policy, not validated here beyond non-empty.

## 7. Forbidden-shortcut self-check (preamble §3)

No RNG, no thresholds, no data, no classifier in scope. Relevant items: renamed state (§7 — guarded
by exact-name pins), profile leaking internals (guarded by tests 6–7), speculative fields beyond §2
(none added — history explicitly deferred, Q2).
