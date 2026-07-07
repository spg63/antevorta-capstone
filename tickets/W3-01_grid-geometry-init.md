# W3-01 — Arena grid geometry and random initialization

**Wave:** W3. **Blocked by:** W0-02 (pure logic — no data; fully parallel with W1/W2). **Blocks:** W3-02.
**Binding spec sections:** §6.1 (geometry), §6.2 (initialization), §10.7 (per-sample sizing).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The spatial substrate: a grid sized from THIS sample's participants, max two agents per cell, random no-
overlap placement. Small and pure — and the natural first ticket for the ARENA stream to learn the pin-
everything test style on.

## Grounding (read before starting)

- Spec §6.1–6.2, §10.7.

## Specification

- **S1.** `Arena` (replacing the W0-02 stub internals): near-square rectangle per the spec §6.1 v1.2 ruling —
  `rows = floor(sqrt(2N))`, `cols = ceil(2N / rows)` for N participants (capacity ∈ [2N, 2N + rows); density
  ≈ the published 0.5 agents/cell, which drives encounter rates); occupancy ≤ 2; a 2-agent cell is an
  encounter (consumed by W3-02). Constructed per sample — nothing sized at import or experiment scope.
- **S2.** Reference `InitPolicy` (behind the W0-02 seam): uniformly random EMPTY-cell placement, no
  co-location at init.

## Forbidden shortcuts

- Any crowd-sized constant; movement or interaction logic creeping in (W3-02's job).

## Test requirements

1. Geometry pins (spec §6.1 v1.2 formula): N = 5/10/26 → 3×4 (12 cells)/4×5 (20)/7×8 (56); density N/cells
   ∈ [0.4, 0.5] property-tested over N = 3..200; occupancy never exceeds 2 (property test, seeded).
2. Init: no co-location; all placements in bounds; deterministic under seed.
3. Per-sample proof: two consecutive constructions with different N produce independently sized grids.

## Acceptance criteria

- Grid + init run standalone on fake agents, seeded, pinned; check suite green.
