# W7-01 — Airline ETL: label rule, structured missingness, splits

**Wave:** W7. **Blocked by:** W1-05 (patterns/artifacts), W4-01 (sit-out machinery). **Blocks:** W7-02, W7-05.
**Binding spec sections:** §4.4 (the dataset — label rule normative), §3 (sit-out), preamble §7 (generality).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The second dataset is the generality test: if onboarding requires touching toolkit core, the core failed. It
brings the sit-out story in real data — a `0` in the 1–5 service ratings means "not applicable," not the
number zero.

## Grounding (read before starting)

- Spec §4.4; the Kaggle Airline Passenger Satisfaction dataset (provenance per W1-01's pattern: checksums,
  versions, fixtures).

## Specification

- **S1.** `wocbots.data.airline`: 22 features; label satisfied vs not with **neutral counting as
  dissatisfied** (normative); 0-valued satisfaction ratings decoded as MISSING so W4-01's sit-out engages;
  per-feature missingness rates recorded.
- **S2.** Same split/normalization discipline as W1-05: stratified 80/20 + eval slice + 5-fold artifacts,
  train-only statistics, persisted.

## Forbidden shortcuts

- Imputing the 0-coded N/As; dataset-specific branches in toolkit core; neutral-as-satisfied "to see."

## Test requirements

1. Label pin: satisfied/neutral/dissatisfied fixture rows → 1/0/0.
2. Missingness decode end-to-end: a 0-rated WiFi row excludes WiFi-dependent agents from that sample.
3. Core-untouched proof: the onboarding merges with zero diffs under
   `wocbots/{agents,arena,interaction,aggregation}/` (stated in the close report).
4. Leakage guards re-applied (the W1-05 pattern).

## Acceptance criteria

- Airline data flows through the unchanged core; missingness works as sit-out; split artifacts persisted.
