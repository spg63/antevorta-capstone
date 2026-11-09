# W1-05 — Splits, normalization, and structural leakage guards — IMPLEMENTATION PLAN

> **READ ME FIRST — status:** **APPROVED by the session driver, 2026-11-08.** The decisions in §3 and
> STEP 0 are implementation authority for this ticket. The spec (`docs/WoC-Bots_Implementation_Spec.md`)
> outranks this plan, and a conflict is a plan bug to report rather than reconcile silently.

**Ticket:** `W1-05_splits-normalization.md`.  
**Wave:** W1. **Blocked by:** W1-04 ✅. **Blocks:** W1-06, W2-02 real-data acceptance criteria, W5-01, W7-01.  
**Binding spec sections:** §4.3.8–9, §10.5, §9.1.  
**Binding preamble sections:** §0 (plan-first and STOP conditions), §2 (one RNG and train-side evaluation),
§3.1 (leakage prohibition), §4 (deterministic numeric tests), §5–6 (check and close gates).  
**Ruling authority:** stakeholder for the closed-W1-04 provenance correction in §3-D4; session driver/team for
the remaining implementation details.

---

## 1. Metadata

This plan was grounded in the W1-05 ticket; the named spec sections; current W1-04 label code/tests and its
reconciliation manifest; the split module/script/tests; and the real-data W2 execution paths. It does not
treat earlier W1 code or manifests as correct merely because they exist.

## 2. Why this ticket exists

The split is a controlled experimental condition, not per-run noise. The same labeled population, membership,
and train-fitted scaler must feed every compared mechanism; otherwise a model, swarm, or baseline can appear
better merely because it received an easier holdout. This ticket makes that condition explicit, persisted, and
structurally hard to bypass.

## 3. Decisions and required rulings

- **D1 — canonical labeled source. ✅ CONFIRMED (session driver, 2026-11-01).**
  `data/processed/movies.sqlite`, table `movies`, is the W1-04 labeled output. Consumers load its persisted
  `label` column; they do not rebuild W1-03 from raw CSVs or recompute labels. The loader rejects
  missing/nonbinary labels, missing required columns, or duplicate SQLite `_rowid` values.
- **D1a — split identity. ✅ CONFIRMED (session driver, 2026-11-08).** SQLite `rowid`, loaded as `_rowid`,
  is the persisted split-membership identity. `tmdbId` is provenance only and need not be unique.
- **D2 — fixed artifact (recommended).** One artifact is built for a named root seed and a fingerprint of the
  canonical labeled source. Ten harness runs reuse that artifact; their child RNGs drive only training and
  later stochastic mechanisms, never split membership.
- **D3 — artifact identity (recommended).** The artifact records the caller-provided root seed (not an opaque
  sklearn sub-seed), source fingerprint, feature list, train/eval/test and fold memberships, train-fitted
  normal-feature min/max values, and the separately sanctioned sanity-only revenue scaler. Loading validates
  the fingerprint and all memberships before a slice is materialized.
- **D4 — closed-ticket provenance correction (STAKEHOLDER RULING REQUIRED BEFORE IMPLEMENTATION).** The
  committed W1-04 reconciliation manifest and its producer still say stakeholder acceptance is pending and
  describe the historical 5× comparison as operative. The ticket and handoff now record the stakeholder's
  2026-10-28 ruling: strict `revenue > 2 × budget` only, no special 5× condition. **Recommended:** refresh
  that compact manifest and its producer/readme wording as a narrow provenance correction in this change,
  without altering the already-correct strict-2× labeling implementation.
- **D5 — revenue boundary (recommended).** Normal `LabeledData` constructed from a split contains only
  `artifact.feature_columns`; it cannot carry `revenue`. A distinct, explicitly named sanity-only data view
  may contain scaled `budget` and `revenue` for `build_sanity_agent` (§9.2/§10.9). This preserves the canary
  while making a normal crowd agent revenue-blind by construction.
- **D6 — cross-stream ownership (required).** `src/wocbots/experiments/` is CORE-owned. DATA owns the split
  artifact and loader; the CORE owner reviews the consumer/config changes before merge.

## 4. Verified grounding facts

- W1-04's local SQLite has 3,032 rows; all 3,032 persisted labels match strict `revenue > 2 * budget`, and
  none is null or outside `{0, 1}`. Its focused tests and W1-05's existing focused tests passed (30 tests).
- `make_split()` correctly creates stratified 80/20 membership, a train-side 90/10 eval carve-out, train-only
  normal-feature min/max values, and five folds over post-eval training rows. Existing unit tests cover
  determinism, stratification, non-train perturbation, folds, round-trip persistence, and the revenue guard.
- The current W1-05 CLI defaults to a nonexistent CSV and `label_a`; its output is absent from `data/derived/`.
- `load_split_artifact()` has no production caller. `materialize_split()` instead calls `make_split()` with
  every run's RNG, while W2-03/W2-04 configs point at `raw_root`; this violates W1-05's fixed-split acceptance
  criterion and W1-04's requirement that downstream consume its labeled output.
