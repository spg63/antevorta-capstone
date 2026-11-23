# W1-06 — Feature-correlation anchor analysis — IMPLEMENTATION PLAN

> **STATUS: APPROVED — stakeholder, 2026-11-16.** The stakeholder ruled that Hollywood retains
> `budget` as its shared anchor to preserve the §9.2 reference setup if the ranking disagrees.

**Ticket:** W1-06_anchor-analysis.md  
**Wave:** W1 (DATA)  
**Blocked by:** W1-05 — ✅ (reviewed: Zain, 2026-11-16)  
**Blocks:** W2-03  
**Binding spec sections:** §5.1, §9.2  
**Binding preamble sections:** §0, §2–6, §8  
**Severity:** 🔴 — anchors affect every downstream Hollywood crowd.  
**Ruling authority:** stakeholder, if measured evidence contradicts the expected anchors.

---

## 1. Metadata

This plan follows full reads of the ticket, binding spec sections, preamble, current handoff state, W1 index row, and existing W1-05/W1-06 paths. There is no prior W1-06 plan. The inherited rank_features helper and synthetic test do not establish completion: there is no train-split runner, ranking artifact, or RESULT.

## 2. Why this ticket exists

Every agent shares the anchors, so this configuration choice changes every Hollywood crowd. W1-06 must produce a reproducible train-only record that W2-03 can consume without rerunning analysis per experiment.

## 3. Decisions

- Rank features by descending absolute point-biserial correlation. Report PCA loadings alongside; do not invent an unspecified combined score.
- Add a small scripts/ analysis command backed by an importable runner in wocbots.data.anchor_analysis. It is an artifact path, not a toolkit runtime path.
- The runner loads the persisted W1-05 artifact, validates it against the labeled SQLite source, and selects exactly train_ids. It neither creates splits nor accepts arbitrary production dataframes.
- Commit results/manifests/w1_06_anchor_analysis.json, with aggregate scores and provenance only, never source rows.
- Keep current budget anchors provisional until evidence is reviewed. Escalate an expectation mismatch; do not silently re-anchor.

## 4. Verified grounding facts

- Spec §5.1 permits 1–4 shared highly correlated anchors and requests point-biserial and/or PCA analysis once per dataset; it expects budget and vote_count to lead.
- Spec §9.2 reference agents and crowd are budget-anchored.
- W1-05 SplitArtifact records memberships, source fingerprint, feature columns, and a schema-2 content digest. validate_split_source proves source identity and train-only scaler derivation.
- load_labeled_sqlite provides stable _rowid keys. DEFAULT_FEATURE_COLUMNS are the nine eligible features; revenue defines the label and is excluded.
- The checked local data/derived/split_v1.json is schema 1 while the merged loader requires schema 2; regenerate it before real analysis.
- The inherited helper computes correlation and min-max-scaled PC1 loadings but does not establish train-only membership or emit an artifact.

## 5. Execution-path map

~~~text
labeled SQLite + persisted schema-2 W1-05 split
  └─ load + validate source/split
       └─ rows whose _rowid is in train_ids only
            └─ seeded rank_features()
                 └─ correlation + PC1 ranking
                      └─ W1-06 JSON artifact
                           └─ ticket RESULT + stakeholder anchor ruling
                                └─ W2-03 Hollywood config anchors
~~~

## 6. Pre-code gates

1. Re-verify W1-05 schema-2 behavior and regenerate its local ignored artifact without changing memberships.
2. Confirm source and regenerated split pass validate_split_source.
3. Define artifact fields for seed, git SHA, source fingerprint, and split digest.
4. If budget/vote_count do not lead, record the failed expectation and obtain a stakeholder ruling before config changes or closure.

## 7. Specification

### src/wocbots/data/anchor_analysis.py

- Validate requested columns, numeric/finite features, binary labels, and degenerate inputs; reject invalid data instead of emitting NaN rankings.
- Preserve point-biserial r, p-value, PC1 loading, and absolute values as separate fields.
- Sort deterministically by descending absolute correlation then feature name for ties.
- Add a runner accepting paths, seed, and output path; it validates the split, isolates train membership, ranks, and writes canonical JSON atomically.

### scripts/run_w1_06_anchor_analysis.py

- Default to the labeled SQLite, data/derived/split_v1.json, seed 42, and W1-06 manifest path.
- Be the sole seed origin and pass its Generator to the helper.
- Print a concise top-six summary; JSON contains the complete ranking.

### Artifact, ticket, and configs

- Commit results/manifests/w1_06_anchor_analysis.json with ticket ID, schema, root seed, git SHA, source fingerprint, split digest, features, train count, ranking, and chosen-anchor/ruling status.
- Fill RESULT from that artifact.
- Only after a ruling, update both Hollywood crowd configs to the chosen 1–4 anchors and remove provisional language. Record any rationale for retaining budget despite contrary ranking.

## 8. Observability

The JSON artifact is the audit record. Source fingerprint and split digest identify the training population; seed and git SHA make the analysis reproducible. The ticket RESULT points to it.

## 9. Sequenced implementation steps

1. Add helper validation, deterministic order, and train-only runner.
2. Add CLI and canonical artifact writer.
3. Add focused tests before real-data execution.
4. Regenerate approved W1-05 split locally and run W1-06 once.
5. Fill RESULT honestly and escalate mismatch.
6. Apply stakeholder config ruling, if issued.
7. Commit artifact, run checks, obtain independent review, and complete closure bookkeeping.

## 10. Test plan

- Smoke: synthetic labeled source plus persisted split emits an artifact, identifies train membership, and ranks synthetic budget in the top set.
- Determinism: same source, split, and seed produce byte-identical canonical JSON.
- Leakage guard: source/split mismatch is rejected before ranking.
- Input guard: missing feature, non-binary label, non-finite feature, and constant feature fail explicitly.
- Stable tie: equal absolute correlations sort by feature name.
- Expand inherited helper test to assert PCA fields and all requested features.

## 11. Blast radius

W2-03 consumes selected anchors in both Hollywood configs. W2-04 and W5 reference experiments depend on this configuration. No agent, arena, aggregation, or evaluation mechanism changes.

## 12. Risks, alternatives, open questions

- **[High] Expected-anchor mismatch:** index history reports budget last at r = 0.0224. Re-run only through the validated schema-2 split, document it, and obtain a stakeholder ruling; do not select an alternative autonomously.
- **[High] Stale local split:** schema 1 cannot be consumed by the approved loader. Regenerate through W1-05; do not relax validation or add a legacy fallback.
- **[Medium] PCA sign ambiguity:** signs can invert without changing component meaning. Report signed and absolute values, but rank only by absolute correlation.
- **[Medium] Determinism:** omit wall-clock timestamps from the analysis artifact; use git SHA, config, and seed.

## 13. Definition of Done

1. Schema-2 source/split validation succeeds and analysis uses train rows only.
2. A seeded runner emits a committed ranking artifact with provenance.
3. RESULT lists top-six scores, chosen anchors, and honest expectation status.
4. Any mismatch has stakeholder ruling before configuration changes and closure.
5. Focused tests plus ruff check ., ruff format --check ., mypy src tests, and full pytest pass.
6. Index status gets independent-review sign-off only after review; handoff is updated. No AI commit or push without explicit human instruction.

