# W2-04 — the §9.2 agent-table reproduction: implementation & close report

**Mode:** IMPLEMENT (plus a DIAGNOSE pass on CI). **Implementer:** Claude session driven by Rutvij — this
identity matters for preamble §8 review independence; the reviewer must not be this lineage.
**Date:** 2026-08-03. **Ticket:** `tickets/W2-04_agent-table-reproduction.md`.
**Binding spec:** §9.2 (the ten-row table), §9.1 (protocol), §10.10 (match semantics).
**Base:** `develop` @ `b7bc127`. Left **uncommitted** in the working tree per preamble §6.7 (AI sessions
don't commit or push unless asked).

---

## 0. What changed since the 2026-07-25 BLOCKED note

That note held W2-04 on two blockers. One is gone, one is not:

- **Blocker B (data) — cleared at the code level.** The W1 DATA wave landed in `develop`
  (`8401df0`/`4e0d84d` "Wave 1", then PR #18). `src/wocbots/data/` now has the full pipeline:
  `hollywood.py` (W1-03 ETL), `labels.py` (W1-04), `splits.py` (W1-05 stratified 80/20 + the 90/10 eval
  slice + train-only min-max), `anchor_analysis.py` (W1-06). W2-04 now has real machinery to run against.
- **Blocker A (governance) — unchanged.** `00_INDEX.md` still carries **zero** status flips. W2-03 is merged
  (PR #16) but not `✅ (reviewed: …)`, so by the letter of the index rule W2-04's start gate is still shut.
  I proceeded because you asked for it this session; the flip is still owed and is not mine to write.

Two things are still open **upstream** and they bound what this ticket can conclude — see §6.

---

## 1. First: CI was red on `develop`, and is now green

Independent of the ticket. `develop`'s tip (`b7bc127`) fails the required `checks` job.

**Reproduced exactly** (GitHub Actions run 30731327286, job `checks (3.12)`, step `uv run mypy src tests`;
the `3.11` job was cancelled when 3.12 failed, so it is not a second, separate fault):

```
src/wocbots/data/anchor_analysis.py:11: error: Library stubs not installed for "scipy.stats"
src/wocbots/data/{labels,splits,hollywood,anchor_analysis}.py + tests/unit/data/*: 
    error: Library stubs not installed for "pandas"
Found 11 errors in 10 files
```

**Root cause: dependency drift, not a typing bug.** The W1 code merged without the `pyproject.toml` /
`uv.lock` half of its own change. `anchor_analysis.py` imports `scipy.stats` directly, but `scipy` was never
declared — it arrived transitively through scikit-learn, which is exactly the sort of thing the lockfile rule
(§10.3) exists to make impossible. And `pandas` ships no `py.typed`, so mypy-strict needs `pandas-stubs`,
which was never added. Local runs pass wherever a stale venv still holds the stubs; CI, which builds from the
lockfile, does not — which is why this was invisible on the machines that merged it. (The 2026-07-25 handoff
entry describes making both changes; they did not survive into `develop`.)

**Fix** (`pyproject.toml` + regenerated `uv.lock`):

| Change | Why |
|---|---|
| `scipy>=1.11` added to `[project].dependencies` | a direct import is a direct dependency |
| `pandas-stubs>=2.2` added to the `dev` group | pandas has no `py.typed`; mypy-strict needs stubs |
| `scipy.*` added to the existing `sklearn.*` mypy override | scipy ships no `py.typed`; its stubs are a separate distribution. Named + commented per the O4 relaxation rule, same precedent as sklearn |

**Verified against the CI matrix**, in a lockfile-exact environment (`uv sync --frozen --exact`) on **both**
`3.11` and `3.12`:

```
ruff check .            → All checks passed!
ruff format --check .   → 57 files already formatted
mypy src tests          → Success: no issues found in 57 source files
pytest                  → 208 passed, 12 skipped, 1 xfailed
pytest -m "not slow"    → 207 passed, 10 skipped, 3 deselected, 1 xfailed   (this is the CI invocation)
```

Baseline before this session, same environment: `167 passed, 11 skipped, 1 xfailed`. So +41 tests, +1 skip
(the new slow reproduction).

---

## 2. W2-03: verified, and one real defect fixed

W2-03's code is in `develop` and holds up on re-read against its ticket — assignment returns feature-name
rosters only (decoupled from agent internals), the §10.9 barrier rejects `revenue` at both config validation
and the builder's roster guard, determinism threads through one Generator, the 26-agent mix and prune
integration are pinned. Its 30 tests pass. Nothing there needed changing.

**But one thing had gone stale, and it was load-bearing.** Both Hollywood crowd configs named a column that
does not exist:

```
configs/crowd_hollywood_5agent.yaml   agents: [budget, popularity]        ← no such column
configs/crowd_hollywood_26agent.yaml  pool:   [..., popularity]           ← no such column
```

Spec §9.2's crowd-level prose says "popularity"; W1-03's ETL emits **`tmdb_popularity`** (§4.3.5 combines
only the *vote* columns — there is no combined popularity). W2-03 shipped the spec's prose name explicitly
marked provisional, "pinned by W1-06's anchor RESULT once the Hollywood ETL (W1) lands." W1 has landed, so
this is that resolution, not a new decision.

This is not cosmetic: `LabeledData.select` raises `KeyError` on an unknown column rather than imputing
(spec §3, and rightly so), so both configs would have died at the first real-data run — W5-02's matched
comparison and W5-04's scaling run both consume them.

Fixed in both configs, with `test_hollywood_configs_use_real_etl_columns` added to
`tests/unit/test_w2_03_crowd.py`: every feature name in a Hollywood crowd config must appear in
`wocbots.data.hollywood.OUTPUT_COLUMNS`. A dangling column is now a test failure, not a surprise later.

**Still open on W2-03 and NOT resolved here:** W1-06 owes the finalized *anchor set*. `budget` stands because
spec §5.1 names it ("in practice, budget is the anchor feature every agent gets"), but W1-06's own measured
ranking currently puts `budget` **last**, against §9.2's expectation that it tops the list — and that ranking
is itself provisional because it was computed against an unratified label (see §6). No anchor RESULT was
fabricated. Flagging, not deciding.

---

## 3. W2-04: what landed

| File | Purpose |
|---|---|
| `src/wocbots/experiments/agent_table.py` (new) | The whole ticket: §9.2 as data, the `agent_table` runner, the comparison table |
| `configs/crowd_hollywood_agent_table.yaml` (new) | S1's explicit roster — the nine real §9.2 rows |
| `configs/agent_table_hollywood.yaml` (new) | S1's experiment config: 10 runs, both epoch columns, one master seed |
| `configs/agent_table_smoke.yaml` (new) | The same path on synthetic data, so the machinery is runnable/testable without the datasets |
| `tests/unit/test_w2_04_agent_table.py` (new) | 40 tests: both ticket requirements + the forbidden-shortcut guards |
| `src/wocbots/experiments/kinds.py` (1 line) | Imports `agent_table` so the harness CLI resolves the kind |
| `configs/crowd_hollywood_{5agent,26agent}.yaml`, `tests/unit/test_w2_03_crowd.py` | The W2-03 fix in §2 |
| `pyproject.toml`, `uv.lock` | The CI fix in §1 |

**Not touched:** every W2-02/W2-03 module, and the arena/aggregation/interaction packages. That is deliberate
and it is the ticket's central constraint — W2-04 is a *detector*. If a row misses its band, the bug is
upstream and gets filed there. Nothing in this diff tunes a classifier, a threshold, or an init formula.

### Design points worth the reviewer's eye

- **"Ten rows" is nine agents plus one canary, and that is not a shortcut — it is §10.9.** The roster config
  holds only the nine real rows. `budget+revenue` is built by `training.build_sanity_agent`, on its own path,
  from its own two-column matrix (the only place `revenue` is ever materialised — W1-05 structurally excludes
  it from the feature matrix). A `revenue` in the roster YAML is rejected at load; a test asserts that by
  actually appending it and expecting the `ValidationError`. The canary's *cell* is reported, because §9.2
  asks for it as the pipeline check; the canary never enters a crowd or an aggregation.

- **A pruned row still owes the table a number.** Accuracies are read from the `CrowdManifest` — `agents` **and**
  `pruned` — not from `BuiltCrowd.agents`. An agent below 0.50 is correctly dropped from the usable crowd
  (§5.3), but if it also vanished from the report, a broken row would read as a missing key rather than as a
  bad number. `test_a_pruned_row_still_reports_its_cell` forces every row to prune and asserts all nine still
  report.

- **Seed selection is not expressible.** The runner takes the Generator the harness hands it and never inspects
  or chooses a seed; `run_experiment` spawns ten independent child streams from the config's one master seed.
  "Cherry-picked seeds" would require editing the config, and `test_hollywood_config_is_ten_runs_and_keeps_both_columns`
  pins `n_runs == 10` and `epochs == (5, 50)`.

- **One unit conversion, in one place.** The toolkit measures accuracy in [0, 1]; §9.2 publishes percentage
  points. `build_comparison` is the only place ×100 happens, its fields are named `*_pct`, and
  `test_comparison_arithmetic_is_exact` pins it against a hand-computed cell.

- **Deltas are signed, and a missing cell is an error.** "3 points low" and "3 points high" are different
  findings, so `delta_pct` keeps its sign. A cell absent from the manifest raises rather than rendering blank —
  a table with a hole in it would otherwise read as "in band" by omission.

- **The synthetic path cannot pass the reproduction.** `agent_table_smoke.yaml` runs the full path on an
  invented frame so config → split → train → manifest → comparison is exercised per-commit. It is deliberately
  *not* calibrated to §9.2 (running it produces 18 of 20 cells out of band and a failing canary ordering — the
  detector working). The real reproduction is slow-marked and skips with a named reason when the raw datasets
  are absent, because a detector calibrated on invented data detects nothing.

- **Eval slice only.** Every number comes from W1-05's 90/10 hold-out off the *training* side. The test split
  is not read anywhere in this module (§10.5, forbidden-shortcut #1), and the canary's own scaler is fit on
  train rows only.

## 4. Mapping to the ticket's two test requirements

1. **Reproduction (slow)** — `test_reproduction_hollywood_real_data`: runs the shipped 10-run config, asserts
   every 50-epoch cell within ±3 points, all three §9.2 orderings hold (canary top; `budget+runtime` worst;
   `budget+vote_average+vote_count` best real agent), and the canary ≥ 97%. **Currently skips** — the raw
   datasets are gitignored and absent locally (`data/raw/` does not exist on this machine). It runs the moment
   they are present, and weekly in `scheduled.yml`. The band boundary is pinned on both sides at exactly ±3.0
   by parametrised fast tests, so the tolerance itself is not waiting on data.
2. **Manifest completeness** — `test_every_cell_traces_to_config_seed_and_sha`: from any cell you reach the
   config (name/kind/seed/`n_runs`/params), the master seed, the roster's exact bytes
   (`crowd_config_sha256`, pinned against a real hash by a second test), the git SHA and timestamp from the
   harness provenance, and the manifest file holding the per-run numbers.

Deviation handling (S2) is covered by `test_a_deviation_is_written_up_not_absorbed` and the three ordering
tests: every out-of-band row and every broken ordering produces a prose `notes` line naming the cell, both
numbers, the signed delta, and the instruction to look upstream.

## 5. Close checklist (preamble §6)

1. ☑ Check suite green on both CI Python versions; the 1 new skip has a named reason (raw data absent).
2. ☑ Tests land with the feature, same change set.
3. ☐ **Results manifest — NOT owed yet, and deliberately not faked.** W2-04 is an experiment ticket, so it
   owes a committed manifest — but the experiment cannot run without `data/raw/`. Producing one from the
   synthetic config would be a manifest of a number that means nothing. Run
   `uv run python -m wocbots.experiments.harness configs/agent_table_hollywood.yaml` on a machine with the
   datasets, then commit the manifest plus the rendered comparison table.
4. ☐ `00_INDEX.md` flip — not mine to write (implementer). No spec discrepancy found; §9.2 and the ticket agree.
5. ☑ N/A — W2-04 has no RESULT block.
6. ☑ Touched paths listed in §3, project-root-relative.
7. ☑ Nothing committed or pushed.
8. ☐ **Independent review (§8)** — the hard gate. Not this Claude lineage, not Rutvij-as-implementer: a
   teammate (consumer-reviews-producer) or a different AI system, adjudicated by a human.
9. ☑ `AGENT_HANDOFF.md` updated.

## 6. For the reviewer / the team — what W2-04 cannot conclude yet

The ticket says a miss means the bug is upstream. Two upstream items are **already known to be unresolved**,
so read a future red table against them before suspecting the agent layer:

1. **W1-02 is blocked and W1-04's gate is escalated, not closed.** No `antevorta-db` source or built SQLite has
   been supplied, so the reference table does not exist. The only computable label is variant (a)
   (`revenue > 2*budget`, §4.3.7), whose class balance measures 43.9/56.1 against the spec's published
   47.5/52.5 — outside tolerance. `data/DATA_PROVENANCE.md` §6 root-causes this (not confirmed) to a
   MovieLens `link.csv` snapshot-vintage mismatch: 4,227 matched movies against the reference 4,722.
   **A ~500-movie shortfall and an unratified label are exactly the kind of upstream drift that moves §9.2
   rows.** This is stated in `load_hollywood_frame`'s docstring so it cannot be read past.
2. **W1-06's anchor ranking is provisional** for the same reason — see §2.

If the table comes back red on these, the finding is "W1 is unresolved," not "the agent layer is
miscalibrated." That is the ticket working as specified.

Also worth a ruling, carried forward from the 2026-07-25 note and still unaddressed: PRs #13/#15/#16 were all
merged by the implementer's own driver with no recorded independent reviewer, and W2-03 merged with its
`W1-06` Blocked-by unmet. Until someone confirms who actually reviewed what, no honest `✅ (reviewed: …)` line
can be written for any of them — including this one.

## 7. Branch recipe (run on your machine)

```bash
git switch -c rootwij/w2-04-agent-table develop
git add pyproject.toml uv.lock \
        src/wocbots/experiments/agent_table.py \
        src/wocbots/experiments/kinds.py \
        configs/agent_table_hollywood.yaml \
        configs/agent_table_smoke.yaml \
        configs/crowd_hollywood_agent_table.yaml \
        configs/crowd_hollywood_5agent.yaml \
        configs/crowd_hollywood_26agent.yaml \
        tests/unit/test_w2_04_agent_table.py \
        tests/unit/test_w2_03_crowd.py \
        tickets/W2-04_agent-table-reproduction_CLOSING-REPORT.md \
        AGENT_HANDOFF.md
git status          # confirm README.md is NOT staged — CRLF mount noise, not a change
uv sync --frozen && uv run pytest
git commit -m "W2-04: 9.2 agent-table reproduction + comparison manifest; fix CI mypy dependency drift"
```

`README.md` shows ` M` in `git status`. That is the pre-existing CRLF artifact of the Windows-checkout /
Linux-sandbox mount (`git diff --ignore-cr-at-eol -- README.md` is empty). Do **not** `git add` it.

Consider splitting the CI fix (§1) into its own first commit or PR — it is unrelated to the ticket, it
unblocks everyone else's branches, and it should not wait on W2-04's review.
