# W2-01 — Agent state and the public profile

**Wave:** W2. **Blocked by:** W0-02 (pure code — no data, can start early). **Blocks:** W2-02, W3-03.
**Binding spec sections:** §2 (the state table — names, ranges, inits are normative), §5.4 (confidence),
§6.5 (public-profile boundary).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full, esp. §7 (exact state names).

## Why this ticket exists (system meaning)

The §2 state table is what every later mechanism reads and writes; a subtly wrong init here surfaces three
waves later as "the swarm doesn't work." This ticket makes the table executable and pinned — state only, no
classifier (W2-02), so the diff is small and the pins are exact.

## Grounding (read before starting)

- Spec §2 in full; §5.4; §6.5's public-profile note.

## Specification

- **S1.** `Agent` (replacing the W0-02 stub internals) carrying exactly the §2 state under exactly the §2
  names. Init formulas pinned: `certainty = (eval_accuracy + eval_precision)/2`; `trust_score =
  eval_precision`; `confidence = w·(acc, prec, rec)` per §5.4 (Hollywood default (0.3, 0.5, 0.2), weights
  config); `prior_performance = 1.0`; `prior_accuracy = eval_accuracy`. Initialization takes eval metrics as
  inputs — where they come from is W2-02's business.
- **S2.** `public_profile()` → read-only mapping: prediction, certainty, confidence, trust_score,
  prior_performance, features. Nothing else, immutable (spec §6.5 — the boundary W8's meta-swarm audit leans
  on).

## Forbidden shortcuts

- Renamed state variables or "simplified" init formulas (preamble §7).
- The profile exposing the classifier, data, or history.

## Test requirements

1. Init pins: eval metrics (0.8, 0.7, 0.6) + Hollywood weights → certainty 0.75, trust 0.7, confidence 0.71
   (exact, 1e-12); prior_performance 1.0; prior_accuracy 0.8.
2. Profile: immutable; exactly the six fields; mutation attempts raise.
3. mypy strict on the tightened seam types (W0-02's stub rule: tighten, never loosen).

## Acceptance criteria

- §2 implemented verbatim and pinned; the profile boundary is real; check suite green.
