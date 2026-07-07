# W2-03 — Feature-assignment policy and the crowd builder

**Wave:** W2. **Blocked by:** W2-02, W1-06 (the anchor RESULT). **Blocks:** W2-04, W5-02.
**Binding spec sections:** §5.1 (assignment), §9.3 (reference compositions).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

Crowd diversity — the load-bearing wisdom-of-crowds precondition — comes from how features are dealt out.
This ticket makes crowd composition pure configuration: a seeded policy plus explicit rosters, so the §9.2
reproduction (W2-04) and every experiment after it is a config file, not code.

## Grounding (read before starting)

- Spec §5.1 (anchors from W1-06's RESULT; random distribution; duplicates allowed); §9.3 (4–5 agents at 2–3
  features; 11 at 4; 26 at 5 with the 1/5/10/10 mix).

## Specification

- **S1.** Seeded assignment policy behind a seam: every agent gets the anchor set; remaining features dealt
  randomly; duplicates neither limited nor encouraged. Explicit rosters (exact feature sets per agent) also
  expressible — W2-04 needs exact rosters.
- **S2.** Crowd builder: config → roster → N trained/evaluated/initialized/pruned agents (W2-02 machinery) +
  a crowd manifest (per-agent features, eval metrics, pruned list). The §9.3 compositions ship as named
  example configs.

## Forbidden shortcuts

- Assignment entangled with agent internals; the sanity agent constructible through this path.

## Test requirements

1. Invariants: anchors in every agent; only legal features dealt; deterministic under seed.
2. Roster expressiveness: the 26-agent §9.3 mix constructs exactly.
3. Pruning integration: a deliberately-bad agent prunes without disturbing the crowd manifest.

## Acceptance criteria

- Crowd composition is config; named example configs exist; check suite green.
