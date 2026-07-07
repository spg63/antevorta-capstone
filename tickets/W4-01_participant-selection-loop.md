# W4-01 — Participant selection, per-sample loop, and reset semantics

**Wave:** W4. **Blocked by:** W2-02, W3-02, W3-04 (first hard cross-stream integration). **Blocks:** W4-02,
W4-03, W6-01, W7-01.
**Binding spec sections:** §3 (lifecycle phases 1–3), §6.6 (reset semantics), §10.6, §10.7; §11 (synthetic
anchor).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The assembly point: for EACH test sample, the participating agents infer, enter a fresh arena, and interact.
The two make-or-break rules are per-sample state hygiene (what resets vs what persists) and the varying
participant set — the missing-data headline capability is just this loop done right. Ground-truth feedback is
deliberately NOT here (W4-02), keeping this diff about the loop.

## Grounding (read before starting)

- Spec §3 (the phase diagram IS the design), §6.6, §10.6/§10.7.

## Specification

- **S1.** Participant selection per sample: exclude pruned agents and any agent missing a required feature
  value. Everything downstream — arena size, round count — derives from THIS participant set.
- **S2.** Per-sample loop: fresh `current_prediction` from each participant's classifier; `certainty` reset
  to its training-time value; W3 arena + interactions; aggregation via the `Aggregator` seam (a trivial
  majority stub until W4-03). Trust, prior_performance, prior_accuracy, history persist across samples.
- **S3.** The synthetic e2e anchor (spec §11): the full loop on a seeded, linearly-separable dataset MUST
  reach ~100% test accuracy — the permanent canary every later wave keeps green.

## Forbidden shortcuts

- One arena for the whole test set; certainty carrying across samples; imputation in participant selection.

## Test requirements

1. Reset semantics: 3 samples; certainty re-initializes each sample while trust/history persist and evolve.
2. Sit-out: a sample missing feature f excludes exactly the f-dependent agents; arena and round count derive
   from the reduced N (asserted).
3. Participation accounting: per-sample participant counts land in the manifest.
4. The synthetic anchor: ~100%, seeded, stable across 10 runs.

## Acceptance criteria

- The infer → arena → aggregate loop runs end to end, seeded; state hygiene proven by tests; the anchor is
  green and marked permanent.
