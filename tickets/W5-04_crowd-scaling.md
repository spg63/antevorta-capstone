# W5-04 — The crowd-scaling run: 26 agents vs the matched five (experiment)

**Wave:** W5. **Blocked by:** W5-02. **Blocks:** W5-05.
**Binding spec sections:** §9.2 ("unique agents help"), §9.3 (the 26-agent composition), §9.1.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The "many, many agents" claim, quantified: the maximal 26-agent composition should beat the deliberately
constrained 5-agent matched config. Tiny ticket — one config, one comparison — kept separate so the matched
comparison (W5-02) stays a clean reproduction of the published protocol.

## Grounding (read before starting)

- Spec §9.3's 26-agent mix (one 5-feature, five 4-feature, ten 3-feature, ten 2-feature); W2-03's named
  composition config.

## Specification

- **S1.** The 26-agent config on all five features, trust-weighted aggregation, 10 seeded runs, same splits
  as W5-02; compared against W5-02's 5-agent result in the manifest.

## Forbidden shortcuts

- Hand-tweaking the roster to force the ordering; different splits than W5-02.

## Test requirements

1. (slow) 26-agent mean ≥ 5-agent matched mean on 10-run means; both numbers + the delta manifest-recorded.

## Acceptance criteria

- The scaling claim reproduced (or its failure escalated with the manifest).
