# W7-03 — The comparison baselines: XGBoost, random forest, logistic regression

**Wave:** W7. **Blocked by:** W5-01. **Blocks:** W7-04, W8-04.
**Binding spec sections:** §9.1 (protocol), §12 (Phase-2 comparison scope).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The three mainstream competitors, wrapped behind the same experiment-config interface as the W5-01 MLP so
W7-04's grid can treat all methods identically. Models only — the grid is W7-04. Fairness rules live here
because they're properties of the wrappers, not the grid.

## Grounding (read before starting)

- Spec §9.1; W5-01's config interface (the pattern to match); xgboost/sklearn versions get manifest-pinned.

## Specification

- **S1.** XGBoost, random forest, logistic regression behind the W5-01-style config interface: standard,
  documented configurations; seeded through the harness; same normalization/split artifacts as everything
  else.
- **S2.** The symmetric-tuning rule, encoded in config: any tuning budget applied to a baseline is applied
  identically to WoC-Bots' knobs (anti-strawman AND anti-self-strawman), and every tune is a recorded config
  decision.

## Forbidden shortcuts

- Silently detuned or leaderboard-tuned baselines; per-method preprocessing.

## Test requirements

1. Interface conformance: each model runs from a config through the standard harness to a manifest.
2. Sanity (slow): each baseline beats majority-class clearly on Hollywood; rough expected ordering (logreg ≤
   tree methods) — a violation is a pipeline bug to investigate, not a result.
3. Determinism per model under fixed seed (the plan §12-R3 warning applies to xgboost too — pin threads).

## Acceptance criteria

- Three fair, seeded, config-driven baselines ready for the grid.
