# W5-02 — The matched head-to-head: WoC-Bots vs the MLP baseline (experiment)

**Wave:** W5. **Blocked by:** W2-03, W4-04, W5-01. **Blocks:** W5-03, W5-04, W5-05.
**Binding spec sections:** §9.2 (the matched configuration and its published optima), §9.1, §10.10.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The published head-to-head, reproduced: the deliberately-matched 5-agent configuration against the W5-01
baseline across the 1–50 epoch sweep. The claim under test is a SHAPE — WoC-Bots reach their optimum in
roughly half the epochs, the MLP edges them slightly at full training — not a pair of decimals.

## Grounding (read before starting)

- Spec §9.2's crowd-comparison paragraph: 5 features (budget, vote_count, vote_average, runtime, popularity);
  five agents — four 2-feature agents anchored on budget + one 5-feature agent; trust-weighted aggregation.
  Targets: WoC-Bots ≈ **76.3% near 20 epochs**; MLP ≈ **76.8% near 40**.

## Specification

- **S1.** One config: the matched roster, trust-weighted aggregation, epochs 1–50 sweep, 10 seeded runs,
  same W1-05 splits as the baseline. Output: both accuracy-vs-epoch curves in one manifest.

## Forbidden shortcuts

- Tuning anything to close a gap without recording it (a documented config change is fine; a quiet one is
  fraud against your own experiment). Different splits/normalization than the baseline saw.

## Test requirements

1. (slow) WoC-Bots optimum within ±3 of 76.3; optimum epoch materially earlier than the MLP's; final
   ordering as published.
2. Manifest: both curves regenerate from one config + seed set.

## Acceptance criteria

- The matched comparison lands in band with the published shape; curves manifest-recorded for the Q1 report.
