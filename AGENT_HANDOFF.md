# Agent Handoff

**Last updated:** 2026-08-24 SamuelGauthier: PR #33 attestation completed by sarjit304, ready to merge

> **HOW THIS FILE WORKS (do not delete this box).** This is the repo's living state journal — the first
> thing every new session reads after the preamble. Rules:
> 1. Only the **header line** and the **CURRENT STATE** section describe the present. Everything under
>    `## PRIOR` is history — never edit it, never implement from it.
> 2. When you finish a work session (or close a ticket), demote the old CURRENT STATE to a `## PRIOR
>    (<date>, <topic>)` section and write a fresh CURRENT STATE. Update the header line (date, who, branch,
>    commit, tree state).
> 3. A CURRENT STATE entry has exactly five parts — fill all five, keep each short:
>    - **Done:** what landed, with ticket IDs and where the evidence is (manifest, PR, test names).
>    - **In flight / blocked:** anything half-done, parked, or waiting on a ruling — say what it waits FOR.
>    - **Owner-attention:** decisions or reviews a human owes (name the human).
>    - **Next step:** the single most useful thing the next session should do.
>    - **Five-minute test:** one or two commands a fresh session can run to verify this entry still
>      describes reality (if the test fails, the handoff is stale — fix it FIRST).
> 4. Write for someone with zero context beyond the preamble. No unexplained abbreviations, no "as
>    discussed." If you invented a name this session, define it.

## CURRENT STATE (2026-08-24, PR #33 — reviewer attestation now actually completed)

- **Done:** sarjit304 re-approved PR #33 and, this time, **checked all five reviewer-attestation
  boxes** in the PR body (not-implementer / full diff read / forbidden-shortcut register /
  test pins verified / index-flip line present) — not just a GitHub "Approve" click. This is
  the first properly-completed §8 attestation seen across #32 or #33. PR shows "Changes
  reviewed — 1 approving review by reviewers with write access," 2/2 checks passing, no
  conflicts with `develop`, mergeable. `00_INDEX.md`'s W3-04 row has been corrected to
  `✅ (reviewed: @sarjit304, 2026-08-24)`, now matching the date the real attestation actually
  happened (rather than the stale 2026-08-17 the implementer had pre-written).

- **In flight / blocked:** PR #33 is **approved but not yet merged** — the merge button hasn't
  been clicked. Nothing is blocking it now on the review side.

- **Owner-attention:** The index row's *content* is now accurate, but the underlying habit that
  produced #32's near-miss is still present: the implementer wrote the index ✅ line as one of
  their own commits (`ff0138d`) before the reviewer had actually done anything, and it happened
  to get corrected to the right date only because it was caught here. Worth a standing note to
  spg63 that the index flip should be written by/at the point of reviewer sign-off, not
  pre-written by the implementer and fixed up after the fact — it's what let #32 merge with an
  empty checklist in the first place, and it's just luck that #33's version didn't ship wrong.

- **Next step:** Merge PR #33 (button is live, all gates satisfied, index now correct). Flag
  the pre-writing-the-index habit to spg63 as a process item, independent of this ticket.

- **Five-minute test:** `git log --oneline -1 develop` after merging should show W3-04's
  squash/merge commit; `uv run pytest -q` → 264 passed, 21 skipped, 2 xfailed still holds.

## PRIOR (2026-08-24, PR #33 review — attestation process bypassed on both #32 and #33)

- **Done:** Independently re-verified PR #33's diff (`ticket/w3-04`, HEAD `cc067ce`) myself:
  `ruff check`, `ruff format --check`, `mypy --strict` all clean; `pytest -q` → 264 passed,
  21 skipped, 2 xfailed; `test_history_trust.py` → 8 passed, matching the closing report's
  D1–D5 pins. PR #32 (W3-03) is confirmed **merged** — `rootwij` merged commit `e5ec77a` into
  `develop` (2 checks passed, +1,422/-6 across 10 files). So #33's branch genuinely does build
  on current `develop`; that part is not stale. The *code* on both tickets is fine. The
  *review process* on both is not — see below.

