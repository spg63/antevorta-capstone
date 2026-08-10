# W3-02 — Movement, anti-clique rules, lockstep round engine — CLOSING REPORT

**Ticket:** [`W3-02_movement-rounds.md`](./W3-02_movement-rounds.md)
**Plan:** [`W3-02_movement-rounds_PLAN.md`](./W3-02_movement-rounds_PLAN.md)
**Implementer:** Samuel Gauthier (hand-implemented; Claude chat session used
for plan and code review, not implementation)
**Date:** 08/07/26

## Touched paths (project-root-relative)

- `src/wocbots/arena/movement_policy.py` (new) — `RandomMovementPolicy`
- `src/wocbots/arena/round_engine.py` (new) — `RoundEngine`
- `src/wocbots/arena/arena.py` (edited) — `move_to`, `cell`, `agents_at`
  added; `place` extended to track agent→cell (D1)
- `src/wocbots/arena/__init__.py` (edited) — exports `RandomMovementPolicy`,
  `RoundEngine`
- `src/wocbots/experiments/kinds.py` (edited) — `w3_02_movement_smoke` kind
  registered alongside `dummy` (D4)
- `tests/unit/test_movement_policy.py` (new)
- `tests/unit/test_round_engine.py` (new)
- `configs/w3_02_movement_smoke.yaml` (new)
- `results/manifests/w3_02_movement_smoke_20260807T224338Z_34cf4f35.json`
  (new) — committed reference manifest, 5 seeded runs, `n_agents=20`,
  `teleport_rate=0.05`

## Decisions (see plan §3 for full reasoning)

- **D1** `Arena` extended with agent↔cell tracking and movement methods
  (`move_to`, `cell`, `agents_at`) — W3-01's Arena had no way to move an
  already-placed agent.
- **D2** `RandomMovementPolicy` self-infers the current round number by
  detecting when an already-seen agent recurs within a call sequence,
  since the locked `MovementPolicy.move(agent, arena, rng) -> Cell`
  protocol carries no round information and isn't this ticket's to widen.
  A DB-backed shared counter was considered and rejected (no in-process
  boundary to cross; per-move I/O cost on the simulation's hottest loop).
- **D3** `RoundEngine`, not `RandomMovementPolicy`, builds the encounter
  log — derived by diffing `arena.agents_at(cell)` around each move, using
  only information already available to it. Avoids widening the
  `MovementPolicy` protocol a second time.
- **D4** The `w3_02_movement_smoke` runner and its `register_kind(...)`
  call live directly in `src/wocbots/experiments/kinds.py`, not a new
  per-ticket file or `src/wocbots/arena/`. First domain dependency
  (`wocbots.arena`, `wocbots.agents`) `kinds.py` has picked up — flagged
  explicitly in the plan rather than left as a silent diff.

## Check suite

```
uv run ruff check .          -> All checks passed!
uv run ruff format --check . -> 45 files already formatted
uv run mypy src tests        -> Success: no issues found in 45 source files
uv run pytest                -> 150 passed, 1 skipped, 0 failed (12.90s)
```

The 1 skip (`test_w2_02_classifier.py`) is pre-existing, named, and
unrelated to W3-02.

## Results manifest

`results/manifests/w3_02_movement_smoke_20260807T224338Z_34cf4f35.json` —
produced via `wocbots.experiments.harness.run_experiment` against
`configs/w3_02_movement_smoke.yaml` (not hand-written), validated against
the real `Manifest` schema. 5 independent seeded runs, `n_agents=20`,
`teleport_rate=0.05`: `encounters_per_agent_round` mean 0.301, std 0.036.

## Status

Implemented, check suite green, encounter-statistics manifest committed
against the real harness — pending independent review (preamble §8).
