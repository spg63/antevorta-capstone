# W2-04 — The §9.2 agent-table reproduction (experiment)

**Wave:** W2. **Blocked by:** W2-03. **Blocks:** W5-05 (Q1 report input).
**Binding spec sections:** §9.2 (the ten-row agent table), §9.1 (protocol), §10.10 (match semantics).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

Ten independently trained classifiers landing in their published bands is the first hard evidence the
data + agent stack is calibrated. Pure experiment ticket: one config, one manifest, one comparison table —
if it misses, the bug is upstream and this ticket is the detector, not the fix.

## Grounding (read before starting)

- Spec §9.2's table — all ten rows, 5 AND 50 epochs (the gap between the columns is part of the signature).

## Specification

- **S1.** A config reproducing the table: the ten listed feature sets as an explicit roster, 5 and 50
  epochs, 10 seeded runs, mean ± std per cell.
- **S2.** Output: a manifest table beside the published values with per-row deltas; deviations investigated
  in prose in the manifest, not absorbed.

## Forbidden shortcuts

- Cherry-picked seeds; skipping the 5-epoch column; tuning W2-02 internals from inside this ticket (a miss
  files a bug upstream).

## Test requirements

1. Reproduction (slow): all ten rows within ±3 points at 50 epochs; orderings preserved (budget+revenue
   ≈ 100 top; budget+runtime worst; budget+vote_average+vote_count best real agent).
2. Manifest completeness: every cell traces to config + seed + SHA.

## Acceptance criteria

- The table regenerates within bands, orderings intact, deltas recorded. Persistent out-of-band rows →
  escalated with the manifest.
