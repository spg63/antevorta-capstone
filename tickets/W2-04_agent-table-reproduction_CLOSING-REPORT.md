# W2-04 — The §9.2 agent-table reproduction — CLOSING REPORT

**Ticket:** [`W2-04_agent-table-reproduction.md`](./W2-04_agent-table-reproduction.md)
**Plan:** [`W2-04_agent-table-reproduction_PLAN.md`](./W2-04_agent-table-reproduction_PLAN.md)
**Implementer:** Claude session driven by Rutvij (this identity matters for preamble §8 — see §7)
**Date:** 2026-08-10 · **Base:** `develop` @ `4bb6804`

> **OUTCOME: implemented, runs clean, and the reproduction MISSES its bands.** That is a
> reportable result, not a failure to finish: the ticket is written as a detector
> ("if it misses, the bug is upstream and this ticket is the detector, not the fix") and its
> acceptance criteria route persistent out-of-band rows to escalation with the manifest.
> The escalation is `results/W2-04_agent_table_comparison.md`. **No band, ordering, or
> published value was adjusted to make anything land.**

## 1. Touched paths (project-root-relative)

- `src/wocbots/experiments/agent_table.py` (new) — `AgentTableRow`, `AGENT_TABLE_ROWS` (the ten §9.2 rows), `agent_table_runner`, `emit_comparison_table`; registers kind `w2_04_agent_table`
- `src/wocbots/experiments/hollywood_data.py` (new) — `load_labeled_hollywood`, `materialize_split`. Extracted from this runner during W2-03's real-data closure so both tickets read the dataset through one path; it owns the eval-slice (§10.5) and TRAIN-only revenue-scaling contracts described in §5.
- `src/wocbots/experiments/harness.py` (edited — one import line, so the kind registers at harness import, matching the existing `mechanism_comparison` / `synthetic_anchor` pattern)
- `configs/w2_04_agent_table.yaml` (new)
- `tests/unit/test_w2_04_agent_table.py` (new — 12 tests: 10 fast, 2 slow `xfail(strict=True)`)
- `results/manifests/w2_04_agent_table_20260810T154449Z_4bb68043.json` (new — the evidence)
- `results/W2-04_agent_table_comparison.md` (new — published vs measured vs delta + the prose deviation write-up)
- `tickets/W2-04_agent-table-reproduction_PLAN.md` (new)
- `tickets/00_INDEX.md` (edited — v1.16 entry; W2-01..04 status marks)
- `tickets/W2-01_agent-state-profile_PLAN.md`, `tickets/W2-02_classifier-train-eval-prune_CLOSING-REPORT.md`, `tickets/W2-03_feature-assignment-crowd_CLOSING-REPORT.md` (new to the repo — governance backfill, see §6)
- `AGENT_HANDOFF.md` (edited)

