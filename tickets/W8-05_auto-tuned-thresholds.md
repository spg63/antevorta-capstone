# W8-05 — Auto-tuned confidence thresholds per dataset (research / stretch)

**Wave:** W8. **Blocked by:** W6-03 (swarm traces). **Blocks:** W8-06.
**Binding spec sections:** §8.2 (thresholds are configuration; auto-tuning is the flagged open question),
§9.1.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full. **Research ticket:** the mini-plan MAY split it
further (objective/tuner vs evaluation) when the team reaches it.

## Why this ticket exists (system meaning)

The ladder's thresholds were hand-tuned on one dataset with one goal. The spec flags automating per-dataset
selection as open and publishable. Success is a defensible method and an honest evaluation — "the defaults
are hard to beat" is a valid, evidenced conclusion.

## Grounding (read before starting)

- Spec §8.2 (especially the Very-High purity MUST); W6-03's archived swarm traces.

## Specification

- **S1.** The objective, stated FIRST and reviewed before any algorithm: what "better thresholds" means
  (e.g., maximize band coverage subject to per-band accuracy floors) on a calibration split. The objective is
  the contribution; the search is plumbing.
- **S2.** The tuner: a calibration-split search over threshold/budget configs, consuming W6-03's traces where
  possible (re-thresholding recorded trajectories is far cheaper than re-running swarms — validate that
  shortcut's fidelity first). Hard constraint: Very-High round-1 purity is NOT searchable.
- **S3.** Evaluation on untouched test folds, both datasets: default vs tuned — per-band accuracy/coverage,
  the objective value, calibration curves. Improvement or its absence reported with equal rigor.

## Forbidden shortcuts

- Tuning on test; relaxing VH purity; a grid search dressed as a method (the objective definition and the
  trace-fidelity argument are the research).

## Test requirements

1. Trace fidelity: re-thresholded trajectories reproduce W6-03's live band assignments on the default config
   exactly.
2. Constraint: tuner outputs violating VH purity are structurally impossible.
3. Split hygiene: calibration/test separation (leakage-guard pattern).
4. (slow) Default-vs-tuned tables + calibration curves, 10 seeds, both datasets.

## Acceptance criteria

- A stated objective, a purity-respecting tuner, an honest evaluation — positive or negative — written up
  for W8-06.
