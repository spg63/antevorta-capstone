# W2-04 — §9.2 agent-table reproduction: published vs measured

**Config:** `w2_04_agent_table` · **Seed:** `20260810` · **Runs:** 10 · **Git SHA:** `4bb68043bb86d4c05eec20d09a77698ca3c7ae41+dirty` · **Generated:** 2026-08-10T15:44:49.549817+00:00

Accuracy on the W1-05 eval slice (train-side 90/10; the test split is untouched — spec §10.5). Every cell is a mean ± population std over 10 seeded runs (spec §9.1). Δ is measured − published, in percentage points.

| Agent features | Epochs | Published | Measured (mean ± std) | Δ (pts) | Within ±3 |
|---|---:|---:|---|---:|:---:|
| `budget+revenue` *(sanity)* | 5 | 98.0% | 55.97% ± 0.00 | -42.03 | ✗ |
| `budget+revenue` *(sanity)* | 50 | 100.0% | 97.33% ± 1.71 | -2.67 | ✓ |
| `budget+vote_average+vote_count` | 5 | 77.2% | 57.53% ± 2.13 | -19.67 | ✗ |
| `budget+vote_average+vote_count` | 50 | 77.6% | 66.46% ± 2.53 | -11.14 | ✗ |
| `budget+tmdb_popularity+vote_average+vote_count` | 5 | 75.4% | 59.30% ± 1.81 | -16.10 | ✗ |
| `budget+tmdb_popularity+vote_average+vote_count` | 50 | 75.7% | 70.74% ± 2.92 | -4.96 | ✗ |
| `budget+vote_count` | 5 | 75.7% | 56.38% ± 1.23 | -19.32 | ✗ |
| `budget+vote_count` | 50 | 75.5% | 67.24% ± 3.03 | -8.26 | ✗ |
| `budget+tmdb_popularity+tmdb_vote_average+tmdb_vote_count` | 5 | 72.8% | 62.35% ± 3.07 | -10.45 | ✗ |
| `budget+tmdb_popularity+tmdb_vote_average+tmdb_vote_count` | 50 | 74.9% | 70.25% ± 2.88 | -4.65 | ✗ |
| `budget+tmdb_vote_count+ml_vote_count` | 5 | 73.0% | 59.01% ± 4.84 | -13.99 | ✗ |
| `budget+tmdb_vote_count+ml_vote_count` | 50 | 73.4% | 71.85% ± 3.36 | -1.55 | ✓ |
| `budget+ml_vote_average+ml_vote_count` | 5 | 62.2% | 55.93% ± 0.12 | -6.27 | ✗ |
| `budget+ml_vote_average+ml_vote_count` | 50 | 64.1% | 61.32% ± 2.59 | -2.78 | ✓ |
| `budget+ml_vote_count` | 5 | 60.3% | 55.97% ± 0.00 | -4.33 | ✗ |
| `budget+ml_vote_count` | 50 | 61.9% | 64.57% ± 2.29 | +2.67 | ✓ |
| `budget+tmdb_vote_average` | 5 | 60.9% | 57.04% ± 1.22 | -3.86 | ✗ |
| `budget+tmdb_vote_average` | 50 | 61.4% | 60.41% ± 3.05 | -0.99 | ✓ |
| `budget+runtime` | 5 | 53.9% | 55.97% ± 0.00 | +2.07 | ✓ |
| `budget+runtime` | 50 | 56.4% | 56.54% ± 1.64 | +0.14 | ✓ |


---

## Deviations — investigated, not absorbed (ticket S2)

**Verdict: the reproduction MISSES. Escalated, per the ticket's own acceptance criteria
("persistent out-of-band rows → escalated with the manifest"). Nothing below was tuned to
close a gap; the bands, the orderings, and the published values are the ticket's, unmodified.**

### D0. The canary passes — the data pipeline is NOT the broken part

Spec §9.2 gives one unambiguous instrument: *"The budget+revenue agent MUST hit ~100% — it
can see the answer. If it doesn't, your data pipeline is broken."*

At 50 epochs it reaches **97.33% ± 1.71**, inside the ±3 band. The join, the cleaning rules,
the label, the split, and the scaling therefore reproduce a learnable `revenue > 2 × budget`
relationship end to end. Whatever is wrong below is **not** a broken ETL.

This is worth stating precisely because the canary's first reading said the opposite. The
initial implementation attached `revenue` to the feature frame **unscaled** — `revenue` is
structurally excluded from W1-05's feature matrix (§S3), so the runner must add it by hand,
and it did so in raw dollars (~1e8) beside min-max features in [0, 1]. The canary collapsed
to 55.23% and correctly reported a broken pipeline: the runner's. Fixed by scaling `revenue`
with a TRAIN-only min-max (same leakage discipline as every other column), and pinned by
`test_sanity_row_recovers_a_revenue_defined_label`, which builds a frame whose label IS
`revenue > 2 × budget` and requires the canary to clear 0.90.

### D1. The 5-epoch column is systematically under-trained — every row, including the canary

| Row | Published 5ep | Measured 5ep | Δ |
|---|---:|---:|---:|
| `budget+revenue` *(sanity)* | 98.0% | 55.97% ± 0.00 | −42.03 |
| `budget+vote_average+vote_count` | 77.2% | 57.53% | −19.67 |
| `budget+vote_count` | 75.7% | 56.38% | −19.32 |
| `budget+tmdb_popularity+vote_average+vote_count` | 75.4% | 59.30% | −16.10 |

Three of these sit at **55.97% ± 0.00** — exactly the majority-class rate of this snapshot
(56.07% positive), with zero variance across ten seeds. That is not a weak classifier; that
is a classifier predicting a constant.

