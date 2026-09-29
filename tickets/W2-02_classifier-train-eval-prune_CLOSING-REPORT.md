# W2-02 — Classifier train/eval/init/prune (+ sanity agent): implementation & close report

**Mode:** IMPLEMENT. **Implementer:** Claude session driven by Rutvij (this identity matters for
preamble §8 review independence — the reviewer must not be this lineage). **Date:** 2026-07-20.
**Ticket:** `tickets/W2-02_classifier-train-eval-prune.md`. **Binding spec:** §5.2, §5.3, §9.2, §10.5, §10.9
(and §2/§5.4 for the state it initializes).

Everything below is left **uncommitted** in the working tree for your review, per your instruction. Nothing
was committed or pushed.

---

## 1. What landed

Two new source modules under `src/wocbots/agents/` and one test module — the sklearn-facing half of the
agent, behind seams, honouring the one-RNG determinism contract.

| File | Purpose | Spec |
|---|---|---|
| `src/wocbots/agents/classifier.py` (new) | Classifier seam (`AgentClassifier` Protocol) + `ClassifierSpec` config + `MLPAgentClassifier` and `LogisticRegressionAgentClassifier` wrappers + `hidden_layer_count`/`hidden_layer_sizes` + `LabeledData`. | §5.2 |
| `src/wocbots/agents/training.py` (new) | `train_agent` (train → eval → initialize W2-01 state), `train_crowd`, `evaluate`, `prune` + `PrunedRecord`/`PruneResult`, `build_sanity_agent`, `TrainedAgent`, `EvalMetrics`, the `LEAKY_FEATURES` barrier. | §5.3, §9.2, §10.5, §10.9 |
| `tests/unit/test_w2_02_classifier.py` (new) | The five ticket test requirements + edges (18 tests). | §4 test discipline |
| `pyproject.toml` (edited) | One named + commented `[[tool.mypy.overrides]]` for untyped `sklearn`/`threadpoolctl`. | W0-01 relaxation rule |

Design notes worth your eye at review:

- **Determinism / the §12-R3 warning is discharged, not wished away.** `fit` draws exactly one integer from
  the harness `Generator` for sklearn's `random_state` (via `rng.integers`, a method call — it does *not* trip
  the W0-04 RNG guard), and every fit/predict runs inside `threadpool_limits(1)`; the logreg solver runs
  `n_jobs=1`. Same feature subset + same Generator state ⇒ bit-identical trained metrics (verified twice, and
  3× for flake).
- **Eval slice, not test split (§10.5).** `train_data` and `eval_data` are separate arguments; the test split
  never enters this module. Leakage would have to be a deliberate act by the caller.
- **The sanity agent is structurally unreachable from the crowd (§10.9).** `train_agent`/`train_crowd` reject
  any leaky feature (`revenue`) — a `ValueError`, tested both entry points. The budget+revenue canary is only
  reachable via the separate `build_sanity_agent`, and it is flagged `is_sanity=True` so aggregation keeps it
  out of reported runs.
- **Public API is via submodules** (`wocbots.agents.classifier`, `wocbots.agents.training`). I deliberately
  did **not** touch `agents/__init__.py` — keeps the branch diff focused and avoids a cross-branch working-tree
  clash during your branch/merge. If the team wants package-level re-exports (like `Agent`), that is a trivial
  one-line follow-up; say the word.

## 2. Check suite — green

Run in a Python-3.10 sandbox venv (the repo targets ≥3.11; a local-only shim backfilled the 3.11 `datetime.UTC`
alias so the existing harness could run — that shim is **not** part of the delivery). mypy was pointed at
`--python-version 3.11` to match `requires-python`.

```
ruff check .            → All checks passed!
ruff format --check .   → all files formatted
mypy --python-version 3.11 src tests → Success: no issues found in 30 source files
pytest                  → 82 passed, 1 skipped   (was 65 before W2-02: +18 tests, 1 slow skip)
```

The one skip is `test_reference_bands_real_data`, `@pytest.mark.slow`, skipped **with a named reason** (the
W1-05 Hollywood eval slice does not exist yet). Independent value-level spot check:

```
ARCH PINS 2/3/10 -> 1 1 3        SIZES 10 features -> (32,32,32)
DETERMINISM identical? True      SYNTHETIC e2e eval_accuracy = 1.0 (>=0.99)
SANITY canary acc = 1.0, is_sanity=True, features=('budget','revenue')
BARRIER: revenue rejected from crowd construction (ValueError)
```

## 3. Mapping to the ticket's five test requirements

1. **Architecture pins** — `test_hidden_layer_count_pins`, `test_hidden_layer_sizes_composition`,
   `test_mlp_architecture_after_fit` (2/3/10 → 1/1/3; 10-feature agent fits to `(32,32,32)`).
2. **Pruning both-sides** — `test_prune_boundary_both_sides` (0.499 pruned / 0.501 kept, pruned **logged** with
   features + accuracy) and `test_prune_keeps_exactly_threshold` (exactly 0.50 kept; the boundary is strict `<`).
