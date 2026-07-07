# W7-06 — The missing-data tolerance study (experiment)

**Wave:** W7. **Blocked by:** W7-04, W7-05. **Blocks:** W8-06.
**Binding spec sections:** §3 (sit-out), §12 (Q2 exit), §9.1.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

First distinctive-capability experiment: monolithic models impute or discard; WoC-Bots field a smaller crowd.
Measured as degradation CURVES against impute-and-predict — no published reference numbers exist, so the
experimental design itself is a deliverable and a paper section. A rigorous negative result is a valid
outcome; an unexamined one is the only failure.

## Grounding (read before starting)

- W7-05's masks; W7-04's method arms and fairness machinery.

## Specification

- **S1.** Arms over the W7-05 masks, both regimes, both datasets, 10 seeds: WoC-Bots (swarm) via sit-out —
  unchanged, that's the point; each baseline × {mean imputation, kNN imputation} (imputers fit on train
  only); PLUS XGBoost's native missing-value handling as its own arm (the strongest fair competitor —
  mandatory).
- **S2.** Outputs: accuracy-vs-deletion-rate curves per arm per regime per dataset (mean ± std bands);
  WoC-Bots participation statistics (mean crowd size vs rate; degenerate-crowd counts) — the mechanism-level
  evidence that sit-out, not luck, produced the curve; the relative-degradation comparison table.

## Forbidden shortcuts

- Imputing for WoC-Bots anywhere; "helping" it at high rates (degenerate-crowd behavior at 50% is a finding);
  omitting XGBoost-native because it competes too well.

## Test requirements

1. Imputer hygiene: fit on train only (leakage-guard pattern).
2. Sit-out accounting: per-sample participant counts match the mask arithmetic (pinned on a fixture).
3. (slow) All arms produce curves; participation stats and the comparison table land in the manifest.

## Acceptance criteria

- The study exists for both datasets and regimes, fair by construction; the graceful-degradation claim
  confirmed and quantified — or the negative documented with participation evidence. W7 wave complete.