The mechanism is arithmetic, not mysterious. `ClassifierSpec.epochs` maps to sklearn's
`MLPClassifier(max_iter=...)`, which for the `adam` solver is literally the epoch count.
With 2,182 training rows at `batch_size=32`, five epochs is ~340 gradient steps at
`learning_rate=0.001` from a random init. The canary — whose target is a *closed-form
function of its own two inputs* — cannot clear the majority class in that budget, but
reaches 97.33% by epoch 50. So the 5-epoch column is measuring optimizer warm-up, not agent
quality.

The published table reports 98% for the canary at 5 epochs. Reproducing that from these
settings is not possible; some element of the published training setup (learning rate,
batch size, init, or the meaning of "epoch") must differ from spec §5.2's stated values.
**This ticket does not adjust them** — the ticket's forbidden-shortcut register bars "tuning
W2-02 internals from inside this ticket (a miss files a bug upstream)". Filed as a question
for the stakeholder, below.

### D2. At 50 epochs, the misses concentrate in the COMBINED vote features

Six of ten rows land inside ±3 at 50 epochs. The four that miss:

| Row | Published 50ep | Measured 50ep | Δ |
|---|---:|---:|---:|
| `budget+vote_average+vote_count` | 77.6% | 66.46% ± 2.53 | **−11.14** |
| `budget+vote_count` | 75.5% | 67.24% ± 3.03 | **−8.26** |
| `budget+tmdb_popularity+vote_average+vote_count` | 75.7% | 70.74% ± 2.92 | −4.96 |
| `budget+tmdb_popularity+tmdb_vote_average+tmdb_vote_count` | 74.9% | 70.25% ± 2.88 | −4.65 |

The pattern is not random. Every row built on `vote_count` / `vote_average` — the
**combined** features that spec §4.3.4–5 constructs by scaling MovieLens ratings ×2,
aggregating per movie, and taking a count-weighted mean across the two sources — comes in
low. Meanwhile every row built purely on the `ml_*` or TMDb-native columns lands inside the
band, as does `budget+runtime`.

The combined features are exactly the quantities that depend on the MovieLens side of the
join, and the MovieLens side is precisely what the open W1-04 escalation is about: this
snapshot matches 4,227 movies against the spec's reference 4,722, and 1,195 rows drop where
the reference drops 1,023. Fewer matched movies means more films carrying `ml_vote_count = 0`
into the weighted mean, which pulls `vote_average` toward its TMDb-only value and shrinks the
information content of `vote_count`. That is a coherent mechanism linking the known data
discrepancy to the specific rows that miss — but it is a **hypothesis**, not a finding,
because confirming it needs W1-02's reference table, which has never been built for want of
an `antevorta-db` artifact.

### D3. One published ordering is broken

The ticket requires three orderings. Measured at 50 epochs:

| Ordering required | Result |
|---|---|
| `budget+revenue` ≈ 100% and tops the table | ✓ 97.33%, highest of all ten |
| `budget+runtime` is the worst real agent | ✓ 56.54%, lowest of the nine |
| `budget+vote_average+vote_count` is the best real agent | ✗ **it is 66.46%, the *worst* of the multi-feature real agents.** The measured best real agent is `budget+tmdb_vote_count+ml_vote_count` at 71.85% |

Both endpoint orderings survive. The one that breaks is the one that depends on the combined
vote features — the same family as D2, from the same suspected cause.

### D4. W1-06 contradicts §9.2 about the anchor, and its RESULT block is still blank

Every row in §9.2 is anchored on `budget`. Point-biserial correlation against the label, on
this snapshot's train split only, ranks `budget` **last of nine** (r = 0.0224, effectively
uncorrelated); `tmdb_vote_count` tops the list at r = 0.3236.

W1-06's RESULT block in `tickets/W1-06_anchor-analysis.md` is still `☐ ____` on `develop`, so
no anchor set has ever been formally chosen or ratified — the Hollywood crowd configs from
W2-03 encode `budget` provisionally, on the spec's word. This ticket does **not** re-anchor.
Re-anchoring would change what the table means while leaving its row labels intact, which is
the worst available outcome for a detector.

---

## What this ticket asks the stakeholder to rule

One question, three parts, all routed together because they share a root:

1. **Is the supplied MovieLens snapshot the intended one?** It is checksum-verified against
   `data/DATA_PROVENANCE.md`, so it is *the file the team was given* — but it yields 4,227
   matched movies against the spec's 4,722 and a 43.93 / 56.07 class balance against the
   published 47.5 / 52.5 (W1-04's tolerance is ±1 point).
2. **If it is:** do the revised counts and balance become this project's reference numbers,
   or does the ±3-point §9.2 band still bind against the published table? The answer decides
   whether W2-04 can ever close green on this data.
3. **What accounts for the 5-epoch column?** Spec §5.2's stated optimizer settings cannot
   produce 98% for a two-feature agent whose label is a closed-form function of its inputs in
   five epochs. Either the published "epoch" means something else, or §5.2's values differ
   from what produced the published table. This is a spec question, not an implementation one.

**Also still owed by the DATA stream, unchanged by this ticket:** W1-04's RESULT block,
W1-06's RESULT block, and an `antevorta-db` artifact (source or built SQLite) to unblock
W1-02 — without which the strict row-level half of W1-04's gate cannot be checked at all.

## Reproducing this table

```bash
uv run pytest tests/unit/data/test_provenance.py   # confirm the raw snapshot first
uv run python -m wocbots.experiments.harness configs/w2_04_agent_table.yaml
```

Every cell above traces to `results/manifests/w2_04_agent_table_<stamp>_<sha>.json`:
config + seed + git SHA + ten per-run records. The table in this file is *generated* from
that manifest by `emit_comparison_table`, never typed by hand, and
`test_comparison_table_artifact_matches_committed_manifest` fails if the two ever drift.
