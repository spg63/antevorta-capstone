# W5-03 — The robustness contrasts: feature removal, crowd vs MLP (experiment)

**Wave:** W5. **Blocked by:** W5-02. **Blocks:** W5-05.
**Binding spec sections:** §9.2 (the two published contrasts), §9.1, §10.10.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The method's fingerprint: the crowd degrades more gracefully than the monolith when a strong feature
disappears, and gains less than the monolith when a noisy one does (bad agents were already marginalized).
The CONTRASTS are the acceptance target; the decimals are seeded noise.

## Grounding (read before starting)

- Spec §9.2's robustness paragraph; W5-02's matched protocol (this ticket is two variants of it, both arms).

## Specification

- **S1.** Remove `vote_count`, both arms: expect WoC-Bots decline ≈ 1.9 points vs MLP ≈ 4.
- **S2.** Remove `runtime`, both arms: expect MLP improve ≈ 1.7 vs WoC-Bots ≈ 0.3.
- Same protocol, seeds, and splits as W5-02; the W5-01 removal-variant configs provide the baseline arms.

## Forbidden shortcuts

- Comparing arms run under different splits or epochs; absorbing a wrong-direction result.

## Test requirements

1. (slow) Both contrast DIRECTIONS hold with the crowd-vs-MLP gaps in the published ballpark (vote_count:
   crowd loss < MLP loss by ≥ 1 point; runtime: MLP gain > crowd gain).
2. Manifest completeness for all four runs.

## Acceptance criteria

- Both published contrasts reproduced in direction and rough magnitude; wrong-direction results escalated
  with manifests, not closed around.
