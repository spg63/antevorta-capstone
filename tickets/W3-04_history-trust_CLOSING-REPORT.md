# W3-04 — Interaction history store and trust updates — CLOSING REPORT

**Ticket:** [`W3-04_history-trust.md`](./W3-04_history-trust.md)  
**Plan:** [`W3-04_history-trust_PLAN.md`](./W3-04_history-trust_PLAN.md)  
**Implementer:** Samuel Gauthier (AI-assisted)  
**Branch:** `ticket/w3-04`  
**Date:** 2026-08-16  

---

## 1. Touched paths (project-root-relative)

**New**
- `src/wocbots/interaction/history.py` — `HistoryRecord` dataclass and `HistoryStore` (directed records, lookup indices, $b_{percCorrect}$ calculation, backfill hook, and tidy DataFrame export)
- `tests/unit/test_history_trust.py` — 8 unit tests (pinned trust arithmetic, $[0, 1]$ clamp boundaries, cardinality $1 \to 2$ checks, backfill isolation, DataFrame schema, `prior_performance` vs `prior_accuracy` guard)
- `tickets/W3-04_history-trust_PLAN.md` — approved implementation plan
- `tickets/W3-04_history-trust_CLOSING-REPORT.md` — this closing report

**Modified**
- `src/wocbots/interaction/policy.py` — `ReferenceInteractionPolicy` updated with spec §6.5 trust update formula backed by `HistoryStore`
- `src/wocbots/interaction/encounter.py` — `Encounter` updated with optional `history_store`, `sample_id`, and `round_num` parameters for directed record logging
- `src/wocbots/interaction/__init__.py` — exports `HistoryRecord`, `HistoryStore`, `ReferenceInteractionPolicy`, `CertaintyFlipScoringPolicy`, `Encounter`

---

## 2. Key Decisions (cross-referenced to Plan §3)

- **D1 — History Storage & Query Model (`HistoryRecord` & `HistoryStore`):** Defined `HistoryRecord` dataclass and in-memory `HistoryStore` with $O(1)$ lookup indices `(agent, partner)` and `sample_id`. Provides `get_perc_correct()`, `backfill_correctness()`, and `to_dataframe()` returning a tidy pandas DataFrame.
- **D2 — Cardinality Ruling (2026-07-07 Codex Review):** Captured exactly 2 directed records per physical encounter (one per receiving perspective), preserving asymmetric trust perspectives ($a$'s view of $b$ and $b$'s view of $a$).
- **D3 — Trust Update Math & Cold-Start Guard:** Replaced `ReferenceInteractionPolicy.update_trust()` stub with exact formula $b_{trust} += 0.05 \times (b_{percCorrect} \times b_{priorPerf}) \times doAgree$, clamped to $[0.0, 1.0]$. Enforced strict cold-start / unscored interaction guard (no update without scored prior history). Strictly used `prior_performance` (multiplier $[0.7, 1.3]$), avoiding `prior_accuracy`.
- **D4 — `Encounter` Backward Compatibility:** Extended `Encounter` constructor with optional `history_store`, `sample_id`, and `round_num` parameters, logging directed records when present while preserving W3-03 compatibility when `history_store=None`.
- **D5 — Back-Fill Hook Isolation:** Implemented `backfill_correctness(sample_id, ground_truth)` mutating only `ground_truth` and `partner_correct` across matching records without altering interaction metrics or predictions.

---

## 3. Definition of Done & Test Verification

| Requirement | Plan / Test Pin | Status |
| :--- | :--- | :--- |
| **S1 (History Store & Cardinality)** | Directed records per (agent, partner, sample); 1 encounter $\to$ 2 directed rows; queryable & tidy DataFrame | ✅ |
| **S1 (Backfill Hook)** | `backfill_correctness` flips correctness and ground truth without touching other fields | ✅ |
| **S2 (Trust Update Math)** | $b_{trust} += 0.05 \times (b_{percCorrect} \times b_{priorPerf}) \times doAgree$, clamp $[0, 1]$, no update without scored history | ✅ |
| **Test 1 (No-History Guard)** | No-history and un-scored encounter $\to$ no trust update | ✅ |
| **Test 2 (Capped Movement & Clamps)** | $|\Delta trust| \le 0.05$ at priorPerf=1.0; both signs ($+0.05, -0.05$); clamped at $0.0$ and $1.0$ | ✅ |
| **Test 3 (percCorrect Pin)** | Scripted 4-encounter history ($3/4 = 0.75$), priorPerf=1.1, agreement $\to$ trust delta $+0.04125$ ($<1\text{e-}9$) | ✅ |
| **Test 4 (Store Completeness)** | Scripted 5-agent, 2-round arena run $\to$ exactly $2K$ directed history rows from $K$ encounter log entries | ✅ |
| **Test 5 (Back-Fill Isolation)** | Ground truth backfill flips correctness and label, leaves all other fields identical | ✅ |
| **Test 6 (Tidy DataFrame)** | `to_dataframe()` returns valid `pd.DataFrame` with full schema and correct row count | ✅ |
| **Test 7 (Performance Scales Guard)** | Verified trust math reads `prior_performance` and ignores `prior_accuracy` | ✅ |
| **Test 8 (Defensive Inputs)** | Uninitialized agent prediction raises `ValueError`; unknown pair queries return `None` | ✅ |

---

## 4. Check Suite Results

```
uv run ruff check .          -> All checks passed!
uv run ruff format --check . -> 74 files already formatted
uv run mypy src tests        -> Success: no issues found in 74 source files
uv run pytest                -> 226 passed, 11 skipped, 1 xfailed (90.74s)
```

- **Delta:** $+8$ passed tests (from baseline of $218 \rightarrow 226$).
- **Skips/Xfails:** Pre-existing, named, and unrelated to W3-04 ($11$ skipped in data/provenance and classifier slow bands, $1$ xfailed in label class balance).

---

## 5. Results Manifest

**N/A** — Pure interface, data structure, and deterministic arithmetic mechanism ticket; no stochastic experiments or harness runs required.

---

## 6. Forward Commitments & Blast Radius

- **W4-01 (`participant-selection-loop`):** Instantiates `HistoryStore` and passes it to `Encounter(..., history_store=store, sample_id=s, round_num=r)` in the per-sample arena loop; verifies persistence across samples.
- **W4-02 (`ground-truth-feedback`):** Calls `history_store.backfill_correctness(sample_id, true_label)` during Phase 4 ground-truth feedback.
- **W4-03 (`voting-aggregators`):** Consumes accumulated `trust_score` and `prior_accuracy` during vote weighting.

---

## 7. Status

**Implemented & Green.** Ready for independent review sign-off per `01_MANDATORY_PREAMBLE.md` §8.
