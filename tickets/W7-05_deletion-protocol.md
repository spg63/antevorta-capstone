# W7-05 — The missing-data deletion protocol (infrastructure)

**Wave:** W7. **Blocked by:** W7-01. **Blocks:** W7-06.
**Binding spec sections:** §3 (sit-out — the capability the masks will probe), §9.1.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The masks that make W7-06's study fair: seeded feature-value deletion applied identically to every method
arm. Infrastructure only, split from the study so the corruption machinery is reviewed and pinned before any
curve is drawn with it.

## Grounding (read before starting)

- Spec §3's sit-out rule; W1-06/W7-02 anchor RESULTs (the targeted regime concentrates on top anchors).

## Specification

- **S1.** Seeded deletion masks at rates {5, 10, 20, 30, 40, 50}%, TEST samples only, two regimes:
  missing-completely-at-random, and feature-targeted (concentrated in the top-2 anchor features — the harder,
  more diagnostic case). Masks persisted; every method arm consumes the identical corruption.
- **S2.** Mask application utilities for both consumers: sit-out form (values removed → W4-01 participant
  selection engages) and imputer-input form (values NaN'd for W7-06's baseline arms).

## Forbidden shortcuts

- Per-method masks; deletion touching training data (the capability under test is inference-time).

## Test requirements

1. Mask determinism: same seed → identical masks; rates land within rounding of nominal.
2. Arm identity: sit-out form and NaN form encode the SAME cells (structural).
3. Train untouched: training artifacts hash-identical before/after masking.
4. Targeted regime: deletions demonstrably concentrated in the named anchors.

## Acceptance criteria

- Persisted, pinned masks + application utilities; W7-06 can begin with its fairness pre-proven.
