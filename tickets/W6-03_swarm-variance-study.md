# W6-03 — The variance study: swarm vs WVM, band calibration (experiment)

**Wave:** W6. **Blocked by:** W6-02. **Blocks:** W7-04, W8-03, W8-05.
**Binding spec sections:** §8.2 (the published claims and reference shape), §9.1 (fixed folds).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The swarm's two published claims, demonstrated on Hollywood data: lower variance than the WVM across folds,
and confidence bands monotone in accuracy. The reference numbers are breast-cancer-derived (VH 100% > High
93.1% > Medium 82.3% > Low 64.7%; accuracy σ² 2.3 vs 24.5), so the SHAPE is the target, not the values.

## Grounding (read before starting)

- Spec §8.2's reference-behavior paragraph; W1-05's 5-fold artifacts; W6-02's swarm trace.

## Specification

- **S1.** Fixed 5-fold splits, identical crowds and seeds: WVM vs swarm. Report per-fold accuracy/precision/
  recall, cross-fold variance for both, per-band accuracy + coverage for the swarm.
- **S2.** Band stability: tier-distribution variance across 5 re-seeded simulations.
- **S3.** The "drop Low band" analysis (the spec §8.2 pattern): overall accuracy after excluding Low-band
  predictions, with retained coverage.

## Forbidden shortcuts

- Comparing on different folds/crowds; single-seed variance claims.

## Test requirements

1. (slow) Variance ordering: swarm cross-fold variance < WVM's; bands monotone in accuracy; full band table
   in the manifest.
2. The drop-Low computation pinned on a synthetic fixture.

## Acceptance criteria

- Both published claims land in shape on Hollywood, manifest-recorded; swarm trace archived for W8-05. W6
  wave complete.
