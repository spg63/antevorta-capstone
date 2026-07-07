# W4-04 — Vote-margin confidence tiers + the mechanism-comparison experiment

**Wave:** W4. **Blocked by:** W4-02, W4-03. **Blocks:** W5-02.
**Binding spec sections:** §7 (tiers), §9.1 (protocol).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

Two small deliverables that complete Phase 1's aggregation story: the vote-margin confidence tiers (the cheap
precursor to W6's ladder), and the experiment showing mechanism 3 > 2 > 1 — which doubles as the integration
test of the trust dynamics. If 3 doesn't win, W3-04's plumbing is broken somewhere unit pins can't see.

## Grounding (read before starting)

- Spec §7's tier boundaries; the same-state rule from W4-03.

## Specification

- **S1.** Tiers: `margin = max(votes_0, votes_1)/total`; buckets ≥95 near-certain / 90–95 very high /
  75–90 high / 65–75 medium / 52–65 low / <52 coin-flip; boundary ownership documented. Filled into the
  `Prediction.tier`/`margin` fields per prediction.
- **S2.** The comparison experiment: one config, fixed split, all three aggregators over IDENTICAL per-sample
  runs (same seeds, same arenas), 10 runs; accuracy/precision/recall per mechanism + per-tier accuracy and
  coverage for mechanism 3.

## Forbidden shortcuts

- Re-running arenas per mechanism; reporting single-run orderings.

## Test requirements

1. Tier boundaries both-sides: margins 0.949/0.951, 0.899/0.901, 0.749/0.751, 0.649/0.651, 0.519/0.521 land
   correctly.
2. Integration (slow, Hollywood): mechanism 3 ≥ 2 ≥ 1 on 10-run means — a violation fails the test and
   indicts the trust plumbing.
3. Manifest: the full comparison regenerates from one config.

## Acceptance criteria

- Tiers reported per prediction; the 3 > 2 > 1 ordering reproduced and manifest-recorded. W4 wave complete.
