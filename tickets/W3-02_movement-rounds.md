# W3-02 — Manhattan movement, anti-clique rules, and the lockstep round engine

**Wave:** W3. **Blocked by:** W3-01. **Blocks:** W3-03 (encounters feed it), W4-01.
**Binding spec sections:** §6.3 (movement), §6.4 (iteration count), §10.3 (ordering artifacts).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The information-dispersal engine: randomized local movement with anti-clique rules preventing pair echo
chambers, run in lockstep rounds. The easiest place in the project to bake in ordering artifacts that
surface later as irreproducible crowd behavior — hence the shuffle proof in the tests.

## Grounding (read before starting)

- Spec §6.3–6.4, §10.3.

## Specification

- **S1.** Reference `MovementPolicy`: one random cardinal step in bounds; onto a 1-occupant cell = encounter;
  2-occupant cells unenterable. Anti-clique: no same-pair encounters twice in a row nor more than twice in
  any 5-round window; blocked agents teleport to a random empty cell; stirring teleport ~5% per agent-round
  (named MAY-tune constant).
- **S2.** Round engine: lockstep; per-round SHUFFLED agent processing order (spec §10.3); all encounters
  resolve before the next round; round count `max(10, round(0.10 × N))` computed per sample. Emits an
  encounter log (round, pair, cell) — W3-03's input and the debugging instrument.

## Forbidden shortcuts

- Fixed iteration order; interaction/scoring logic in the arena (this ticket produces ENCOUNTERS, only).

## Test requirements

1. Anti-clique both-sides: pair meets round r → cannot meet r+1 (forced-geometry fixture); third meeting in
   a 5-round window prevented; blocked agent demonstrably teleports.
2. Round-count pins: N = 5 → 10; N = 120 → 12.
3. Shuffle proof: processing order differs across rounds under a fixed seed, and is itself seed-deterministic.
4. Encounter-log completeness: every 2-agent co-location appears exactly once per round.

## Acceptance criteria

- Arena + movement run standalone, seeded; encounter statistics (encounters/agent/round) recorded in the test
  manifest for tuning reference.
