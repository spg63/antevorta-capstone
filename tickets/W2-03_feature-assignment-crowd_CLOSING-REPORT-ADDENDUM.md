# W2-03 — CLOSING REPORT ADDENDUM: real-data closure

**Ticket:** [`W2-03_feature-assignment-crowd.md`](./W2-03_feature-assignment-crowd.md)
**Original report:** [`W2-03_feature-assignment-crowd_CLOSING-REPORT.md`](./W2-03_feature-assignment-crowd_CLOSING-REPORT.md) (2026-07-20, mechanism + synthetic tests)
**This addendum:** 2026-08-10 · Claude session driven by Rutvij · base `develop` @ `4bb6804`

The original report closed W2-03's mechanism: the assignment seam, the crowd builder, the
crowd manifest, and thirty unit tests, all green, merged in PR #16. It could not close one
thing, and said so: the Hollywood crowd configs encoded their columns **provisionally**,
pending the W1 ETL. The ETL has since landed and the raw data is now on disk, so this
addendum closes that gap — and records what it found.

## 1. The defect the real data exposed

Both shipped Hollywood configs named a feature the ETL does not produce:

| Config | Named | W1-03 actually emits |
|---|---|---|
| `configs/crowd_hollywood_5agent.yaml` | `popularity` | `tmdb_popularity` |
| `configs/crowd_hollywood_26agent.yaml` | `popularity` (in `pool`) | `tmdb_popularity` |

Either config raised `KeyError: feature 'popularity' is not in this dataset` on first contact
with real data. **Both §9.2 and §9.3 reference crowds were unbuildable**, and had been since
they were written.

**Why thirty passing tests missed it.** `tests/unit/test_w2_03_crowd.py` builds synthetic
frames whose columns are constructed to match whatever the config under test names. That is
the correct way to test a *mechanism* — the assignment policy really is right — but it makes
the config-vs-reality question structurally untestable: the fixture always agrees with the
config, so a config that agrees with nothing real still passes. This is worth stating
plainly, because the same shape of blind spot will exist for every future dataset config.

## 2. What landed

- **Configs fixed** — `popularity` to `tmdb_popularity` in both files, with a comment recording
  why, so the next reader does not "helpfully" revert it to match the spec's prose.
- **`src/wocbots/experiments/hollywood_data.py`** (new) — one shared path to the real
  train/eval split, so W2-03's crowds and W2-04's agent table read the dataset identically.
  It owns two contracts that are easy to get wrong separately: the eval slice is the
  train-side 90/10 and never the test split (§10.5), and `revenue` is scaled with TRAIN-only
  statistics (W1-05 excludes it from the feature matrix, so callers must attach it by hand —
  and attaching it raw destroyed the §9.2 canary once already).
- **`src/wocbots/experiments/crowd_build.py`** (new) — the `w2_03_hollywood_crowd` experiment
  kind. No new mechanism: `build_crowd` is W2-03's, untouched. Reports roster size, kept vs
  pruned counts, and the crowd's eval-accuracy spread, ten seeded runs, mean ± std.
- **`configs/w2_03_crowd_5agent.yaml`, `configs/w2_03_crowd_26agent.yaml`** (new) — one per
  named crowd, so both policy branches of the §5.1 seam (explicit and seeded) meet real data.
- **`tests/unit/test_w2_03_hollywood_crowd.py`** (new, 9 tests: 6 fast, 3 slow) — see §3.
- **`src/wocbots/experiments/harness.py`** — one import line so the kind registers.

## 3. The test that would have caught this

`test_hollywood_configs_name_only_real_etl_columns` reads the shipped YAML and checks every
feature name against `DEFAULT_FEATURE_COLUMNS` — W1-05's single source of truth for what the
feature matrix can supply. It is **fast and needs no dataset**, so it runs in CI and stays
green permanently, on every future crowd config, not just these two.

It carries its own self-test. `test_the_column_check_catches_a_planted_bad_name` plants the
original defect (`popularity`) in a temp config and requires the check to reject it — the same
reasoning as the W0-04 RNG guard's planted-violation fixture: a guard that cannot catch the
bug it was written for is decoration.

The three `@slow` tests build both crowds on the real split and assert the spec compositions:
§9.2's five agents at sizes `[2,2,2,2,5]`, §9.3's `{5:1, 4:5, 3:10, 2:10}`, `budget` in every
roster (§5.1), `sanity_free` (§10.9), manifest reconciliation, and byte-identical rebuilds
under the same master seed.

**Result: 9 passed in 31.56s.** Both reference crowds construct and train on real Hollywood
data for the first time.

## 4. Measured results — both crowds, real data, 10 seeded runs

`results/manifests/w2_03_crowd_5agent_20260810T160002Z_4bb68043.json` and
`results/manifests/w2_03_crowd_26agent_*.json`. Mean ± population std over 10 runs (spec §9.1);
accuracy is on the train-side eval slice (§10.5).

