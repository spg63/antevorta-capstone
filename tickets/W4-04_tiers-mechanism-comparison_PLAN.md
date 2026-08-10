# W4-04 — Vote-margin tiers + mechanism-comparison experiment — IMPLEMENTATION PLAN

> **STATUS: IMPLEMENTED, PENDING INDEPENDENT REVIEW**
>
> **About this plan.** Per-ticket execution plan for
> [`W4-04_tiers-mechanism-comparison.md`](./W4-04_tiers-mechanism-comparison.md).

**Ticket:** [`W4-04_tiers-mechanism-comparison.md`](./W4-04_tiers-mechanism-comparison.md)

**Precedence:** spec > this plan > ticket

**Wave:** W4 (CORE)

**Blocked by:** W4-02, W4-03 (merged on `develop` via PR #17)

**Blocks:** W5-02

**Binding spec sections:** §7 (tiers), §9.1 (protocol)

**Binding preamble:** [`01_MANDATORY_PREAMBLE.md`](./01_MANDATORY_PREAMBLE.md)

---

## 1. Why this ticket exists

Complete Phase 1 voting: vote-margin confidence tiers on every aggregated prediction, plus the experiment proving mechanism 3 ≥ 2 ≥ 1 on identical per-sample runs (integration test of trust-weight plumbing).

---

## 2. Decisions

- **D1 — Tier module location:** `src/wocbots/aggregation/tiers.py` (alongside W4-03 voting). Boundary ownership documented in module docstring (lower bound inclusive except top bucket).

- **D2 — Fill tier/margin in `VoteOutcome.to_prediction()`:** W4-03 left `tier`/`margin` as `None`; W4-04 fills them at the aggregator seam. Degenerate path (`N < 3`) keeps tier `"low"` (W4-02/W6-02 convention) but records margin from certainty-weighted tally.

- **D3 — Same-state mechanism comparison:** `run_mechanism_comparison()` runs infer + arena once per sample, then aggregates with UWM/WVM/trust on the **frozen** participant snapshot. Forbidden shortcut avoided: no re-running arena per mechanism.

- **D4 — Stable manifest tier keys:** Every run emits all six tier metric keys (`trust_tier_*_accuracy/coverage`); unused tiers → `0.0`. Prevents harness aggregation `KeyError` when different runs hit different buckets.

- **D5 — Per-sample participation in manifest:** `participant_count_s000` … `participant_count_sNNN` plus min/max/mean (W4-01 test req 3). Fixed `n_test` in config keeps keys stable across runs.

- **D6 — Synthetic anchor as harness kind:** W4-01 permanent canary registered as `synthetic_anchor` experiment kind + `configs/synthetic_anchor.yaml` (spec §11).

- **D7 — Arena stub retained:** W3-02/03/04 not landed; lifecycle uses `NoOpInteractionRunner`. Mechanism ordering test validates trust-weight vs prior_accuracy divergence under feedback, not full arena trust dynamics — full integration deferred to W3-04 + lifecycle wiring.

---

## 3. Deliverables

| Path | Purpose |
|------|---------|
| `src/wocbots/aggregation/tiers.py` | Margin + tier buckets |
| `src/wocbots/experiments/evaluation.py` | `run_test_set`, `run_mechanism_comparison`, manifest flatteners |
| `src/wocbots/experiments/mechanism_comparison.py` | Harness kind `mechanism_comparison` |
| `src/wocbots/experiments/synthetic_anchor.py` | Harness kind `synthetic_anchor` |
| `configs/mechanism_comparison.yaml` | 10-run comparison config |
| `configs/synthetic_anchor.yaml` | Anchor canary config |
| `tests/unit/test_w4_04_tiers.py` | Boundary pins |
| `tests/unit/test_w4_04_mechanism_comparison.py` | Manifest + ordering (slow) |
| `tests/unit/test_w4_01_synthetic_anchor*.py` | Anchor + participation manifest |

---

## 4. Test plan

1. Tier boundaries both-sides (0.949/0.951, …) — `test_w4_04_tiers.py`
2. Mechanism 3 ≥ 2 ≥ 1 on 10-run means — `test_mechanism_ordering_trust_ge_wvm_ge_uwm` (`@slow`)
3. Full comparison manifest from one config — `test_mechanism_comparison_manifest_from_one_config` (`@slow`)
4. Synthetic anchor ≥99% × 10 runs — `test_synthetic_anchor_reaches_near_perfect_accuracy` (`@slow`)

---

## 5. Out of scope (explicit)

- Real W3 arena in lifecycle (W3-02/04)
- W3-04 history store back-fill (hook tested with stub only)
- Hollywood ETL / real-data runs (W1-05)
