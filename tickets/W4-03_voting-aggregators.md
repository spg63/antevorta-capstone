# W4-03 — The three voting aggregators (UWM, WVM, trust-weighted)

**Wave:** W4. **Blocked by:** W4-01. **Blocks:** W4-04.
**Binding spec sections:** §7 (the three formulas + tie rule — normative), §2 (prior_accuracy vs trust_score),
§10.4.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

Three interchangeable `Aggregator` implementations that are each other's controls: UWM the floor, WVM the
standard weighted baseline, trust-weighted the contribution — the only one consuming what the arena actually
produces. Mechanism only; the comparison experiment is W4-04.

## Grounding (read before starting)

- Spec §7's formulas and tie rule; §10.4 (the vote-scale bug).

## Specification

- **S1.** UWM: 100 votes per participant for its predicted class. WVM: `round(100 × prior_accuracy)`, 50
  votes before any track record. Trust-weighted: `votes = round(((prior_accuracy + trust_score)/2) × 100)`.
- **S2.** Majority of vote totals wins; exact ties → class 1, tie occurrences counted. Each returns a W0-02
  `Prediction` (tier/margin left None here — W4-04 fills them).
- **S3.** Same-state rule: aggregators consume a frozen snapshot of crowd state, so the three can be compared
  on IDENTICAL per-sample runs (aggregation is the only variable).

## Forbidden shortcuts

- `prior_accuracy`/`trust_score` scale confusion — a 5,000-vote agent is spec §10.4's exact bug.
- Tie-breaks by "whatever max() returns."

## Test requirements

1. Formula pins: prior_acc 0.8 → WVM 80; (0.8, trust 0.7) → trust-weighted 75; no-history agent → WVM 50.
   Exact.
2. Tie pin: engineered 50/50 split → class 1, tie counted.
3. Same-state guarantee: the three aggregators consume one frozen snapshot (structural test).

## Acceptance criteria

- Three formula-pinned, interchangeable aggregators behind the seam; check suite green.
