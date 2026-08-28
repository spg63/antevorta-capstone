# W2-04 — The §9.2 agent-table reproduction — IMPLEMENTATION PLAN

> **STATUS: DRAFT — pending independent review (preamble §9 → §10)**

**Ticket:** [`W2-04_agent-table-reproduction.md`](./W2-04_agent-table-reproduction.md)
**Wave:** W2 (AGENTS stream)
**Blocked by:** W2-03 ✅ (merged, PR #16) — and, for meaningful numbers, W1-05 / W1-06 (see §6)
**Blocks:** W5-05 (Q1 report input)
**Binding spec sections:** §9.2 (the ten-row agent table), §9.1 (protocol), §10.10 (match semantics), §10.5 (leakage), §10.9 (sanity agent)
**Binding preamble sections:** §2 (hard rules), §3 (forbidden-shortcut register), §4 (test discipline), §6 (close checklist), §8 (independent review)
**Severity of getting it wrong:** HIGH — this ticket is the calibration detector for the entire agent stack. A reproduction that passes for the wrong reason (tuned seeds, tuned internals, synthetic data) silently blesses a broken pipeline and every W5 number inherits the error.
**Ruling authority:** the spec for method; the stakeholder for any out-of-band row that persists (ticket AC).

---

## 1. Metadata

Re-read in full to write this plan, at `develop` @ `4bb6804`:

- `tickets/W2-04_agent-table-reproduction.md` (the ticket)
- `tickets/01_MANDATORY_PREAMBLE.md` §§2–4, 6, 8–10
- `docs/WoC-Bots_Implementation_Spec.md` §9.1, §9.2, §5.2, §5.3, §10.5, §10.9
- `src/wocbots/agents/classifier.py`, `training.py`, `crowd.py` (W2-02/W2-03, the machinery this ticket configures)
- `src/wocbots/experiments/{config,harness,manifest,registry,kinds}.py` (W0-03/W0-04)
- `src/wocbots/data/{hollywood,labels,splits,anchor_analysis,provenance}.py` (W1)
- `data/DATA_PROVENANCE.md` §5–6 (the open escalation this ticket runs into)

This plan is self-contained: every number it pins is quoted from the spec below, not recalled.

---

## 2. Why this ticket exists

Ten independently trained classifiers landing in their published bands is the first hard
evidence that the data layer and the agent layer are jointly calibrated. Everything after it
— crowd voting, the matched comparison, the Q1 exit — is built on the assumption that a
2-feature agent on this data really does score what the published work says it scores.

This is a **pure experiment ticket**. It adds no mechanism. Its output is one config, one
manifest, and one comparison table. The ticket states its own epistemics plainly: *"if it
misses, the bug is upstream and this ticket is the detector, not the fix."* A detector that
is adjusted until it reads clean is not a detector, which is why §3-D7 below refuses the
obvious temptation.

---

## 3. Decisions

**D1 — Accuracy is measured on the EVAL slice, never the test split.**
W1-05 produces an 80/20 train/test split plus a 90/10 eval slice off the *training* side.
Spec §10.5 and preamble §2 make the test split untouchable until final evaluation (W5).
W2-02's `evaluate()` already reads a caller-supplied eval slice for exactly this reason.
*Rejected:* measuring on the test split. It would burn the holdout for a calibration check
and violate forbidden-shortcut #1. The published table is an agent-quality table, and agent
quality is an eval-slice quantity throughout this codebase.

**D2 — Both epoch columns live in ONE manifest, as separate metric keys.**
The ticket: *"5 AND 50 epochs (the gap between the columns is part of the signature)."* One
metric key per (feature set, epoch count) — twenty keys total — so a single manifest carries
the whole signature and the two columns cannot drift apart across invocations.
*Rejected:* one config/manifest per epoch column. It would let someone regenerate one column
against a different SHA and compare the two halves without noticing.

**D3 — Aggregation is the harness's, not the runner's.**
`ExperimentConfig.n_runs = 10`; `harness._aggregate` already computes mean and population std
per metric across runs, and `SeedSequence(seed).spawn(n_runs)` already gives independent
per-run streams. The runner returns one flat `Mapping[str, float]` per run and nothing else.
*Rejected:* aggregating inside the runner. It would duplicate `_aggregate`, and it would put
the "10 runs, mean ± std" rule (spec §9.1) in two places where it can disagree with itself.

**D4 — The raw-data load is cached across runs; the SPLIT is not.**
`rating.csv` is 20,000,263 rows / 690 MB. Re-running the W1-03 ETL for each of 10 runs costs
minutes per run for a result that is *identical every time* — the ETL is deterministic and
takes no seed. So the labeled dataframe is built once and memoised per process.
The split is re-derived per run from that run's own `rng`, because split membership IS the
stochastic dimension the 10 runs are supposed to sample.
*Rejected:* caching the split too. That would make ten runs of one split — a single run
reported ten times, with a fake std.

**D5 — The sanity agent stays in the table, via its own constructor.**
Row 1 of §9.2 is `budget, revenue` at ~100%. It is built with `build_sanity_agent()` (the
only path allowed to touch `revenue`, spec §10.9) and is reported here because §9.2 lists it
and because pipeline validation is precisely the use §10.9 permits. It never enters a crowd.
*Rejected:* omitting it. The ticket forbids skipping rows, and this row is the one that
distinguishes "the agents are weak" from "the data is broken."

**D6 — The comparison table is DERIVED from the manifest, never typed by hand.**
A function reads a written manifest and emits the markdown table (published | measured |
delta). Hand-transcribing means the report and the evidence can disagree.
*Rejected:* writing the table inside the runner. The table is a view over the aggregate,
which does not exist until all 10 runs are done.

**D7 — The reproduction test asserts the ticket's real bands, and is allowed to FAIL LOUDLY.**
Test requirement 1 is ±3 points at 50 epochs plus three ordering assertions. Given the
unresolved W1-04 label gate (§6 and §12-R1), this assertion is expected to fail on the
current data snapshot. It is written as a real assertion anyway, marked `@pytest.mark.slow`
and `xfail(strict=True)` with a reason naming W1-04 — `strict=True` so that the day the
upstream data is fixed and the table starts passing, the suite goes RED and forces someone to
remove the marker and flip the status honestly.
*Rejected:* (a) loosening the bands to whatever the data currently produces — that is
forbidden-shortcut territory and destroys the detector; (b) deleting the test until W1 is
fixed — the ticket's test requirement would then be owed, and preamble §4 forbids closing
with owed tests; (c) plain `xfail` (non-strict) — it would let a real fix pass unnoticed.

---

## 4. Verified grounding facts

Re-checked against the spec, not recalled. Spec §9.2, all ten rows, accuracy at 5 / 50 epochs:

| # | Agent features | 5 ep | 50 ep |
|---|---|---|---|
| 1 | budget, revenue *(sanity check only)* | 98% | 100% |
| 2 | budget, vote_average, vote_count | 77.2% | 77.6% |
| 3 | budget, tmdb_popularity, vote_average, vote_count | 75.4% | 75.7% |
| 4 | budget, vote_count | 75.7% | 75.5% |
| 5 | budget, tmdb_popularity, tmdb_vote_average, tmdb_vote_count | 72.8% | 74.9% |
| 6 | budget, tmdb_vote_count, ml_vote_count | 73% | 73.4% |
| 7 | budget, ml_vote_average, ml_vote_count | 62.2% | 64.1% |
| 8 | budget, ml_vote_count | 60.3% | 61.9% |
| 9 | budget, tmdb_vote_average | 60.9% | 61.4% |
| 10 | budget, runtime | 53.9% | 56.4% |

Further pinned facts:

- Spec §9.1: every reported number is a **mean over 10 seeded runs with std**.
- Spec §9.2: *"The budget+revenue agent MUST hit ~100% — it can see the answer. If it doesn't, your data pipeline is broken."*
- Spec §5.2: hidden layers `max(1, round(0.3 × input_size))`, width 32, Adam 0.001, batch 32. `ClassifierSpec.epochs` is bounded `[5, 50]` — the two columns sit exactly on the bounds.
- Spec §5.3: agents with eval accuracy < 0.50 are pruned. **This ticket does NOT prune** — §9.2 reports every row including weak ones; pruning is a crowd-construction step, not a reporting step.
- Spec §10.10 / §9.2: match semantics are "direction and magnitude, not decimals"; the ticket's own band is ±3 points at 50 epochs.
- All nine `DEFAULT_FEATURE_COLUMNS` from W1-05 cover every feature named in the ten rows except `revenue`, which is structurally excluded from the feature matrix and reached only by the sanity path.

---

## 5. Execution-path map

```
config YAML (kind: w2_04_agent_table, seed, n_runs: 10)
  └─ harness.run_experiment
       ├─ SeedSequence(seed).spawn(10)          -- one independent stream per run
       └─ for each run:  rng
            └─ _agent_table_runner(config, rng)
                 ├─ _load_labeled_hollywood()   -- MEMOISED (D4); no rng, deterministic
                 │    raw CSVs → build_hollywood_features → variant_a_label
                 ├─ make_split(labeled, rng)    -- per-run; the stochastic dimension
                 │    → train_ids / eval_ids / test_ids (test unused here, D1)
                 ├─ apply_scaling(...)          -- TRAIN-fit min-max, applied to eval
                 └─ for each of 10 rows × {5, 50} epochs:
                      row 1  → build_sanity_agent(...)   (revenue path, D5)
                      rows 2-10 → train_agent(...)       (leak-guarded path)
                      → evaluate(classifier, eval_data)  → accuracy
                 returns {"<slug>@5ep": acc, "<slug>@50ep": acc, ...}   (20 keys)
       └─ _aggregate  → mean ± std per key over the 10 runs
       └─ write_manifest → results/manifests/w2_04_agent_table_<stamp>_<sha>.json

results/W2-04_agent_table_comparison.md  ← emit_comparison_table(manifest)   (D6)
```

Nothing in this path calls `numpy.random.*`: the runner only advances the Generator the
harness hands it (W0-04 RNG-discipline guard).

---

## 6. Pre-code gates

| Gate | State |
|---|---|
| W2-03 merged (`ExplicitAssignment`, `CrowdConfig`) | ✅ PR #16 |
| W2-02 merged (`train_agent`, `build_sanity_agent`, `evaluate`, `prune`) | ✅ PR #15 |
| W0-03/W0-04 harness + manifest + registry | ✅ PR #13 |
| W1 DATA modules on `develop` | ✅ PR #18 |
| Raw data present and checksum-verified | ✅ `tests/unit/data/test_provenance.py` → 10 passed |
| **W1-04 label gate ruled** | ❌ **OPEN — escalated, see §12-R1** |
| **W1-06 RESULT block filled** | ❌ **OPEN — blank in the ticket file; ranking contradicts §9.2, see §12-R2** |

The last two gates are **not** satisfied, and this plan does not pretend otherwise. They do
not block *building* the detector — they determine how its output must be read. §12 routes
both to the stakeholder, which is what the ticket's own acceptance criteria instruct
("Persistent out-of-band rows → escalated with the manifest").

---

## 7. Specification

**`src/wocbots/experiments/agent_table.py`** (new; CORE-owned directory, AGENTS-authored — flag at review per the one-writer rule)

```python
AGENT_TABLE_ROWS: tuple[AgentTableRow, ...]     # the ten §9.2 rows, published 5ep/50ep values
EPOCH_COLUMNS: tuple[int, ...] = (5, 50)

@dataclass(frozen=True)
class AgentTableRow:
    features: tuple[str, ...]
    published: dict[int, float]                 # {5: 0.772, 50: 0.776}
    is_sanity: bool = False
    @property
    def slug(self) -> str                       # "budget+vote_average+vote_count"

def _load_labeled_hollywood(raw_root: Path) -> pd.DataFrame     # memoised (D4)
def _agent_table_runner(config, rng) -> Mapping[str, float]     # 20 keys
register_kind("w2_04_agent_table", _agent_table_runner)

def emit_comparison_table(manifest: Manifest) -> str            # markdown, D6
```

Metric key format: `f"{row.slug}@{epochs}ep"` — e.g. `budget+runtime@50ep`. Flat `str → float`
because that is what `RunResult.metrics` and `_aggregate` accept.

**`configs/w2_04_agent_table.yaml`** (new)

```yaml
name: w2_04_agent_table
kind: w2_04_agent_table
seed: 20260810
n_runs: 10
params:
  raw_root: data/raw
```

**`tests/unit/test_w2_04_agent_table.py`** (new) — see §10.

**Not touched:** `agents/` (this ticket configures W2-02/W2-03, it does not modify them),
`data/` (consumes W1 as-is), any existing config or manifest.

---

## 8. Observability

- `results/manifests/w2_04_agent_table_<UTC>_<sha8>.json` — the evidence. Twenty aggregate
  entries (mean + std), ten per-run records, provenance (git SHA, timestamp), the config verbatim.
- `results/W2-04_agent_table_comparison.md` — published vs measured vs delta, one row per
  (feature set, epoch column), plus the prose write-up of every deviation (ticket S2: deviations
  are *investigated in prose in the manifest, not absorbed*).

---

## 9. Sequenced implementation steps

1. `AgentTableRow` + `AGENT_TABLE_ROWS` with the ten published pairs from §4. No I/O yet.
2. Unit-test the table constant: ten rows, exactly one sanity row, every non-sanity row
   `revenue`-free, every feature present in `DEFAULT_FEATURE_COLUMNS`.
3. `_load_labeled_hollywood` + memoisation; a test that the second call is the same object.
4. `_agent_table_runner` against the real data; register the kind.
5. `configs/w2_04_agent_table.yaml`; run the harness; commit the manifest.
6. `emit_comparison_table`; write `results/W2-04_agent_table_comparison.md`.
7. The slow reproduction test + the manifest-completeness test (§10).
8. Closing report; `AGENT_HANDOFF.md`; index flip **only** after independent review (§8).

---

## 10. Test plan

**Fast (CI runs these — `pytest -m "not slow"`):**

| # | Test | Exact assertion |
|---|---|---|
| T1 | `test_table_has_ten_rows_matching_spec_92` | `len(AGENT_TABLE_ROWS) == 10`; published values equal the §4 table to the decimal |
| T2 | `test_exactly_one_sanity_row_and_it_is_the_leaky_one` | exactly one `is_sanity`; its features are `("budget", "revenue")`; no other row contains `revenue` |
| T3 | `test_every_non_sanity_feature_is_a_real_split_column` | every feature ∈ `DEFAULT_FEATURE_COLUMNS` |
| T4 | `test_metric_keys_cover_ten_rows_times_two_columns` | 20 distinct keys; format `<slug>@{5,50}ep` |
| T5 | `test_manifest_completeness` | every aggregate key traces to a config + seed + git SHA; `len(runs) == 10`; every run carries all 20 keys |
| T6 | `test_runner_is_deterministic_given_the_same_generator` | two runs, same `default_rng(k)`, on a synthetic frame ⇒ byte-identical metrics dict |

**Slow (the ticket-close gate — `pytest`, `@pytest.mark.slow`):**

| # | Test | Exact assertion |
|---|---|---|
| T7 | `test_agent_table_reproduces_published_bands` | for all ten rows: `abs(measured_50ep − published_50ep) <= 3.0` points |
| T8 | `test_orderings_preserved` | `budget+revenue` ≈ 100 and is the max; `budget+runtime` is the min of all non-sanity rows; `budget+vote_average+vote_count` is the max of all non-sanity rows |

T7 and T8 carry `xfail(strict=True, reason="W1-04 label gate open: the shipped snapshot's class balance is 43.93/56.07 vs published 47.5/52.5, and W1-06 ranks budget last (r=0.022) against §9.2's expectation that it anchors. Remove this marker when W1-04 is ruled — strict=True makes the suite fail if it starts passing.")`

---

## 11. Blast radius

- **W5-05 (Q1 exit)** consumes this manifest directly as a report input.
- **W5-02** does not depend on it, but a failed reproduction predicts a failed matched comparison — the same upstream cause.
- Nothing depends on this module's *code*: it registers a kind and adds no seam. Changing
  `AGENT_TABLE_ROWS` changes a published-value constant, which is a spec change and therefore
  a stakeholder matter, not a refactor.
- `emit_comparison_table` is the only new public surface; W8-06 (report assembly) is its
  eventual second consumer.

---

## 12. Risks, alternatives, open questions

**R1 — [Critical, STAKEHOLDER] The W1-04 label gate is open and this ticket runs straight into it.**
Measured on the checksum-verified snapshot at `develop` @ `4bb6804`:

| Quantity | Measured | Spec reference | Δ |
|---|---|---|---|
| Joined movies | 4,227 | 4,722 | −495 |
| Usable rows | 3,032 | 3,699 | −667 |
| Dropped rows | 1,195 | 1,023 | +172 |
| Class balance (variant a) | 43.93 / 56.07 | 47.5 / 52.5 | −3.57 pts |
| Train / test | 2,182 / 607 | ~2,959 / ~740 | −777 / −133 |

W1-04's own rule is that a balance outside ±1 point escalates. It is 3.57 points out. W1-02
(the antevorta-db reconciliation that would settle it) has never run — no `antevorta-db`
source or SQLite has been supplied. **Mitigation:** none available inside this ticket. Build
the detector, run it, record the deltas, escalate. Tuning anything to close this gap is
forbidden-shortcut territory.

**R2 — [High, STAKEHOLDER] W1-06 contradicts §9.2 about the anchor.**
Point-biserial correlation on the train split of this snapshot ranks `budget` **last** of
nine features (r = 0.0224); `tmdb_vote_count` tops it (r = 0.3236). Every §9.2 row is anchored
on `budget`. Either the snapshot is the wrong vintage or the spec's expectation does not hold
for this data. W1-06's RESULT block is still blank, so nothing is recorded either way.
**Mitigation:** report it; do not silently re-anchor. Re-anchoring would change what the
table means while leaving its labels intact — the worst available outcome.

**R3 — [Medium] Runtime.** 10 runs × 10 rows × 2 epoch settings = 200 MLP fits, plus one ETL
pass. Mitigated by D4 (memoised load) and by `threadpool_limits(1)` already pinning the fits.
Expected single-digit minutes; the test is `@slow` and out of CI's path either way.

**R4 — [Low] Directory ownership.** `experiments/` is the CORE stream's under the one-writer
rule, and this lands an AGENTS-authored file there. The alternative — putting an experiment
kind in `agents/` — would be worse, since every other kind lives in `experiments/`. Flag to
CORE at review rather than resolve unilaterally.

**Open question for the stakeholder (one question, two parts):** is the supplied MovieLens
snapshot the intended one, and if so, do the revised counts and balance become this project's
reference numbers — or does the ±3-point §9.2 band still bind against the published table?
The answer determines whether T7/T8's `xfail` markers ever come off.

---

## 13. Definition of Done

1. ☐ Check suite green: `ruff check .` / `ruff format --check .` / `mypy src tests` / `pytest` (full, slow included). No skipped test without a named reason.
2. ☐ T1–T8 land in the same change set as the runner (preamble §4).
3. ☐ Results manifest committed under `results/manifests/` — config + seed + git SHA + all 20 aggregate cells.
4. ☐ `results/W2-04_agent_table_comparison.md` committed, with per-row deltas AND the prose deviation write-up (ticket S2).
5. ☐ No RESULT block in this ticket (it has none); W1-04's and W1-06's remain the DATA stream's to fill — flagged, not filled by this ticket.
6. ☐ Touched paths listed project-root-relative in the closing report.
7. ☐ Nothing lands on `main`; PR onto `develop`, labelled with the ticket number, linked to its issue.
8. ☐ **Independent review signed off (§8)** — Rutvij drove this session, so Rutvij is the implementer and cannot sign. Reviewer is CORE (consumer-reviews-producer) or a different AI system.
9. ☐ `AGENT_HANDOFF.md` updated: old CURRENT STATE demoted to PRIOR, fresh five-part CURRENT STATE, header refreshed.
10. ☐ `00_INDEX.md` W2-04 row flipped — to `✅ (reviewed: <who>, <date>)` **only if** the bands are met; otherwise to `◐ implemented, out-of-band — escalated (see manifest)`, which is the honest state while R1/R2 are open.
