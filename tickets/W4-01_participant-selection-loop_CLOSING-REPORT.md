# W4-01 — Participant selection loop + arena integration — CLOSING REPORT

**Ticket:** [`W4-01_participant-selection-loop.md`](./W4-01_participant-selection-loop.md)  
**Addendum:** [`W4-01_participant-selection-loop_ARENA-INTEGRATION.md`](./W4-01_participant-selection-loop_ARENA-INTEGRATION.md)  
**Implementer:** Manan Patel  
**Branch:** `manan/w4-01-arena-integration`  
**Date:** 2026-08-28

## Touched paths (project-root-relative)

**New**

- `src/wocbots/experiments/arena_interaction.py`
- `tests/unit/test_w4_01_arena_integration.py`

**Modified**

- `src/wocbots/experiments/lifecycle.py` — arena sample id + history back-fill
- `src/wocbots/experiments/evaluation.py` — default arena runner + mechanism-comparison back-fill
- `src/wocbots/interaction/encounter.py` — trust update ordered before scoring, so §6.5 doAgree reads encounter-time predictions (post-scoring-flip safe) without breaking the `InteractionPolicy` seam

**Pre-existing on `develop` (consumed)**

- W4-01 lifecycle scaffold + synthetic anchor (PR #17)
- W3-01..04 arena + interaction kernel (PR #32, #33)

## Definition of Done

| Criterion | Status |
|-----------|--------|
| S1 — Participant selection / sit-out | ✅ (PR #17) |
| S2 — Per-sample loop, certainty reset, arena + interactions | ✅ (this branch) |
| S3 — Synthetic anchor ~100% | ✅ (PR #17) |
| Test req 1 — reset semantics | ✅ |
| Test req 2 — sit-out / round count | ✅ |
| Test req 3 — participation manifest | ✅ |
| Test req 4 — synthetic anchor stable | ✅ |
| Independent review (preamble §8) | ☐ pending |
| PR merged to `develop` | ☐ pending |

## Check suite

```
pytest tests/unit/test_w4_01_*.py tests/unit/test_w4_03_aggregators.py tests/unit/test_w4_04_*.py -m "not slow"
```

## Notes

Branch is rebased on current `develop` with W4-01-only delta (no duplicate W3 interaction files). Wave W4 closes for CORE once this PR merges and §8 review lands.
