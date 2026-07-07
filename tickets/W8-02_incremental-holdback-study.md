# W8-02 — The incremental-feature holdback study (experiment)

**Wave:** W8. **Blocked by:** W8-01. **Blocks:** W8-06.
**Binding spec sections:** §1, §9.2 (feature-addition context), §9.1.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The paper-grade measurement of the injection claim: how much of a full retrain's lift does injection recover,
at what fraction of the cost, and how fast does the crowd learn to listen to the newcomers?

## Grounding (read before starting)

- W8-01's API; W5-02's matched protocol (the base configuration); spec §9.2's feature-addition figure context.

## Specification

- **S1.** Holdback protocol, Hollywood, 10 seeds: train a crowd with feature X held back, for X ∈
  {vote_count, popularity, vote_average}; measure; inject X-bearing agents; measure again on the SAME test
  stream.
- **S2.** Outputs per X: accuracy before/after injection; the injected agents' integration curves (trust and
  prior_accuracy evolution over the stream); wall-clock cost of injection vs retrain-from-scratch at equal
  final feature sets. The comparison table: Δaccuracy(injection) vs Δaccuracy(retrain) vs both costs.

## Forbidden shortcuts

- A retrain arm with different epochs/data than the injection arm's agents; reporting lift without the
  integration curves (speed-of-integration is half the claim).

## Test requirements

1. (slow) All three holdback runs complete, 10 seeds; the lift/cost table and integration curves in the
   manifest.
2. Protocol audit: injection and retrain arms end at identical feature sets (structural).

## Acceptance criteria

- Lift, integration speed, and cost quantified across three features, written up for W8-06 — whatever the
  numbers say.