| | §9.2 five-agent (explicit) | §9.3 26-agent (seeded) |
|---|---:|---:|
| Roster size | 5.00 ± 0.00 | 26.00 ± 0.00 |
| Kept after §5.3 pruning | 5.00 ± 0.00 | 26.00 ± 0.00 |
| **Pruned** | **0.00 ± 0.00** | **0.00 ± 0.00** |
| Crowd mean eval accuracy | 0.6388 ± 0.0171 | 0.6515 ± 0.0202 |
| Weakest agent | 0.5580 ± 0.0038 | 0.5572 ± 0.0121 |
| Strongest agent | 0.7177 ± 0.0249 | 0.7280 ± 0.0220 |

**Zero agents pruned in either crowd, across all twenty builds.** Spec §5.3's cut is
`eval_accuracy < 0.50` and the weakest agent in either configuration sits at ~0.557, so the
feature assignment is producing a crowd where every member carries some signal — which is what
§5.3's log exists to tell you, in the good direction. Roster size and kept count have exactly
zero variance, confirming both policies construct their spec composition deterministically
regardless of which split a seed draws.

These are **composition and agent-quality numbers, not a published-table comparison.** The
§9.2 crowd-level reproduction (76.3% at 20 epochs against the monolithic MLP's 76.8% at 40)
is W5-02's ticket and needs the baseline W5-01 owns; nothing here claims to reproduce it. The
individual-agent spread is consistent with W2-04's ten-row table, including its shortfall
against published values — same data, same upstream escalation.

## 5. Mapping to the ticket's acceptance criteria

| Ticket item | State |
|---|---|
| **S1** seeded policy behind a seam; explicit rosters expressible | ✅ original report; both branches now exercised on real data |
| **S2** crowd builder to trained/evaluated/pruned agents + crowd manifest; §9.3 compositions as named configs | ✅ original report; the named configs now actually *work* |
| **Test req 1** anchors in every agent; only legal features dealt; deterministic under seed | ✅ synthetic (original) **+ real data** (this addendum) |
| **Test req 2** the 26-agent §9.3 mix constructs exactly | ✅ synthetic (original) **+ real data**: `{5:1, 4:5, 3:10, 2:10}` |
| **Test req 3** a bad agent prunes without disturbing the manifest | ✅ original report |
| **AC** crowd composition is config; named configs exist; check suite green | ✅ — and the named configs are now verified against the ETL, which is what "exist" has to mean |

## 6. What is still NOT closed, and why

**W2-03's Blocked-by column reads `W2-02, W1-06`. W1-06 is still unmet.** Its RESULT block in
`tickets/W1-06_anchor-analysis.md` is literally `☐ ____`, so no anchor set has ever been
chosen or ratified. Both configs still anchor on `budget` **provisionally**, on the spec's
word (§5.1).

Measured on this snapshot's train split, `budget` ranks **last of nine** features by
point-biserial correlation with the label (r = 0.0224); `tmdb_vote_count` tops the list
(r = 0.3236). **This addendum does not re-anchor.** Re-anchoring would silently change what
every §9.2/§9.3 crowd means while leaving its labels intact, and the choice belongs to W1-06's
RESULT block and its ruling authority, not to a config edit made downstream.

So W2-03 is **mechanically complete and now verified on real data**, but it merged with an
unmet blocker in the first place and that is still true. Flagged, not resolved.

## 7. Close checklist (preamble §6) — the items this addendum changes

1. ✅ Check suite green: ruff / ruff-format / mypy-strict clean; `test_w2_03_hollywood_crowd.py` 9 passed.
3. ✅ Results manifests committed for both crowd configs (`results/manifests/w2_03_crowd_*`) — config + seed + git SHA + 10 per-run records.
4. ⚠️ `00_INDEX.md` W2-03 row stays `◐`, not `✅` — see item 8.
5. ✅ W2-03 has no RESULT block of its own. W1-06's is blank and remains the DATA stream's; flagged in §6, deliberately not filled here.
8. ❌ **Independent review still not done.** Rutvij drove both the original session and this one. A different team member or a different AI system must sign off. **This addendum makes that review more important, not less** — a defect of exactly this shape survived thirty green tests and a merge.

## 8. For the reviewer

- **The config fix itself.** Confirm `tmdb_popularity` is right and `popularity` was wrong by reading `wocbots.data.hollywood.build_hollywood_features` (it renames TMDb's `popularity` to `tmdb_popularity`), not by trusting this report.
- **`hollywood_data.materialize_split`.** It is now shared by two tickets, so a leak here contaminates both. Check the revenue min/max really are TRAIN-only.
- **Whether the fast column check is broad enough.** It validates against `DEFAULT_FEATURE_COLUMNS`. A config could legitimately want a column outside that list; if so this pin needs widening rather than deleting.
- **§6's non-decision.** Judge whether leaving `budget` as the provisional anchor is right, or whether W2-03 should be blocked outright until W1-06 rules. There is a defensible argument for the stricter reading.