**Not touched:** `src/wocbots/agents/` — this ticket configures W2-02/W2-03, it does not modify them (the ticket's forbidden shortcut: "tuning W2-02 internals from inside this ticket"). No `data/` code. No existing config or manifest.

## 2. Check suite

```
uv run ruff check .          -> All checks passed!
uv run ruff format --check . -> all files already formatted
uv run mypy src tests        -> Success: no issues found in 69 source files
uv run pytest tests/unit/test_w2_04_agent_table.py  -> 10 passed, 2 xfailed
```

The two xfails are `strict=True` and deliberate — see §4.

## 3. Mapping to the ticket's requirements

| Ticket item | Where | State |
|---|---|---|
| **S1** ten feature sets as an explicit roster, 5 AND 50 epochs, 10 seeded runs, mean ± std per cell | `AGENT_TABLE_ROWS` × `EPOCH_COLUMNS`; `n_runs: 10`; harness `_aggregate` | ✅ 20 cells, mean + population std |
| **S2** manifest table beside published values, per-row deltas, deviations investigated in prose | `emit_comparison_table` → `results/W2-04_agent_table_comparison.md` §D0–D4 | ✅ |
| **Test req 1** ±3 pts at 50 epochs; three orderings | `test_agent_table_reproduces_published_bands`, `test_orderings_preserved` | ⚠️ assert the ticket's real bands; **currently xfail** — 4 rows miss, 1 ordering breaks |
| **Test req 2** manifest completeness — every cell traces to config + seed + SHA | `test_manifest_completeness` | ✅ |
| **Forbidden:** cherry-picked seeds | one master seed → `SeedSequence.spawn(10)`; no seed selection anywhere | ✅ |
| **Forbidden:** skipping the 5-epoch column | both columns in one manifest (plan §3-D2) | ✅ |
| **Forbidden:** tuning W2-02 internals | `agents/` untouched; the 5-epoch anomaly is filed upstream, not patched | ✅ |

## 4. Results, in one paragraph

The `budget+revenue` canary reaches **97.33% ± 1.71 at 50 epochs**, inside the ±3 band. By
spec §9.2's own instrument ("MUST hit ~100% … if it doesn't, your data pipeline is broken"),
**the data pipeline is validated.** Six of ten rows land inside ±3 at 50 epochs. Four miss,
and they are exactly the rows built on the *combined* MovieLens+TMDb vote features
(`vote_average` / `vote_count`, spec §4.3.4–5) — the family that depends on the side of the
join the open W1-04 escalation is about. Two of three required orderings hold (canary tops
the table; `budget+runtime` is the worst real agent); the third breaks, and it is again a
combined-vote row. The entire 5-epoch column is under-trained: three rows sit at exactly
55.97% ± 0.00, the majority-class rate with zero variance across ten seeds — a constant
predictor. Full analysis, with the mechanism and what it does and does not prove, is in
`results/W2-04_agent_table_comparison.md`.

The two slow tests carry `xfail(strict=True)` naming W1-04 as the blocker. `strict=True` is
load-bearing: if the upstream data is fixed and the table starts landing, the suite goes RED
and forces someone to remove the marker and flip the status honestly, rather than a silent
pass sliding by.

## 5. One real defect found and fixed during implementation — by the canary

`revenue` is structurally excluded from W1-05's feature matrix (§S3), so the runner has to
attach it by hand for the sanity row. The first implementation attached it **unscaled** —
raw dollars (~1e8) beside min-max features in [0, 1]. The canary scored **55.23%** and
correctly reported a broken pipeline: this runner's. Fixed by scaling `revenue` with a
TRAIN-only min-max (the same leakage discipline W1-05 applies to every other column) and
pinned by `test_sanity_row_recovers_a_revenue_defined_label`, which constructs a frame whose
label *is* `revenue > 2 × budget` and requires the canary to clear 0.90. The manifest from
the buggy run was deleted rather than left on disk to be cited.

Recording this because it is the ticket's thesis demonstrated on itself: the canary caught a
real defect that no other row would have revealed.

## 6. Governance backfill done alongside (not part of the ticket's own scope)

W2-01's plan and W2-02/W2-03's closing reports had lived on the implementer's Desktop since
July and were never committed. They are now in `tickets/` under the repo's naming convention.
`00_INDEX.md` carries status marks for W2-01..04 for the first time — all `◐`, none `✅`,
because none has had an implementer-independent review (§7). W2-02 and W2-03 shipped without
separate plan documents; their design rationale lives in their closing reports. That is a
process gap, recorded here rather than papered over with retrospective plans written after
the fact.

## 7. Preamble §6 close checklist — stated explicitly

1. ✅ Check suite green. Skips are named: 10 × "raw data not present locally (expected in CI)" — these PASS locally now that `data/raw/` is populated; 1 × W2-02's W1-05 band check.
2. ✅ Tests land in the same change set as the feature.
3. ✅ Results manifest committed — config + seed + git SHA + 10 per-run records + 20 aggregate cells. **Caveat:** its `git_sha` carries `+dirty` because the code was uncommitted when the run happened (AI sessions do not commit). Re-run once from the committed tree so the manifest cites a clean SHA before this ticket closes.
4. ⚠️ Status flipped in `00_INDEX.md` to `◐ implemented, OUT OF BAND — escalated`, which is the honest state. **Not `✅`.** Spec discrepancies found → reported in the comparison artifact, not reconciled.
5. ✅ This ticket has no RESULT block. W1-04's and W1-06's remain blank and remain the DATA stream's to fill — flagged in the escalation, deliberately not filled by this ticket.
6. ✅ Touched paths listed above, project-root-relative.
7. ⚠️ Nothing on `main`. PR onto `develop`, labelled with the ticket number, linked to Issue #7 — **owed by the human; AI sessions do not commit or push.**
8. ❌ **Independent review NOT done.** Rutvij drove this session, so Rutvij is the implementer and cannot sign it off. A fresh Claude session is explicitly not independent either. Reviewer must be CORE (consumer-reviews-producer per the index) or a different AI system.
9. ✅ `AGENT_HANDOFF.md` updated — old CURRENT STATE demoted to PRIOR, fresh five-part entry, header refreshed.

## 8. For the reviewer — where to look hardest

- **`_accuracy_for_row` / the sanity path.** Confirm `build_sanity_agent` is the only route by which `revenue` reaches a classifier, and that `train_agent`'s leak guard still makes a revenue-seeing crowd agent unconstructible.
- **The revenue scaling in `agent_table_runner`.** It is hand-rolled rather than going through `apply_scaling`, because `revenue` is not in `SplitArtifact.feature_columns`. Check the min/max really are TRAIN-only — this is the exact shape of leak W1-05 exists to prevent, and it is the line that already had one bug.
- **`load_labeled_hollywood`'s `lru_cache`.** Verify that memoising the ETL cannot leak state across runs, and that the SPLIT is genuinely re-derived per run (plan §3-D4 — caching it would fake the std).
- **The `xfail(strict=True)` markers.** Judge whether xfail is the right call versus letting the suite go red now. The argument for xfail is in plan §3-D7; disagreement here is legitimate and worth a finding.
- **Directory ownership.** `experiments/` is CORE's under the one-writer rule and this is an AGENTS-authored file in it (plan §12-R4). Every other experiment kind lives there, so the alternative looked worse — but this needs CORE's sign-off, not mine.

## 9. What Wave 2 still owes after this

| Item | Owner |
|---|---|
| Independent review of W2-01, W2-02, W2-03, W2-04 → then the four index flips to ✅ | CORE / a different AI system |
| Re-run the harness from a committed tree so the manifest cites a clean SHA | whoever commits |
| PR onto `develop`, labelled, linked to Issue #7 | Rutvij |
| **W1-04 gate ruling + W1-06 RESULT block + an `antevorta-db` artifact** | DATA stream / stakeholder — **this is what actually blocks W2-04 from ✅** |