- `data/processed/` and `data/derived/` are intentionally ignored. Compact provenance manifests under
  `results/manifests/` are committed deliverables, so the plan records hashes/counts there without committing
  raw rows or split IDs.

## 5. Execution-path map

```
W1-03 feature SQLite → W1-04 labels `movies.label`
    └─ split-builder CLI (root seed, canonical source validation)
         ├─ ignored data/derived/split_<version>.json + .npz
         └─ committed compact W1-05 provenance manifest

W2/W5 experiment YAML (`labeled_sqlite`, `split_artifact`)
    └─ load labeled SQLite + load artifact
         └─ validate source fingerprint and id partition/folds
              └─ materialize normal train/eval/test views (no revenue)
                   └─ materialize explicit sanity-only views (budget + revenue)
                        └─ train/evaluate mechanisms with harness child RNGs
```

No production branch in this map calls `make_split()`. It is a builder-only function.

## 6. Pre-code gate

Before any implementation:

1. D1 is confirmed. Stakeholder/session driver approves D2–D6, especially whether D4's W1-04 provenance
   correction is in scope for W1-05.
2. CORE owner accepts review responsibility for changes below `src/wocbots/experiments/` and real-data YAML
   configurations.
3. Record the approval/date in this plan's RESULT block. If D4 is not approved, leave closed W1-04 files
   untouched and make the W1-05 provenance manifest explicitly state the current stakeholder ruling.

## 7. Specification

### S1 — artifact construction and provenance

- Keep `make_split()` RNG-threaded, but accept/persist the explicit root seed supplied by the builder rather
  than storing an internal sklearn sub-seed as the artifact identity.
- Add validated source fingerprinting over canonical `tmdbId`, `label`, and the selected normal feature values;
  duplicate IDs or incomplete required columns are errors.
- Extend `SplitArtifact` and JSON serialization with source identity and the sanctioned revenue scaler while
  retaining the current NPZ membership layout. Validate JSON/NPZ consistency, disjoint complete membership,
  fold partitioning, feature exclusions, and source fingerprint during load/materialization.
- Make `scripts/build_w1_05_splits.py` default to the labeled SQLite/table and `label`; retain explicit CLI
  overrides for reproducible alternate local locations. It writes ignored artifact files plus a compact,
  committed W1-05 provenance manifest with seed, source hash/fingerprint, membership/fold hashes, scaler
  metadata, git SHA, and no raw rows.

### S2 — safe materialization

- Replace RNG-based production materialization with an artifact-backed API, e.g.
  `materialize_split(labeled: DataFrame, artifact: SplitArtifact) -> HollywoodSplit`.
- `HollywoodSplit` exposes normal `train_data`, `eval_data`, and `test_data` built from the persisted normal
  feature list only. It additionally exposes clearly named sanity-only equivalents solely for the canary path.
- Use the persisted train-fitted normal scaler for every normal slice. Fit/apply the persisted sanity-only
  revenue scaler from normal training IDs only; no eval/test value may affect either scaler.

### S3 — consumer migration

- Update `load_labeled_hollywood()` to load and validate the W1-04 labeled SQLite output, not reconstruct
  features/labels from `raw_root`.
- Update W2-03 crowd and W2-04 agent-table runners plus their real-data YAML configs to require
  `labeled_sqlite` and `split_artifact` parameters. Remove their split regeneration path.
- Route only `build_sanity_agent` to the sanity-only data views. All normal agents/crowds receive normal data,
  so a revenue feature cannot reach them even through a careless caller.

### S4 — W1-04 provenance correction (conditional on D4)

- Update the reconciliation script/manifest and `data/README.md` to state the ratified strict-2× rule and the
  historical/non-operative status of the comparison. Do not introduce a 5× branch into the shipped label.
- Regenerate the compact reconciliation manifest from the existing labeled SQLite only after the tree intended
  for that manifest is otherwise clean, so its SHA and dirty flag are meaningful.

## 8. Observability

The W1-05 compact manifest must identify: builder version, root seed, labeled-source path and SHA/fingerprint,
feature columns, per-split/fold counts and membership digests, scaler parameters/digests, and git SHA. Every
experiment config records the artifact path; runners surface the artifact source fingerprint in their manifest
metrics/provenance-compatible output so incomparable runs cannot be mistaken for comparisons.

## 9. Sequenced implementation steps

1. Complete §6 approvals and record the RESULT below.
2. Add source validation/fingerprinting and strengthen `SplitArtifact` construction, persistence, and loading
   in `src/wocbots/data/splits.py`.
3. Convert the W1-05 builder script to the canonical labeled SQLite input and emit its compact provenance
   manifest; build the single-seed local smoke artifact.
4. Refactor `src/wocbots/experiments/hollywood_data.py` into an artifact-backed labeled-data loader and
   normal/sanity-only materializer.
