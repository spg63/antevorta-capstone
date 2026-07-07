# W1-05 — Splits and normalization (with structural leakage guards)

**Wave:** W1. **Blocked by:** W1-04. **Blocks:** W1-06, W2-02 (real-data ACs), W5-01, W7-01.
**Binding spec sections:** §4.3 items 8–9, §10.5 (leakage), §9.1 (fixed-splits discipline).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

Normalization statistics computed on the wrong side of the split poison every downstream metric invisibly —
the nastiest silent corruption in the project. This ticket closes it structurally, once, and freezes the
split artifacts every experiment reuses.

## Grounding (read before starting)

- Spec §4.3.8–9, §10.5; W1-04's labeled dataframe.

## Specification

- **S1.** Seeded, label-stratified 80/20 train/test (~2,959 / ~740); 90/10 eval slice off the training side.
  Split membership persisted (row ids per split, keyed by seed) — every experiment and mechanism comparison
  reuses identical splits. 5-fold split artifacts generated too (Q2 consumes them; cheap to make now).
- **S2.** Min-max scaling to [0, 1], statistics from the TRAIN split only, applied to eval/test; scaler
  params persisted with the split artifact.
- **S3.** `revenue` structurally excluded from the feature matrix (label + W2-02's sanity agent only).

## Forbidden shortcuts

- Scaler statistics touching eval/test rows; re-randomized splits between experiments.

## Test requirements

1. Split determinism: same seed → identical membership; stratification within ±1 point per split.
2. Leakage guard (structural): scaler params provably a function of train rows only (perturb test rows →
   params unchanged).
3. No-revenue guard: the feature-matrix builder cannot emit `revenue` (asserted).

## Acceptance criteria

- Persisted split + scaler artifacts; leakage structurally tested; all later tickets consume these artifacts
  and nothing else.
