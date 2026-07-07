# W8-04 — The federated meta-swarm experiment

**Wave:** W8. **Blocked by:** W7-03, W8-03. **Blocks:** W8-06.
**Binding spec sections:** §1 (collaboration-without-data-sharing), §9.1.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The dissertation's institutions-that-can't-share-data story, quantified: disjoint-shard external sources
swarmed together vs each alone vs a pooled monolith. The second paper-grade result, and the payoff of
W8-03's boundary discipline.

## Grounding (read before starting)

- W8-03's external agent; W7-03's trained baselines (the external sources — they already exist).

## Specification

- **S1.** Heterogeneous crowds, both datasets, 10 seeds: (a) all-native vs mixed vs all-external accuracy
  under swarm aggregation, with external agents wrapping W7-03's XGBoost/RF/logreg; (b) the federated arm —
  three external sources each trained on a DISJOINT train shard, swarmed together, vs each shard-model alone
  vs one monolith on the pooled data (identically preprocessed); (c) trust dynamics — do native agents learn
  to trust a strong external source (integration curves, the W8-02 pattern)?

## Forbidden shortcuts

- A pooled arm preprocessed differently from the shards; shard "leakage" through shared normalization
  statistics (each source normalizes on ITS shard — that's the realism).

## Test requirements

1. Shard hygiene: disjointness asserted; per-shard normalization structural.
2. (slow) All three sub-experiments complete; the swarmed-vs-alone-vs-pooled gaps and trust curves in the
   manifest.

## Acceptance criteria

- The collaboration-without-sharing claim quantified on both datasets; written up for W8-06.