5. Migrate CORE-owned W2 runners/configs and their tests to require/load the artifact; obtain CORE review.
6. Add the §10 pins, run focused tests, then run the complete check suite.
7. If D4 was approved, refresh W1-04 provenance metadata; otherwise retain its history and record the ruling
   in the W1-05 manifest only.
8. Generate the committed W1-05 provenance manifest, obtain independent review, then update ticket/index/
   handoff per the preamble close checklist. Do not commit or push from an AI session.

## 10. Exact test pins

1. Same explicit root seed and identical labeled frame produce byte-identical artifact membership, fingerprint,
   scaler data, and serialized JSON/NPZ payloads; a different seed changes membership.
2. Train/eval/test are disjoint and complete; sizes are 72%/8%/20% after the eval carve-out; each label rate
   is within one percentage point of the total; every fold partitions post-eval train IDs and touches neither
   eval nor test IDs.
3. Perturb all eval/test normal feature values and prove normal scaler parameters do not change. Independently
   perturb their revenues and prove the sanity-only revenue scaler does not change.
4. Attempt to materialize with a changed source fingerprint, duplicate ID, missing `label`, invalid label, or
   missing feature; each must raise before any data reaches a model.
5. Assert normal materialized `LabeledData.features` never contains `revenue`; assert only the explicitly
   named sanity view contains it and normal crowd construction still rejects it.
6. Monkeypatch `make_split()` to fail, then materialize/run W2-03 and W2-04 from a valid artifact; both must
   succeed, proving consumers load rather than re-split. Conversely, a missing artifact config/path must fail
   loudly.
7. Move an artifact JSON/NPZ pair and confirm it still loads; tamper an NPZ membership or manifest metadata
   and require validation failure.
8. Exercise the CLI on a temporary labeled SQLite fixture: its defaults use `label`, write both artifact files
   and provenance metadata, and reject an unlabeled database.
9. Retain all current W1-05 pins and W1-04 strict-boundary pins; conditional D4 tests pin the refreshed
   stakeholder-ruling metadata without asserting historical 5× behavior as a shipped requirement.

## 11. Blast radius

- **DATA-owned:** `src/wocbots/data/splits.py`, data exports, W1-05 builder, W1 data tests, W1-05 compact
  manifest, and—only if approved—W1-04 reconciliation provenance/readme.
- **CORE-owned (review required):** `src/wocbots/experiments/hollywood_data.py`, W2-03/W2-04 runners, real-data
  configs, and their integration tests.
- **AGENTS-owned consumer surface:** sanity-agent call sites/tests may need a mechanical switch from normal to
  sanity-only data; request AGENTS review if that diff reaches its directory.

## 12. Risks and open items

- The labeled SQLite is ignored local data. A compact committed manifest verifies its identity but cannot
  magically make the data distributable; a fresh environment must rebuild and label it before generating or
  consuming the split artifact.
- The current W1-04 reconciliation manifest is stale (`stakeholder acceptance pending`, dirty worktree, old
  SHA). D4 determines whether its correction ships in this change.
- Existing results/manifests for W2-03/W2-04 used regenerated splits. They remain historical evidence, not
  directly comparable with future fixed-artifact runs; do not overwrite them.
- Replacing a raw-data loader with the labeled SQLite contract is deliberately breaking for callers. Required
  config validation and loud errors are preferable to silently falling back to rebuilding/splitting.

## 13. Definition of done

W1-05 is done only when one canonical labeled source produces a persisted, fingerprinted split/scaler artifact;
all real-data consumers require and validate that artifact; normal matrices structurally exclude revenue; all
ticket pins and the full check suite pass; a compact provenance manifest is committed; independent review is
recorded; and the index/handoff close bookkeeping is complete.

---

## STEP 0 — RESULT

**D1 — CONFIRMED (session driver, 2026-11-01):** W1-05 consumes the persisted `movies.label` column from
`data/processed/movies.sqlite`; it does not rebuild labels from raw CSVs.

**D1a — CONFIRMED (session driver, 2026-11-08):** SQLite `rowid`, loaded as `_rowid`, is split membership
identity; duplicate `tmdbId` values do not cause deduplication or cross-split reuse.

**D2 — APPROVED (session driver, 2026-11-08):** All experiments reuse one persisted split artifact rather
than splitting again per run.

**D3 — APPROVED (session driver, 2026-11-08):** Artifact identity includes root seed, source fingerprint,
memberships, and scaler metadata; mismatched source data is rejected.

**D4 — APPROVED (session driver, 2026-11-08):** Correct the stale W1-04 reconciliation provenance, script,
and README to reflect the strict-2× stakeholder ruling.

**D5 — APPROVED (session driver, 2026-11-08):** Normal agent data structurally excludes `revenue`; only the
named sanity-agent view may contain it.

**D6 — APPROVED (session driver, 2026-11-08):** Update CORE-owned experiment consumers/configuration and
obtain CORE review before merge.