- **In flight / blocked:** Both W3-03 (#32, merged) and W3-04 (#33, open) were/are marked
  `✅ (reviewed: ..., <date>)` in `00_INDEX.md`, but neither ticket actually satisfied
  preamble §8 before that happened:
  1. **PR #32 (W3-03) — merged with the reviewer attestation checklist still 100% unchecked.**
     SamuelGauthier (the implementer) directly asked AnuragRSimha, in-PR, to go through the
     attestation so the PR could merge — a documented, explicit request. AnuragRSimha never
     did; he only clicked GitHub's "Approve," which is not the same thing as the §8 checklist
     (full diff read, forbidden-shortcut register, test-pin verification). The PR was then
     **merged anyway, ~1 week after that unanswered request, by rootwij** — a third person who
     is not listed as a reviewer on the PR at all and left no review of his own. So the ticket
     closed with zero recorded completions of any §8 checklist item, by anyone. The `00_INDEX.md`
     row (`✅ reviewed: @AnuragRSimha, 2026-08-17`) names a reviewer who never finished the
     attestation, and doesn't mention rootwij, who's the one who actually merged it.
  2. **PR #33 (W3-04) — same shape, still open.** Reviewer checklist 100% unchecked;
     `00_INDEX.md`'s `✅ (reviewed: @sarjit304, 2026-08-17)` row was committed by the
     implementer (`ff0138d`, SamuelGauthier) before the PR was even marked ready for review
     (Aug 24) — the review date predates the PR's own ready-for-review event.
  3. **Both index self-flips follow the identical pattern:** implementer writes their own
     ✅ row into `00_INDEX.md` as one of their commits, rather than the reviewer recording it
     at actual sign-off time, per preamble §8's explicit instruction.

- **Owner-attention:** This is now confirmed across two consecutive ticket-closing PRs, not
  a one-off: an implementer can (a) self-flip the index to ✅, (b) get an "Approve" click that
  never completes the actual checklist, and (c) have a third, uninvolved person merge it once
  the real reviewer stalls — and the ticket ends up marked reviewed with nobody having done
  the review. **A direct, in-PR request to the reviewer to complete the attestation was made
  and ignored on #32; the merge went through regardless.** This needs to go to the repo admin
  (spg63) or stakeholder — branch protection that blocks merge until the attestation checklist
  items are checked (or an equivalent required-review rule) would close this gap outright,
  since asking people to comply by hand has now failed twice.

- **Next step:** Do not treat W3-03 or W3-04 as having had a real independent review, `00_INDEX.md`
  notwithstanding. Escalate to spg63/stakeholder for a process fix (branch protection / required
  checklist) rather than re-requesting attestation from AnuragRSimha or sarjit304 individually —
  that path is already demonstrated not to work. For #33 specifically: get someone who did not
  implement it to actually complete the attestation before it merges, so it doesn't repeat #32's
  pattern a third time.

- **Five-minute test:** `git log --oneline -1 develop` → should show `e5ec77a` or later;
  `uv run pytest -q` → 264 passed, 21 skipped, 2 xfailed confirms the code side is still fine
  independent of the process issue. Check PR #32 and #33's "Reviewer attestation" checklists
  directly on GitHub — if either is fully checked, this entry is stale, update it.

## PRIOR (2026-08-17, PR #32)

- **Done:** @AnuragRSimha reviewed W3-03 in #32
- **In flight / blocked:** W3-04, W6-02 unblocked
- **Owner-attention:** Nothing.
- **Next step:** Finish W3-04's plan and implementation
- **Five-minute test:** `git log --oneline -5 develop`, `pytest -q`

## PRIOR (2026-08-16, W3-04 implemented, pending independent review)

- **Done:** W3-04 (Interaction history store and trust updates) implemented on
  branch `ticket/w3-04`. `HistoryRecord` and `HistoryStore` land in
  `src/wocbots/interaction/history.py`; `ReferenceInteractionPolicy.update_trust`
  implements §6.5 trust update formula; `Encounter` records directed history
  rows (cardinality 1 encounter -> 2 directed rows). Check suite green: ruff /
  ruff-format / mypy-strict / pytest all pass (226 passed, 11 skipped, 1
  xfailed — +8 new pinned tests in `tests/unit/test_history_trust.py`).
  Pure-mechanism ticket (results manifest N/A). Plan and closing report:
  `tickets/W3-04_history-trust_PLAN.md` and
  `tickets/W3-04_history-trust_CLOSING-REPORT.md`.
- **In flight / blocked:** W3-04 awaiting independent review sign-off
  (preamble §8); W4-01 (participant selection loop & arena integration) is
  unblocked for implementation.
- **Owner-attention:** Independent reviewer needed for W3-04.
- **Next step:** Independent review of W3-04 -> flip `00_INDEX.md` row to
  `✅ (reviewed: <who>, <date>)` -> proceed to W4-01.
- **Five-minute test:** `uv run pytest tests/unit/test_history_trust.py -q`
  -> 8 passed; `python -c "from wocbots.interaction import HistoryStore, HistoryRecord, ReferenceInteractionPolicy"`.

## PRIOR (2026-08-16, PR #30's Wave 2 work merged with the landed W1 wave)

- **Done:** `develop` (@ `c15deaa`, which now carries PR #31's W1-02/W1-04/W1-05 work plus its
  review fixes) merged into `rootwij/w2-03-04-real-data` to clear PR #30's only conflict. The
  conflict was this file and nothing else: two sessions each wrote a CURRENT STATE on top of
  `4bb6804`. Both are preserved verbatim below as PRIOR entries — the 2026-08-15 W1-05 entry
  and the 2026-08-10 Wave 2 entry — and nothing was dropped. The code sides are disjoint (W2
  touched `src/wocbots/experiments/`, `configs/`, `tests/unit/test_w2_*`; W1 touched
  `src/wocbots/data/`, `scripts/`, `tests/unit/data/`) and merged with no conflict.

- **In flight / blocked:**
  1. **The §9.2 reproduction still MISSES, and that is the reportable result, not an
     unfinished one.** See the 2026-08-10 PRIOR entry for the numbers; nothing in the W1 merge
     moves them, and nothing was tuned to close any gap. Checked explicitly: that entry warned
     the two `xfail(strict=True)` W2-04 slow tests would go RED if W1-04 fixed the data. On the
     merged tree with `data/raw/` present they **still xfail** — W1-04 shipped variant (a)
     undefended at the same 43.93/56.07 balance, so the label the agent table trains against is
     unchanged. CI cannot see this either way: it runs `-m "not slow"` and has no raw data.
  2. **`data/derived/split_v1.*` must be regenerated before anything consumes its folds.** It
     predates PR #31's fold-leak fix — see the review amendment in the 2026-08-15 PRIOR entry.
  3. **W1-06 (anchor analysis) has still not run against the real split.** It is the last open
     W1 item, and it must run against the regenerated `split_v1`, not the artifact on disk.

- **Owner-attention:**
  1. **Stakeholder / Dr. Grimes** — the three-part ruling requested in
     `results/W2-04_agent_table_comparison.md` is still unanswered (snapshot intent, whether
     the ±3 band still binds, and the 5-epoch column).
  2. **CORE / a different AI system** — independent review (§8) of W2-01, W2-02, W2-03 and
     W2-04 is still owed. Rutvij drove all four sessions and cannot sign any of them off. No
     W2 ticket is ✅.
  3. **Anurag** — three items PR #31's review left open: regenerate `data/derived/split_v1.*`;
     regenerate `tests/fixtures/w1_02_reference/movies_reference_excerpt_50.csv` (the committed
     excerpt contains none of the duplicate-tmdbId rows it advertises); and commit
     `scripts/build_movies_sqlite.py`, which this file, `data/DATA_PROVENANCE.md` §5 and
     `wocbots.data.ground_truth`'s module docstring all name as W1-02 S1's provenance record
     but which does not exist in the repo.
  - **Closed by the merge:** the 2026-08-10 entry's DATA-stream item ("W1-04's RESULT block and
    W1-06's are still literally `☐ ____`; W1-02 has never run") is superseded — W1-02 and W1-04
    landed in PR #31, W1-06 remains open and is listed above.

- **Next step:** land PR #30, then run W1-06's anchor analysis
  (`wocbots.data.anchor_analysis.rank_features`) against a regenerated `split_v1`. That is the
  last item standing between here and a closed W1 wave.

- **Five-minute test:** `uv run pytest -m "not slow"` → 239 passed, 7 skipped, 11 deselected
  (the 7 skips are all local-data-dependent: `data/raw/movies.sqlite` and the gitignored
  labeled CSV); `git log --oneline -1 origin/develop` → `c15deaa`.

## PRIOR (2026-08-15, W3-03 implemented, pending independent review)

- **Done:** W3-03 (interaction kernel: certainty update and prediction flip)
  implemented on branch `ticket/w3-03`. `CertaintyFlipScoringPolicy`,
  `ReferenceInteractionPolicy`, and `Encounter` land in
  `src/wocbots/interaction/`. Check suite green: ruff / ruff-format /
  mypy-strict / pytest all pass (218 passed, 11 skipped, 1 xfailed — +10 new
  pinned tests in `tests/unit/test_interaction_kernel.py`). Pure-mechanism
  ticket (results manifest N/A). Plan and closing report:
  `tickets/W3-03_certainty-update-flip_PLAN.md` and
  `tickets/W3-03_certainty-update-flip_CLOSING-REPORT.md`.
- **In flight / blocked:** W3-03 awaiting independent review sign-off
  (preamble §8); W3-04 (history store + trust updates) unblocked for planning
  and implementation.
- **Owner-attention:** Independent reviewer needed for W3-03.
- **Next step:** Independent review of W3-03 → flip `00_INDEX.md` row to
  `✅ (reviewed: <who>, <date>)` → proceed to W3-04.
- **Five-minute test:** `uv run pytest tests/unit/test_interaction_kernel.py -q`
  → 10 passed; `python -c "from wocbots.interaction import CertaintyFlipScoringPolicy, ReferenceInteractionPolicy, Encounter"`.

## PRIOR (2026-08-15, W3-02 reviewed and merged on develop)

- **Done:** @rootwij merged and reviewed W3-02 in #21
- **In flight / blocked:** W3-03, W4-01 unblocked, plan and implementation in
  progress
- **Owner-attention:** Reviewer didn't update 00_INDEX.md nor pull request
  checklist nor PLAN's DoD.
- **Next step:** Finish W3-03's plan and implementation
- **Five-minute test:** `git log --oneline -5 develop`, `pytest -q`

## PRIOR (2026-08-15, W1-05 splits + scaler artifact built on real shipped data)

- **Done:** W1-05 S1/S2/S3 run against the real shipped label from
  `data/hollywood_features_labeled_variant_a.csv` (3,032 rows, variant (a) label — see
  W1-04's RESULT block). `src/wocbots/data/splits.py` gained persistence
  (`write_split_artifact`/`load_split_artifact`, npz for id arrays + JSON for
  seed/feature-columns/scaler params, mirroring `wocbots.data.ground_truth`'s writer
  convention) — it previously only built `SplitArtifact` in memory with no save path.
  `scripts/build_w1_05_splits.py` (new CLI runner, same shape as
  `extract_w1_02_reference.py`) ran with the project's standard seed (42, per
  `configs/*.yaml`) and produced `data/derived/split_v1.json` +
  `data/derived/split_v1.npz` (gitignored derived artifacts, per `data/README.md` policy).
  Result: 2,182 train / 243 eval / 607 test, 5 folds, 9 feature columns
  (`revenue` structurally excluded). Stratification holds within 0.1pt of the overall
  56.07% positive rate across train/eval/test — well inside the ±1pt requirement (this is
  stratification quality, unrelated to and not fixing W1-04's published-balance gap).
  Scaler params (train-only) verified to put scaled train features in [0, 1].
  `tests/unit/data/test_splits.py` gained a persistence round-trip test. Full repo suite:
  **215 passed, 13 skipped, 0 failed** (`uv run pytest -q`); RNG-discipline guard
  (`tests/unit/test_rng_discipline.py`) confirms the new script's `default_rng` call
  doesn't need allowlisting since it's outside `src/wocbots/`, the guard's only scope.

- **Review amendment (2026-08-16, independent review of PR #31):** `make_split` was cutting
  its 5 folds from `train_idx` — the 80% slice taken BEFORE the 90/10 eval rows are carved
  out — while `train_ids` holds the 72% that remains after. Every fold's training side
  therefore carried the eval slice, so Q2 cross-validation would have been scored against
  agent eval metrics computed on rows it had already trained on (spec §10.5). Folds now cut
  from `real_train_idx`; `test_folds_partition_the_train_ids_and_exclude_the_eval_slice`
  fails against the original loop. **The `data/derived/split_v1.*` artifact described above
  predates this fix and must be regenerated** (`uv run python scripts/build_w1_05_splits.py`)
  before anything consumes its folds — train/eval/test membership is unchanged, fold
  membership is not.

- **In flight / blocked — carried forward, NOT resolved by this session:**
  1. **W1-06 (anchor analysis) has not been run against this real split yet.** The code
     (`wocbots.data.anchor_analysis`) is implemented and unit-tested against synthetic
     data only. Running it against `data/derived/split_v1`'s real train ids is the
     literal next step to close W1-06's RESULT block and finish the W1 wave.
  2. **W1-02's independence gap** (see the 2026-08-14 entry below) is unaffected by this
     work — still permanent, not pending.
  3. **`scripts/build_movies_sqlite.py` does not exist in the repo**, but this file (line 111),
     `data/DATA_PROVENANCE.md` §5, and `src/wocbots/data/ground_truth.py`'s module docstring
     all name it as the record of how `movies.sqlite` was produced — which is W1-02 S1's
     actual deliverable ("the FILE plus a record of how it was produced"). Whoever ran that
     build must commit the script they ran; it was deliberately not reconstructed during
     review, because a plausible-looking rewrite is not a provenance record.

- **Owner-attention:** none new. W1-05 is done per its own acceptance criteria.

- **Next step:** run W1-06's anchor analysis (`wocbots.data.anchor_analysis.rank_features`)
  against the real train split (`data/derived/split_v1`, loadable via
  `wocbots.data.splits.load_split_artifact`), verify `budget`/`vote_count` top the ranking
  as spec §9.2 expects, choose the anchor set, and fill the ticket's RESULT block. That's
  the last open item in the W1 wave.

- **Five-minute test:** `uv run python scripts/build_w1_05_splits.py` (regenerates
  `data/derived/split_v1.*` deterministically — same seed, same output); `uv run pytest
  tests/unit/data/test_splits.py -q` (expect 10 passed).

## PRIOR (2026-08-15, W1-04 label gate ruled and closed — variant (a) shipped)

- **Done:** The owner-attention decision from the 2026-08-14 entry below is resolved: label
  columns are ruled OUT OF SCOPE for this dataset snapshot (option (a)), and variant (a)
  (`revenue > 2×budget`, spec §4.3.7) ships as THE label, undefended — ratified by Anurag
  Ravishankar Simha (project owner), 2026-08-15. `tickets/W1-04_labels-validation-gate.md`'s
  RESULT block is filled: shipped balance 43.93/56.07 (n=3,032, computed on
  `data/raw/movies.sqlite`), does NOT match the published 47.5/52.5 (outside ±1pt tolerance) —
  that mismatch is accepted, not silently fixed. `src/wocbots/data/labels.py` and
  `src/wocbots/data/ground_truth.py` docstrings updated to state the ruling instead of
  describing an open block. `tests/unit/data/test_labels.py`'s xfail
  (`test_class_balance_within_one_point_of_published_split`) replaced with a passing
  regression pin (`test_shipped_label_balance_matches_ratified_result`) on the ratified
  numbers — it does not re-impose the published-balance requirement the ruling waived.
  `data/hollywood_features_labeled_variant_a.csv` regenerated locally (gitignored, per
  `data/*.csv` policy) from `movies.sqlite`. Check suite: `pytest tests/unit/data -q` → 37
  passed, 12 skipped, 0 xfailed.

- **In flight / blocked — carried forward, NOT resolved by this ruling:**
  1. **W1-02's independence gap is still open and now permanent, not just pending.** Because
     the label gap is ruled out of scope rather than unblocked, `movies.sqlite` will not
     become an independent reference later unless someone supplies actual `antevorta-db`
     output — nothing in this session changes that likelihood.
  2. **W1-05 and W1-06 have not yet been re-run against the real shipped label.** W1-05's
     splits/scaling code and W1-06's anchor-analysis code are implemented and unit-tested
     against fixtures/synthetic data, but neither has been executed against
     `data/hollywood_features_labeled_variant_a.csv` to produce real split artifacts or fill
     W1-06's RESULT block. That's the next concrete step to actually finish the W1 wave.

- **Owner-attention:** none outstanding for W1-04 — this entry closes it. W1-05/W1-06 need a
  session to actually run them against the real labeled data, not a ruling.

- **Next step:** run W1-05 (`wocbots.data.splits`) against
  `data/hollywood_features_labeled_variant_a.csv` to produce the persisted 80/20 splits +
  scaler artifacts, then run W1-06's anchor analysis on the resulting train split and fill its
  RESULT block. That closes out the W1 wave per its own acceptance criteria.

- **Five-minute test:** `uv run pytest tests/unit/data -q` (expect 37 passed, 12 skipped, 0
  xfailed); `cat tickets/W1-04_labels-validation-gate.md` and check the RESULT block is
  checked, not blank.

## PRIOR (2026-08-14, W1-02 S1/S2 implemented, pending independent review)

- **Done:** W1-02's S1 is resolved by stakeholder ruling (Sean Grimes, email "Re: Antevorta
  SQLite", 2026-08-14): ground truth is built by CSV-porting through the existing W1-03
  pipeline (`scripts/build_movies_sqlite.py`), not the antevorta-db JVM build, and not a
  row-level extraction from the antevorta-db instance. S2 (extraction/versioning/counts) is
  implemented against that file: `src/wocbots/data/ground_truth.py`
  (`extract_reference`/`write_versioned_reference`/`write_excerpt`),
  `scripts/extract_w1_02_reference.py` (CLI runner), `tests/unit/data/test_ground_truth.py` (7
  tests: 5 pass against a local `data/raw/movies.sqlite`, 2 explicit named skips — not silent
  gaps — for the parts the ruling doesn't cover), committed excerpt
  `tests/fixtures/w1_02_reference/movies_reference_excerpt_50.csv`. Full counts + the exact
  ruling quote recorded in `data/DATA_PROVENANCE.md` §5. Check suite run locally on the
  touched files: `pytest tests/unit/data -q` → 36 passed, 12 skipped, 1 xfailed (pre-existing
  skips/xfail unchanged by this work).

- **In flight / blocked — carried forward, NOT resolved by this session:**
  1. **W1-02's independence gap.** `movies.sqlite` is produced by the same W1-03 logic it would
     need to validate — it is not an independent reference. This is now explicitly documented
     (not silently accepted) in `data/DATA_PROVENANCE.md` §5, item 1.
  2. **Label columns.** No label columns exist anywhere in scope (not in `movies.sqlite`, not
     supplied separately). The stakeholder's ruling addressed the SQLite *build method*, not
     the label *formula* (`TMDBMoviesPusher.kt`'s `determinePerformanceClass`). This was NOT
     fabricated — see `data/DATA_PROVENANCE.md` §5 item 2 for exactly what's needed to unblock
     it. W1-04's S2/S3 (label variants, the reconciliation gate) cannot run as specified until
     this is answered.

- **Owner-attention (Dr. Grimes / the team):** one specific decision needed to actually close
  W1-02/unblock W1-04 fully: for the label columns, either (a) rule that they're out of scope
  for this dataset snapshot and W1-04 ships spec's stated rule (`revenue > 2×budget`)
  undefended by reference reconciliation — a documented scope cut, not a silent one — or (b)
  supply the label formula/column some other way (a value he's willing to pull from
  antevorta-db directly, or the relevant Kotlin logic). Independent review still needed for
  this ticket's diff per preamble §8 before `00_INDEX.md` flips past a bare status.

- **Next step:** send Grimes the one-line question above; once answered, either close W1-04's
  gate with the ruled-in label or wire up the supplied formula, then get W1-02's diff
  independently reviewed and flip `00_INDEX.md`.

- **Five-minute test:** `PYTHONPATH=src pytest tests/unit/data/test_ground_truth.py -q` (needs
  `data/raw/movies.sqlite` present locally, else the sqlite-dependent tests skip with a named
  reason); `cat data/DATA_PROVENANCE.md` section 5 for the ruling + counts.
## PRIOR (2026-08-10, Wave 2 done on real data — W2-03 was broken, W2-04 escalates)

- **Done:** The Hollywood raw data is on disk at `data/raw/{tmdb,movielens}/` and
  checksum-verified (`tests/unit/data/test_provenance.py` → 10 passed; previously all skipped).
  **W2-03 real-data closure:** both shipped Hollywood crowd configs named `popularity`, which
  the W1-03 ETL does not emit (it emits `tmdb_popularity`) — **both the §9.2 and §9.3 reference
  crowds were unbuildable and had been since they were written.** Thirty green W2-03 unit tests
  missed it because they build synthetic frames matching whatever the config names. Configs
  fixed; new `src/wocbots/experiments/hollywood_data.py` (one shared real-split path for W2-03
  and W2-04), `crowd_build.py` (kind `w2_03_hollywood_crowd`), `configs/w2_03_crowd_{5,26}agent.yaml`,
  `tests/unit/test_w2_03_hollywood_crowd.py` (9 passed incl. 3 slow real-data builds, plus a
  planted-defect self-test), addendum in `tickets/W2-03_*_CLOSING-REPORT-ADDENDUM.md`.
  **W2-02:** its real-data band check no longer skips — the sanity agent scores 97.3% on real data.
  **W2-04** implemented: `src/wocbots/experiments/agent_table.py` (kind `w2_04_agent_table`,
  the ten §9.2 rows, the comparison emitter), `configs/w2_04_agent_table.yaml`,
  `tests/unit/test_w2_04_agent_table.py` (10 passed, 2 xfailed), manifest
  `results/manifests/w2_04_agent_table_20260810T154449Z_4bb68043.json`, escalation artifact
  `results/W2-04_agent_table_comparison.md`. Plan + closing report in `tickets/W2-04_*`.
  Governance backfill: W2-01's plan and W2-02/W2-03's closing reports moved into `tickets/`
  (they had lived outside the repo since July); `00_INDEX.md` v1.16/v1.17 + W2-01..04 status marks.
  Check suite green (ruff / ruff-format / mypy-strict / pytest).
- **In flight / blocked:** **The §9.2 reproduction MISSES and this is the reportable result,
  not an unfinished one.** The `budget+revenue` canary hits 97.33% ± 1.71 at 50 epochs, so by
  spec §9.2's own instrument the DATA PIPELINE IS VALIDATED. But 4 of 10 rows fall outside
  ±3 at 50 epochs — all four built on the combined MovieLens+TMDb vote features — one of the
  three required orderings breaks, and the whole 5-epoch column is under-trained (three rows
  sit at exactly 55.97% ± 0.00, the majority-class rate, zero variance over ten seeds).
  The two slow tests carry `xfail(strict=True)` naming W1-04; they go RED if the data is
  fixed and the table starts passing. Nothing was tuned to close any gap.
- **Owner-attention:**
  1. **Stakeholder / Dr. Grimes** — three-part ruling in `results/W2-04_agent_table_comparison.md`:
     is this MovieLens snapshot the intended one (it is checksum-verified but joins 4,227 vs
     the spec's 4,722, balance 43.93/56.07 vs 47.5/52.5); if so do the revised numbers become
     the reference or does the ±3 band still bind; and what accounts for the 5-epoch column,
     since spec §5.2's stated optimizer settings cannot produce 98% for the canary in five epochs.
  2. **DATA stream** — W1-04's RESULT block and W1-06's are still literally `☐ ____`; W1-02
     has never run for want of an `antevorta-db` artifact. This is what blocks W2-04 from ✅.
  3. **CORE / a different AI system** — independent review (§8) of W2-01, W2-02, W2-03 AND
     W2-04. Rutvij drove all four sessions and cannot sign any of them off. No W2 ticket is ✅.
  4. **Rutvij** — commit + PR onto `develop`, labelled, linked to Issue #7; then re-run the
     harness from the committed tree so the manifest cites a clean SHA (it currently reads
     `4bb68043...+dirty`, honest but not closeable evidence).
- **Next step:** get the W1-04 ruling. Everything else in Wave 2 is done and waiting on review;
  that ruling is the only thing that can move W2-04 from `◐ escalated` to `✅`.
- **Five-minute test:** `uv run pytest tests/unit/data/test_provenance.py` → 10 passed (if they
  SKIP, `data/raw/` is missing and this entry is stale — fix that first);
  `uv run pytest tests/unit/test_w2_04_agent_table.py` → 10 passed, 2 xfailed.


## PRIOR (2026-08-07, W3-02 implemented, pending independent review)
- **Done:** W3-02 (movement, anti-clique, lockstep round engine) implemented on
  branch ticket/w3-02. RandomMovementPolicy + RoundEngine land in
  src/wocbots/arena/; Arena extended with move_to/cell/agents_at (plan §3 D1).
  Encounter statistics recorded via a real registered harness kind
  (w3_02_movement_smoke in src/wocbots/experiments/kinds.py, plan §3 D4) — not a
  hand-written manifest; committed reference manifest at
  results/manifests/w3_02_movement_smoke_20260807T224338Z_34cf4f35.json. Check
  suite green: ruff / ruff-format / mypy-strict / pytest all pass (150 passed, 1
  skipped — pre-existing, unrelated). Closing report:
  tickets/W3-02_movement-rounds_CLOSING-REPORT.md.

- **In flight / blocked:** W3-02 awaiting independent review sign-off (preamble
  §8) before 00_INDEX.md's W3-02 row can be flipped past its current bare ✅ to
  a dated, attributed one, and before W3-03/W4-01 can treat it as landed rather
  than merely implemented.

- **Owner-attention:** independent reviewer needed for W3-02 (name TBD). Whoever
  reviews: update 00_INDEX.md's W3-02 row to ✅ (reviewed: <who>, <date>) and
  this file's CURRENT STATE before merging the PR — the W3-01 review skipped
  exactly this step, which is why the prior session had to spend a round
  reconciling stale docs after the fact (see PRIOR below).

- **Next step:** get W3-02 independently reviewed; once landed, W3-03 and W4-01
  are unblocked on this ticket specifically (W4-01 still separately needs
  W3-04).

- **Five-minute test:** git log --oneline -5 origin/develop, pytest -q


## PRIOR (2026-08-08, W4-04 tiers + mechanism comparison — since merged to develop in PR #29)

- **Done:** W4-04 on `manan/w4-04-tiers-mechanism-comparison` (Manan Patel): tiers, mechanism-comparison +
  synthetic-anchor kinds, evaluation loop, tests. Plan + closing report in `tickets/W4-04_*`. Process doc
  `docs/BRANCHING.md`. W4-01/02/03 on `develop` (PR #17); W4-04 **not** merged yet.
- **In flight / blocked:** Manual PR merge to `develop`. W4-01 arena integration blocked on W3-02/04. Branch
  protection on `main`/`develop` not enabled — needs repo admin.
- **Owner-attention:** **Manan** — PR to `develop`, label W4-04, link Issue #9, independent review. **Admin
  (spg63)** — enable branch protection per `docs/BRANCHING.md`.
- **Next step:** Open/refresh PR; merge after CI + review; flip W4-04 status in index with reviewer line.
- **Five-minute test:** `git log develop -1 --oneline` → no W4-04 tiers; branch tip → `2c19b25` or later.

## PRIOR (2026-08-01, W3-01 reviewed and merged on develop)

- **Done:** @rootwij merged and reviewed W3-01 in #21
- **In flight / blocked:** W3-02 unblocked, plan and implementation in progress
- **Owner-attention:** Reviewer didn't update 00_INDEX.md nor pull request
  checklist nor PLAN's DoD.
- **Next step:** Finish W3-02's plan and implementation
- **Five-minute test:** `git log --oneline -5 develop`, `pytest -q`

## PRIOR (2026-07-31, W3-01 implemented on branch, pending review)

- **Done:** W3-01 (grid geometry + random init) implemented on branch
  `ticket/w3-01-plan`. `Arena` (rows/cols per §6.1 v1.2, occupancy ≤ 2 via
  `_GridCell`) + `RandomInitPolicy` (uniformly random empty cell, spec §6.2)
  land in `src/wocbots/arena/`, replacing the W0-02 constructor-only stub.
  Check suite green: ruff / ruff-format / mypy-strict / pytest all pass
  (arena scope: 21 passed). Pure-mechanism ticket: results manifest N/A.
  Check suite green: ruff / ruff-format / mypy-strict / pytest all pass (136
  passed, 1 skipped — the skip is test_w2_02_classifier.py's W1-05 real-data
  band check, pre-existing, unrelated to W3-01).
  Closing report: `../W3-01_grid-geometry-init_CLOSING-REPORT.md`.
- **In flight / blocked:** W3-01 close blocked on independent review (§8 —
  someone who didn't implement it). W3-02 (movement/rounds) can start its
  mini-plan now that `Arena`/`RandomInitPolicy` exist, but stays blocked on
  W3-01's review sign-off per the index.
- **Owner-attention:** Reviewer needed for W3-01 — read the diff vs. the
  ticket and plan, check the forbidden-shortcut register, confirm the test
  pins (N=5/10/26 geometry, density sweep 3–200, occupancy-cap, init
  determinism).
- **Next step:** independent review of W3-01 → flip W3-01 in `00_INDEX.md` →
  W3-02 fully unblocked.
- **Five-minute test:** `uv run pytest tests/unit/test_grid_geometry.py
  tests/unit/test_random_init_policy.py -q` → 12 passed;
  `python -c "from wocbots.arena import Arena, RandomInitPolicy"`.

## PRIOR (2026-07-25, W1 DATA stream merged into this tree — needs review)

- **Done:** Reconciled the W1 DATA-stream tree (drafted independently on a divergent branch, never committed,
  no shared git history with this tree) into `develop` by file-level merge — no `git merge` was possible, so
  every overlapping file was diffed and resolved by hand, then validated by actually running the check suite.
  Brought in: `src/wocbots/data/{provenance,hollywood,labels,splits,anchor_analysis}.py`,
  `tests/unit/data/` (6 files) + `tests/fixtures/{tmdb5000,movielens20m}/`, `data/DATA_PROVENANCE.md`,
  `docs/WAVE_GUIDE.md`, and the completed `tickets/W1-04_labels-validation-gate.md` /
  `tickets/W1-06_anchor-analysis.md` (over develop's blank templates). Rewrote `src/wocbots/data/__init__.py`
  (was a placeholder stub) to export the public API, matching the sibling-package convention. Two real
  conflicts had to be resolved, not just copied over: (1) `splits.py`/`anchor_analysis.py` called
  `numpy.random.default_rng()` directly, which trips the W0-04 RNG-discipline guard (only
  `experiments/harness.py` may originate a Generator) — refactored both to take a threaded
  `rng: np.random.Generator` param instead (mirrors `agents/classifier.py`'s `_seed_from` pattern); the W1
  tests that called `make_split(..., seed=N, ...)` / `rank_features(..., seed=N)` were updated to pass
  `rng=np.random.default_rng(N)`. (2) `pyproject.toml` was missing `scipy` (used by `anchor_analysis.py`'s
  point-biserial correlation) and `pandas-stubs` (mypy-strict needs it now that `data/` imports pandas) — added
  both, plus a named `scipy.*` mypy override alongside the existing `sklearn.*` one, and regenerated `uv.lock`
  (`uv lock`) so the two stay in sync. Also dropped `data/hollywood_features_labeled_variant_a.csv`, which the
  W1 tree carried but which contradicts this repo's own `.gitignore`/`data/README.md` policy (derived CSVs are
  never committed — only `DATA_PROVENANCE.md` belongs in `data/`) and isn't documented anywhere as an intended
  deliverable; looked like session scratch output. ~40 W1 test functions got `mypy --strict` return/param
  annotations they were missing (develop's test suite is fully strict-typed; W1's wasn't). Check suite green
  via the documented `uv` workflow: `uv run ruff check .` / `uv run ruff format --check .` / `uv run mypy src
  tests` all clean; `uv run pytest -q` → **156 passed, 11 skipped, 1 xfailed** (the xfail is W1-04's own
  documented class-balance pin, not new). The pre-existing git-repo-dependent test failures in
  `test_harness.py`/`test_manifest.py`/`test_provenance.py` (they shell out to `git rev-parse HEAD`) are
  unrelated to this merge — confirmed identical on unmodified `develop` before touching anything; they'll pass
  once this lands inside a real git checkout.
- **In flight / blocked:**
  1. **Carried forward, still open — W1-04's gate is escalated, not closed; W1-02 is still blocked.** Merging
     the code did NOT resolve this. Variant (a) `revenue > 2×budget` label balance measured 43.9/56.1 against
     the spec's published 47.5/52.5 (±1pt tolerance) — outside tolerance, root-caused (not confirmed) in
     `data/DATA_PROVENANCE.md` §6 to a likely MovieLens `link.csv`/`movie.csv` snapshot-vintage mismatch. W1-02
     (the `antevorta-db` ground-truth reconciliation that would confirm or refute this) never ran — no
     `antevorta-db` source or built SQLite has been supplied. **No label has shipped.** W1-06's anchor ranking
     (`budget` ranks last against spec's §9.2 expectation that it tops the list) is provisional for the same
     reason and hasn't been re-run against a validated label.
  2. W2-03's own upstream note (see the demoted entry below) — the Hollywood crowd configs
     (`configs/crowd_hollywood_*.yaml`) encode `budget` as anchor **provisionally**, pending exactly this. That
     dependency is now unblocked at the code level (the DATA modules exist) but not at the data-quality level
     (item 1 above) — re-running W1-06 for real numbers is still gated on W1-02/a stakeholder ruling.
  3. This merge itself has had no independent review (preamble §8) — I (Claude) did both the reconciliation and
     its own validation; that doesn't count. Not committed (AI sessions don't commit).
  4. W2-03 is also still pending its own independent review, unchanged by this merge (see demoted entry).
- **Owner-attention (Dr. Grimes / the team):**
  1. Same asks as the W1 branch originally raised, still outstanding: supply `antevorta-db` (source or built
     SQLite) to unblock W1-02, or rule on how to proceed without it; rule on whether the W1-04 join shortfall
     (4,227 matched movies vs. spec reference 4,722) is a data-vintage issue, a pipeline defect, or grounds to
     accept revised reference numbers for this dataset snapshot.
  2. A human or different-AI reviewer (not this session): check the merge diff, in particular (a) whether
     dropping `hollywood_features_labeled_variant_a.csv` was the right call, and (b) the `seed: int` →
     `rng: Generator` signature change to `make_split`/`rank_features` — a real API change, not a mechanical
     port, worth a second pair of eyes before anything downstream (W2-04, W5-*) builds on it.
  3. Rutvij: W2-03 still needs committing per its own closing report, independent of this merge.
- **Next step:** get an `antevorta-db` artifact (or a stakeholder ruling on the MovieLens snapshot question)
  to unblock W1-02, then re-run the W1-03→W1-04 chain for real and choose/ratify a shipped label; re-run W1-06
  once that lands. In parallel, get this merge independently reviewed and committed.
- **Five-minute test:** `uv sync && uv run pytest -q` → expect `156 passed, 11 skipped, 1 xfailed` (needs a
  real git repo for the harness/manifest/provenance tests to pass; they'll show as failures with `fatal: not a
  git repository` in a bare working copy — that's the pre-existing baseline, not new). `uv run mypy src tests`
  → `Success: no issues found`. If `src/wocbots/data/hollywood.py` is absent, this entry is stale — fix it
  FIRST.

## PRIOR (2026-07-20, W2-03 implemented on branch, pending review)

- **Done:** W2-03 (feature-assignment policy + crowd builder) implemented on
  `rootwij/w2-03-feature-assignment-crowd` (based off `w2-02-classifier-train-eval`; implementer: Claude
  session driven by Rutvij — preamble §8 review independence). Paths: `src/wocbots/agents/crowd.py`
  (`AssignmentPolicy` seam + `SeededRandomAssignment` (§5.1) / `ExplicitAssignment`; `CrowdConfig` +
  `SeededAssignmentConfig` / `ExplicitAssignmentConfig` / `AgentGroup` with `from_yaml`; `build_crowd`
  config→roster→train_crowd→prune; `CrowdManifest` + `write_/read_crowd_manifest`),
  `configs/crowd_hollywood_26agent.yaml` (§9.3 seeded 1/5/10/10 mix), `configs/crowd_hollywood_5agent.yaml`
  (§9.2 explicit matched crowd), `configs/crowd_smoke.yaml` (synthetic, runnable), and
  `tests/unit/test_w2_03_crowd.py` (30 tests: the 3 ticket reqs + §10.9 barrier + edges). Assignment yields
  feature-name rosters only (decoupled from agent internals — the forbidden shortcut); one Generator threads
  deal→train so same config+seed ⇒ byte-identical crowd manifest; `revenue` barred at config validation AND by
  the builder's roster guard (§10.9). Check suite green (ruff / ruff-format / mypy-strict / pytest:
  **112 passed, 1 skipped**, the skip = W2-02's W1-05 slow band test). No source outside this ticket touched
  (`agents/__init__.py`, `pyproject.toml`, W2-02 modules all unchanged). Pure-mechanism ticket: results
  manifest N/A. Closing report: `../W2-03_feature-assignment-crowd_CLOSING-REPORT.md`.
- **In flight / blocked:** W2-03 close blocked on independent review (§8 — NOT Rutvij or this Claude lineage;
  a CORE teammate reviewing AGENTS, or a different AI e.g. Codex). Upstream: **W1-06 (the anchor RESULT) is
  unfilled** and the W1 DATA wave hasn't landed — so the Hollywood configs encode the spec-named anchor
  (`budget`, §5.1) + §9.2 columns as **provisional**, and W2-04's real §9.2 reproduction stays gated on W1-05
  (eval slice) + W1-06 (final anchors/column names). W2-02 is likewise implemented-but-unreviewed on its branch.
- **Owner-attention:** (1) Reviewer (CORE/consumer-reviews-producer, or Codex): read the full W2-03 diff vs the
  ticket, check the forbidden-shortcut register (assignment⊥internals; §10.9 barrier) against the code, confirm
  the test pins (26-agent mix, prune integration, determinism). (2) DATA: W1-05 + W1-06 unblock W2-04's
  reproduction and let the Hollywood configs' names be finalized. (3) Rutvij: commit the branch (recipe in the
  closing report §5) — add only the 5 W2-03 paths + this handoff; **do NOT stage `README.md`** (CRLF mount
  noise, not a real change).
- **Next step:** independent review of W2-03 → flip W2-03 in `00_INDEX.md` to `✅ (reviewed: <who>, <date>)` →
  W2-04 / W5-02 unblock.
- **Five-minute test:** `pytest -q` → 112 passed, 1 skipped; `ls src/wocbots/agents` → `__init__.py agent.py
  classifier.py crowd.py training.py`; `python -c "from wocbots.agents.crowd import build_crowd, CrowdConfig"`
  imports clean; `git log w2-02-classifier-train-eval..rootwij/w2-03-feature-assignment-crowd` non-empty once
  committed. If `crowd.py` is absent or the index shows W2-03 ✅, this entry is stale — fix it FIRST.

## PRIOR (2026-07-17, W2-01 implemented, pending mini-plan ratification + review)

- **Done:** W2-01 (Agent state + public profile) implemented per its mini-plan
  (`W2-01_agent-state-profile_MINIPLAN.md`, drafted 2026-07-16, DRAFT — its proposed Q1–Q6 rulings are
  applied but NOT yet ratified; implementer: Claude session driven by Rutvij — preamble §8 review
  independence). Paths: `src/wocbots/agents/agent.py` (`ConfidenceWeights`, `HOLLYWOOD_WEIGHTS`,
  `Agent` with the §2 table + §6.5 `public_profile()` + §6.6 `reset_certainty()`),
  `src/wocbots/agents/__init__.py` (stub replaced, seam import path unchanged),
  `tests/unit/test_w2_01_agent_state.py` (15 tests incl. the ticket's 1e-12 init pins). One mechanical
  completion to adjudicate at review (the W0 D1/D2 pattern): `test_w0_02_seams.py`'s Agent-stub
  assertion retired (the stub no longer exists — its contract said W2-01 replaces it). Check suite
  green locally: 36 passed, ruff check + format clean, mypy strict clean. Pure-code ticket: results
  manifest N/A (mini-plan §2-S6).
- **In flight / blocked:** W2-01 close blocked on: (a) mini-plan Q1–Q6 ratification + independent
  review (must not be Rutvij or this Claude lineage — CORE teammate or a different AI system), (b) PR
  review + merge to `develop`, (c) index flip with a `reviewed:` line. Separately, W0-01/W0-02
  governance close-out was never done: PR #11 merged with NO recorded independent review, index not
  flipped, `AGENT_HANDOFF` was stale until this entry, STEP-0 RESULT blocks still unfilled, CODEOWNERS
  handles still `*-TBD`, GitHub issues #2/#3 (W0-01/02) still open. PR #13 (W0-03/04) has no filled
  template and no reviewer.
- **Owner-attention:** (1) CORE (Anurag): ratify/adjust the W2-01 mini-plan's Q1–Q6, review the W2-01
  PR; also a post-merge review of PR #11 so W0-01/02 can flip with a `reviewed:` line. (2) Team: fill
  both STEP-0 RESULT blocks (named-and-dated), send GitHub handles for CODEOWNERS. (3) EVAL: review
  PR #13 (consumer-reviews-producer). (4) Stakeholder: O8 branch protection now that CI exists, and on
  `develop` too if it stays the integration branch (ruling wanted: is `develop` official? Nothing in
  the control plane names it).
- **Next step:** Rutvij (native git, not the sandbox): `git fetch origin`, `git switch -c
  w2-01-agent-state origin/develop`, commit ONLY `src/wocbots/agents/`, the two test files, and this
  handoff (the tree shows ~58 CRLF-noise "modified" files — do NOT `git add -A`), push, open a PR to
  `develop` with the template filled, Q1–Q6 listed for ratification in the PR body.
- **Five-minute test:** `uv run pytest -q` → 36 passed; `grep -l current_prediction
  src/wocbots/agents/agent.py` non-empty. If the index shows W2-01 ✅ or `agents/agent.py` doesn't
  match the description above, this entry is stale — fix it FIRST.

## PRIOR (2026-07-16, W0-01 + W0-02 implemented on branch, pending ratification + review)

- **Done:** W0-01 and W0-02 implemented per their APPROVED plans, on branch `w0-scaffold` (implementer:
  Claude session driven by Rutvij — this identity matters for preamble §8 review independence). Paths:
  `pyproject.toml`, `CODEOWNERS` (root — S4 location ruling), `.github/pull_request_template.md`,
  `.github/workflows/{ci,scheduled}.yml`, `src/wocbots/__init__.py` (+ 7 package `__init__.py`),
  `src/wocbots/types.py`, `src/wocbots/protocols.py`, Agent/Arena constructor-only stubs,
  `tests/unit/test_scaffold.py` (W0-01 §10 pins), `tests/unit/test_w0_02_seams.py` (W0-02's 3 test
  requirements), README S6 sections. Check suite green locally (22 tests; ruff 0.15.22 / mypy strict /
  full + `-m "not slow"` variants). Two mechanical plan completions flagged for review: D1 build backend
  (hatchling — plan §7-S2 omits one; §10.4 import pin needs it), D2 `types-pyyaml` dev dep (mypy strict).
  Separately: Rutvij's W2-01 mini-plan drafted (outside the repo), AGENTS stream.
- **In flight / blocked:** `uv.lock` not yet generated (sandbox had no PyPI route) — Rutvij runs `uv lock`
  before committing; STEP-0 RESULT blocks NOT filled — the code assumes the recommended defaults
  (O2–O5, O7–O9), proposal circulated to the team 2026-07-16; CODEOWNERS handles are `*-TBD`
  placeholders; O8 branch protection + Actions enablement need a repo admin (stakeholder), applied AFTER
  ci.yml lands (§6.4 sequencing ruling); ticket closes blocked on independent review (must not be Rutvij
  or this Claude session's lineage — a teammate or a different AI system, e.g. Codex).
- **Owner-attention:** (1) Team: ratify O2–O5/O7–O9 (adopt-defaults proposal from Rutvij), fill both
  RESULT blocks named-and-dated, send GitHub handles for CODEOWNERS. (2) Stakeholder: confirm Actions
  enabled; apply O8 protection once `checks` exists; adjudicate the D1/D2 completions at review.
  (3) CORE/EVAL: this was your ticket — review the PR (preamble §8) and pair on the close.
- **Next step:** team ratifies STEP-0 → fill RESULT blocks → `uv lock` → Rutvij pushes `w0-scaffold` →
  draft PR (W0-01 + W0-02, template filled) → independent review → merge → index status flips with
  `reviewed:` lines → W2-01/W3-01 unblock.
- **Five-minute test:** `ls src/wocbots` → 10 entries (7 packages + `__init__.py`, `types.py`,
  `protocols.py`); `uv run pytest -q` → 22 passed (slow dummy included); `git log main..w0-scaffold`
  non-empty. If main already contains these files or the index shows W0-01/W0-02 ✅, this entry is stale —
  fix it FIRST.

## PRIOR (2026-07-07, repo bring-up)

- **Done:** Repository created by the stakeholder (**PUBLIC**, MIT-licensed). Pre-laid: directory skeleton,
  seed `.gitignore`, `README.md`, control documents (`CLAUDE.md`, `AGENTS.md`, this file,
  `docs/agent_prompts/`). Ticket set in `tickets/` (index v1.11: 42 tickets, 9 waves, 5 streams); spec at
  `docs/WoC-Bots_Implementation_Spec.md` (**v1.2**). The Codex control-plane review (preamble §8's first
  live execution) is folded in: ten findings accepted — four spec method rulings (arena capacity,
  exact-arithmetic example, prior_accuracy totality, small-N swarm fallback) + process fixes — full
  disposition in `tickets/02_CODEX_CONTROL_PLANE_REVIEW_2026-07-07.md`. Stakeholder rulings live in the
  index changelog (v1.2–v1.11) and the W0-01 plan §12.
- **In flight / blocked:** No code exists; no ticket has started. Nothing is blocked: the W0-01 AND W0-02
  plans are **APPROVED (stakeholder, 2026-07-07)** — W0-02's was authored by Codex and reviewed by Claude
  (the first AI→AI plan review; disposition in its banner + index v1.13). The only gate before W0-01 code
  is the team's own STEP-0; W0-02 additionally waits on W0-01 ✅. **The project is now paused for the
  students to read through everything** (stakeholder, 2026-07-07).
- **Owner-attention:** (1) Team: run the W0 STEP-0 ruling meeting — the wave plan's O1–O6 (O1 and O6
  already ruled by fact: the repo exists, MIT license landed) and the W0-01 plan's O7–O9; record rulings in
  both RESULT blocks. (2) Team: fill stream-owner GitHub handles (index streams table → the plan's
  CODEOWNERS §7-S4).
- **Next step:** the STEP-0 meeting, then CORE + EVAL implement W0-01 while DATA starts W1-01 (no
  blockers) and AGENTS/ARENA draft their W2-01/W3-01 mini-plans.
- **Five-minute test:** `ls tickets/ | wc -l` → 48 files (42 tickets + index + preamble + 3 plans + the
  02_ review doc); the FIRST changelog entry in `tickets/00_INDEX.md` is v1.13 (the W0-02 plan, Codex-
  authored, approved). If the newest changelog entry or the git history describes work this CURRENT STATE
  doesn't mention, this handoff is stale — fix it FIRST.
