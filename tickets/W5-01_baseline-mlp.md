# W5-01 — The monolithic MLP baseline

**Wave:** W5. **Blocked by:** W1-05. **Blocks:** W5-02, W7-03.
**Binding spec sections:** §9.1 (baseline MLP spec — normative), §9.2 (its published optima).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full. Mini-plan before code.

## Why this ticket exists (system meaning)

Every WoC-Bots claim in Q1 is relative to this model. It must be the PUBLISHED comparison target — a single
hidden layer over all features — not the best network the team can build; a tuned deep baseline is a different
(Phase 2) comparison and putting it here would silently move the goalposts of every reproduction number
(spec §9.1's explicit warning).

## Grounding (read before starting)

- Spec §9.1's baseline block; §9.2's crowd-comparison numbers (MLP optimum 76.8% at 40 epochs; the 5/50-epoch
  protocol).

## Specification

### S1. The model

All available features (never `revenue`); ONE hidden layer, width ~2× input count (MAY tune, document);
Adam 0.001, cross-entropy, batch 32; same W1-03 normalization and splits as the agents; seeded via the
harness.

### S2. The experiment

Train/evaluate at 5 and 50 epochs (10 seeded runs, mean ± std) on the standard split; additionally sweep
epochs 1–50 at the 5-feature configuration (budget, vote_count, vote_average, runtime, popularity) — the
curve W5-02 compares against WoC-Bots' (spec §9.2: MLP optimum ≈ 76.8% at ~40 epochs).

### S3. Feature-removal variants

Config-driven feature subsets for W5-02's robustness contrasts: all-features, minus `vote_count`, minus
`runtime` (spec §9.2's two published contrasts).

## Forbidden shortcuts

- Architecture search, early stopping, dropout, schedulers — none of it; the baseline is the published shape.
- A different normalization or split than the agents see.

## Test requirements

1. Shape pin: n features → one hidden layer of round(2n) units; revenue structurally absent.
2. Determinism: same config + seed → identical metrics.
3. Integration (slow): 50-epoch all-features accuracy in the mid-70s band (76.8% ± 3); the 1–50 curve's
   optimum lands in the 35–50 epoch region.

## Acceptance criteria

- Baseline runs from config through the standard harness; epoch curve + removal variants manifest-recorded;
  optimum in the published band.