3. **Determinism** — `test_training_is_deterministic` (same subset + seed → identical metrics, twice).
4. **Synthetic e2e** — `test_synthetic_agent_reaches_99pct` (one agent ≥ 99% on a separable 2-feature set), plus
   `test_logreg_variant_classifies` (agent internals don't matter).
5. **Real data (slow)** — `test_reference_bands_real_data` marked slow + skipped until W1-05; its guarantee is
   stood up *now* by `test_sanity_agent_is_the_canary` (canary ~100% on synthetic revenue) and
   `test_revenue_barred_from_crowd_construction` (the §10.9 structural barrier).

## 4. Branch recipe (run on your machine, where git is unconstrained)

The working tree is currently on `ars589` with the four W2-02 changes present but uncommitted. You asked to base
off `w2-01-agent-state` and bring the harness in. Because `ars589` (harness) and `w2-01-agent-state` (Agent)
touch **disjoint files**, this is conflict-free:

```bash
# 1. Shelve the delivered W2-02 changes so the tree is clean to branch
git stash push --include-untracked -m "w2-02-delivery"

# 2. Base off w2-01-agent-state, create the ticket branch
git checkout w2-01-agent-state
git checkout -b w2-02-classifier-train-eval

# 3. Bring in the W0-03/04 harness (W2-02 depends on it); disjoint files ⇒ no conflicts
git merge --no-ff ars589 -m "merge: bring W0-03/04 harness under W2-01 for W2-02"

# 4. Restore the W2-02 files on top
git stash pop

# 5. Review, run the gate, then commit
git status && git diff
pytest                      # expect: full suite green, 1 slow test skipped (W1-05)
git add -A && git commit -m "W2-02: classifier train/eval/init/prune + sanity agent (§5.2/5.3/9.2/10.9)"
```

## 5. AGENT_HANDOFF.md — CURRENT STATE to paste (after you branch)

Per close-checklist §6.9, demote the old CURRENT STATE to `## PRIOR (2026-07-16, W0-01/02 on branch)` and add:

```markdown
## CURRENT STATE (2026-07-20, W2-02 implemented on branch, pending review)

- **Done:** W2-02 implemented on `w2-02-classifier-train-eval` (= `w2-01-agent-state` + merge of `ars589`'s
  W0-03/04 harness). Paths: `src/wocbots/agents/classifier.py`, `src/wocbots/agents/training.py`,
  `tests/unit/test_w2_02_classifier.py`, `pyproject.toml` (one named mypy override for untyped
  sklearn/threadpoolctl). Classifier seam + MLP/logreg wrappers (§5.2), train→eval→init→prune (§5.3),
  budget+revenue sanity agent on a barred path (§9.2/§10.9), single-RNG determinism pinned via
  `threadpool_limits(1)` + seed-from-Generator (§12-R3). Check suite green (ruff/mypy-strict/pytest:
  82 passed, 1 slow skip). Implementer: Claude session driven by Rutvij.
- **In flight / blocked:** ticket-close blocked on independent review (§8 — NOT Rutvij or this Claude
  lineage; a teammate or Codex). Real-data test req 5 (§9.2 bands: sanity ~100%, budget+vote_count 75.7±3)
  is `@pytest.mark.slow` + skipped until W1-05 lands the Hollywood eval slice — it then needs a committed
  results manifest.
- **Owner-attention:** (1) Reviewer (consumer-reviews-producer, or Codex): read the full diff vs the ticket,
  check the forbidden-shortcut register against the code, confirm the pins. (2) DATA: W1-05 eval slice
  unblocks the §9.2 band reproduction. (3) `agents/__init__.py` re-exports for the W2-02 public API are an
  optional follow-up (W2-02 uses submodule imports).
- **Next step:** independent review → flip W2-02 in `00_INDEX.md` to `✅ (reviewed: <who>, <date>)` →
  W2-03 / W4-01 unblock.
- **Five-minute test:** `pytest -q` → 82 passed, 1 skipped; `ls src/wocbots/agents` → `__init__.py agent.py
  classifier.py training.py`; `git log w2-01-agent-state..w2-02-classifier-train-eval` non-empty. If any
  fails, this entry is stale — fix it first.
```

## 6. Remaining close-checklist items (yours / a second set of eyes)

- ☐ **Independent review (§8)** — the hard gate. Not this Claude session's lineage and not you-as-implementer;
  a teammate or a different AI (e.g. Codex), findings adjudicated by a human. This is what flips the ticket ✅.
- ☐ **`00_INDEX.md` status flip** with `✅ (reviewed: <who/what>, <date>)` — after review.
- ☐ **Results manifest** — only owed once test req 5 runs on real W1-05 data (the §9.2 bands). Nothing to
  commit before then; there is no reported experiment yet, only unit-level pins.
- ☐ **Commit** the branch (recipe in §4) — humans commit; I left it to you.
- ☑ Tests land with the feature (same change set). ☑ Check suite green. ☑ No spec discrepancy found — the
  ticket said "prediction" for the profile but that is W2-01's surface; W2-02 introduces no §-level conflict.
