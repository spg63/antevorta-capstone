# W7-04 — The full comparison grid (experiment)

**Wave:** W7. **Blocked by:** W6-03, W7-02, W7-03. **Blocks:** W7-06, W8-06.
**Binding spec sections:** §9.1 (5-fold, fixed folds), §4.4 (airline ballpark), §12 (Q2 exit contribution).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The proposal's Phase-2 table: {WoC-Bots trust-weighted, WoC-Bots swarm, MLP, XGBoost, RF, logreg} ×
{Hollywood, airline}. The published thesis is comparable accuracy plus properties the others lack — so the
comparison must be fair by construction (identical folds and preprocessing, structurally asserted), and the
swarm rows carry the per-band columns mainstream methods cannot produce.

## Grounding (read before starting)

- Spec §9.1; the airline mid-90s ballpark; W7-02's scale protocol (it governs the airline runs).

## Specification

- **S1.** One config → the grid over fixed 5-fold splits × 10 seeds: accuracy/precision/recall mean ± std
  per cell, per-fold detail, per-band accuracy/coverage for swarm rows, drop-Low-band accuracy (the W6-03
  computation) as the confidence value-add column.
- **S2.** Analysis notes for the paper: where WoC-Bots sit per dataset; what the bands add; airline WoC-Bots
  vs the published mid-90s.

## Forbidden shortcuts

- Different folds/preprocessing per method; single-seed cells; omitting an unflattering column.

## Test requirements

1. Fairness structural: fold membership and normalization artifacts byte-identical across methods.
2. Regeneration: the full table from one config + seed set (manifest audit).
3. (slow) The grid completes on both datasets under the W7-02 protocol.

## Acceptance criteria

- The table exists, fair by construction, fully regenerable; gaps vs published ballparks analyzed (and
  escalated if material); analysis notes drafted for W8-06.
