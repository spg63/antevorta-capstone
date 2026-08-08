# W4-04 — Vote-margin tiers + mechanism-comparison — CLOSING REPORT

**Ticket:** [`W4-04_tiers-mechanism-comparison.md`](./W4-04_tiers-mechanism-comparison.md)  
**Plan:** [`W4-04_tiers-mechanism-comparison_PLAN.md`](./W4-04_tiers-mechanism-comparison_PLAN.md)  
**Implementer:** Manan Patel (AI-assisted)  
**Branch:** `manan/w4-04-tiers-mechanism-comparison`  
**Date:** 2026-08-08

## Touched paths (project-root-relative)

**New**

- `src/wocbots/aggregation/tiers.py`
- `src/wocbots/experiments/evaluation.py`
- `src/wocbots/experiments/mechanism_comparison.py`
- `src/wocbots/experiments/synthetic_anchor.py`
- `configs/mechanism_comparison.yaml`
- `configs/synthetic_anchor.yaml`
- `tests/unit/test_w4_04_tiers.py`
- `tests/unit/test_w4_04_mechanism_comparison.py`
- `tests/unit/test_w4_01_synthetic_anchor.py`
- `tests/unit/test_w4_01_synthetic_anchor_manifest.py`

**Modified**

- `src/wocbots/aggregation/voting.py` — tier/margin on predictions
- `src/wocbots/aggregation/__init__.py`
- `src/wocbots/experiments/lifecycle.py` — degenerate margin
- `src/wocbots/experiments/harness.py` — register new kinds
- `tests/unit/test_w4_01_lifecycle.py` — degenerate + back-fill hook
- `tests/unit/test_w4_03_aggregators.py` — tier/margin assertions

**Process docs (this session)**

- `docs/BRANCHING.md`
- `README.md` — develop workflow
- `.github/pull_request_template.md` — develop target + checklist

## Definition of Done

| Criterion | Status |
|-----------|--------|
| S1 — Tiers on `Prediction.tier` / `margin` | ✅ |
| S2 — Mechanism comparison experiment, identical runs, 10-run manifest | ✅ |
| Test req 1 — tier boundary pins | ✅ |
| Test req 2 — 3 ≥ 2 ≥ 1 ordering (`@slow`) | ✅ |
| Test req 3 — manifest from one config | ✅ |
| W4-01 anchor + participation manifest (same branch) | ✅ |
| Independent review (preamble §8) | ☐ pending |
| PR merged to `develop` | ☐ pending (awaiting Manan) |

## Check suite

```
python -m ruff check .          -> All checks passed!
python -m mypy src tests        -> Success (after Literal cast fix)
pytest -m "not slow"            -> 190 passed (local, 2026-08-08)
```

CI fixes on branch: ruff import order (`db5fa4d`), mypy Literal assignment (`2c19b25`).

## Results manifest

Experiment kinds produce manifests via harness:

- `configs/mechanism_comparison.yaml` — `kind: mechanism_comparison`
- `configs/synthetic_anchor.yaml` — `kind: synthetic_anchor`

Run: `uv run python -m wocbots.experiments.harness configs/mechanism_comparison.yaml`

## Known limitations

- Lifecycle still uses `NoOpInteractionRunner` until W3-02/04 land (W4-01 full arena integration).
- History back-fill hook is stub-tested; W3-04 store not wired.

## Status

**Implemented, CI expected green, pending independent review and manual merge to `develop`.**
