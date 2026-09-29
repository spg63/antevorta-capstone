# W2-03 — Feature-assignment policy + crowd builder: implementation & close report

**Mode:** IMPLEMENT. **Implementer:** Claude session driven by Rutvij (this identity matters for
preamble §8 review independence — the reviewer must not be this lineage). **Date:** 2026-07-20.
**Ticket:** `tickets/W2-03_feature-assignment-crowd.md`. **Binding spec:** §5.1 (assignment), §9.3
(reference compositions); also §5.3/§9.2/§10.9 for the machinery it reuses.
**Branch:** `rootwij/w2-03-feature-assignment-crowd` (based on `w2-02-classifier-train-eval`).

Everything below is left **uncommitted** in the working tree for your review, per the repo's "humans
commit" rule (preamble §6.7: agent sessions don't commit/push unless asked). Nothing was committed or pushed.

---

## 1. What landed

One new source module, three named configs, and one test module — the feature-assignment policy behind a
seam plus the crowd builder, sitting on top of W2-02's train/eval/prune machinery (untouched).

| File | Purpose | Spec |
|---|---|---|
| `src/wocbots/agents/crowd.py` (new) | `AssignmentPolicy` seam + `SeededRandomAssignment` (§5.1) and `ExplicitAssignment`; `CrowdConfig`/`SeededAssignmentConfig`/`ExplicitAssignmentConfig`/`AgentGroup` (validated, `from_yaml`); `build_crowd` (config→roster→train_crowd→prune); `CrowdManifest` + `write_/read_crowd_manifest`. | §5.1, §9.3, §10.9 |
| `configs/crowd_hollywood_26agent.yaml` (new) | §9.3 26-agent mix (seeded: 1×5 / 5×4 / 10×3 / 10×2, budget-anchored). | §9.3 |
| `configs/crowd_hollywood_5agent.yaml` (new) | §9.2 matched 5-agent crowd (explicit: four budget-anchored 2-feature agents + one 5-feature). | §9.2 |
| `configs/crowd_smoke.yaml` (new) | Dataset-agnostic smoke config (f0..f4) so the whole path runs on synthetic data before W1. | preamble §0.3 |
| `tests/unit/test_w2_03_crowd.py` (new) | The three ticket test requirements + edges + the §10.9 barrier (30 tests). | §4 test discipline |

**Not touched:** `agents/__init__.py` (submodule imports, consistent with W2-02), `pyproject.toml` (no new
deps or mypy overrides — `crowd.py` only reaches sklearn transitively through the already-covered W2-02
modules), and W2-02's `classifier.py`/`training.py` (reused as-is; feature assignment stays *out* of agent
internals — the ticket's forbidden shortcut).

Design notes worth your eye at review:

- **Assignment is decoupled from agent internals (forbidden shortcut).** `AssignmentPolicy.assign(rng)`
  returns a *roster* — a `tuple[tuple[str, ...], ...]` of feature NAMES — and nothing else. No agents, no
  classifiers, no training. The builder then hands that roster to W2-02's `train_crowd`. A test pins that the
  roster contains only strings.
- **The seeded policy honours §5.1 exactly.** Every agent gets the anchor set; the remainder is dealt from
  the pool *without replacement within an agent* (distinct columns) but *independently across agents*
  (duplicate feature sets allowed — a test forces and asserts duplicates). It calls no RNG of its own; it only
  advances the passed `Generator` via `rng.choice` (a method call — the W0-04 RNG guard stays green, verified).
- **Determinism threads through one Generator.** `build_crowd` deals features from the same `Generator` it
  then passes to `train_crowd` for per-agent classifier seeds. Same config + same seed ⇒ byte-identical
  `CrowdManifest` (pinned).
- **The sanity agent is structurally unreachable from this path (§10.9).** `revenue` (the single source of
  truth is `training.LEAKY_FEATURES`) is rejected at *config validation* — a YAML naming it cannot even load —
  and `build_crowd` re-checks the roster before training (defense in depth against a rogue policy). Both are
  tested. The budget+revenue canary remains reachable only via W2-02's `build_sanity_agent`.
- **Crowd composition is pure config.** The §9.3 compositions ship as named YAML; `CrowdConfig.from_yaml`
  loads and validates them. Adding an experiment is a config file, not code (the acceptance criterion).

## 2. Check suite — green

Run in a Python-3.10 sandbox (the repo targets ≥3.11; a local-only `sitecustomize` shim backfilled the 3.11
`datetime.UTC` alias so the existing harness/provenance import — that shim is **not** part of the delivery,
same posture as W2-02). mypy pinned to the 1.x line the repo targets (`mypy==1.14.1`; the sandbox's default
2.3.0 hit an unrelated internal error) and pointed at `--python-version 3.11`.

```
ruff check .            → All checks passed!
ruff format --check .   → 32 files already formatted
mypy --python-version 3.11 src tests → Success: no issues found in 32 source files
pytest                  → 112 passed, 1 skipped   (was 82 before W2-03: +30 tests)
```

Stable across 3 back-to-back runs (determinism is by construction; nothing flakes). The one skip is W2-02's
`test_reference_bands_real_data` (`@pytest.mark.slow`, W1-05 not landed) — unchanged by this ticket.

Independent value-level spot check:

```
26-AGENT MIX   total=26  histogram={2:10, 3:10, 4:5, 5:1}   all budget-anchored, only legal features
EXPLICIT 5-AGENT roster exact & ordered (budget+vote_count … budget+all5)
DETERMINISM    same seed → byte-identical manifest: True
PRUNE INTEGR.  trap agent → eval_accuracy 0.0 → pruned+logged; survivors intact; n_assigned=kept+pruned
LEAK GUARD     revenue rejected at config load AND by the roster guard (ValueError/ValidationError)
```

## 3. Mapping to the ticket's three test requirements

1. **Invariants** — `test_seeded_anchors_in_every_agent`, `test_seeded_multi_anchor_present_in_every_agent`
   (anchors in every agent); `test_seeded_only_legal_features_dealt` (nothing outside anchors ∪ pool; distinct
   within an agent); `test_seeded_roster_deterministic_under_seed` + `test_build_crowd_manifest_deterministic`
   (deterministic under seed — roster AND full manifest); `test_seeded_roster_seed_actually_threads` (seed
   really threads — not a constant).
2. **Roster expressiveness** — `test_26_agent_mix_constructs_exactly` (the §9.3 mix constructs to exactly
   total 26 / histogram {2:10, 3:10, 4:5, 5:1}); `test_explicit_roster_is_exact` (explicit rosters reproduce
   an exact, ordered feature-set list — what W2-04 needs). Plus `test_duplicate_feature_sets_allowed`.
3. **Pruning integration** — `test_bad_agent_prunes_without_disturbing_manifest`: a deliberately-bad "trap"
   agent (learns the train split, inverted on eval ⇒ eval_accuracy 0.0) prunes; the manifest records it in
   `pruned` with its reason, the survivors sit in `agents`, and `composition` reconciles
   (n_assigned = n_kept + n_pruned) with the full roster still recorded in order.

Forbidden-shortcut + edge coverage: `test_leaky_feature_rejected_in_seeded_config`,
`test_leaky_feature_rejected_in_explicit_config`, `test_build_crowd_rejects_leaky_roster_defense_in_depth`
(§10.9 barrier); `test_assignment_returns_only_feature_names` (assignment ⊥ agent internals);
`test_anchor_count_bounds` (§5.1's 1–4), `test_seeded_dealt_exceeds_pool_rejected`,
`test_seeded_n_features_below_anchor_count_rejected`, `test_anchors_and_pool_must_be_disjoint`,
`test_explicit_declared_anchor_must_be_in_every_agent`; `test_example_configs_load`,
`test_smoke_config_builds_end_to_end`, `test_crowd_manifest_json_roundtrips`,
`test_crowd_manifest_records_architecture_for_mlp`, `test_assignment_policies_satisfy_the_seam`.

## 4. Open items / things for the reviewer

- **W1-06 dependency is not satisfied (disclosed, not silently worked around).** The ticket is blocked-by
  W1-06 (the anchor RESULT), which is unfilled — the whole W1 DATA wave hasn't landed. Following the W2-02
  precedent (proceed on synthetic; defer real-data reproduction), the Hollywood configs encode the anchor the
  spec itself names — `budget` (§5.1: "in practice, budget is the anchor feature every agent gets") — and the
  §9.2 five-feature column set, marked **provisional** in the config comments. W2-04's actual §9.2 reproduction
  is gated on W1-05 (the eval slice) **and** W1-06 finalizing the exact anchor set + real column names. No
  anchor RESULT was fabricated. If the team would rather I *not* ship Hollywood-named configs until W1-06 is
  filled, that's a one-line revert of the two `crowd_hollywood_*.yaml` files (the mechanism + smoke config
  stand alone).
- **`n_features` vs a size-list.** I expressed §9.3 as `groups: [(count, n_features)]` because it reads exactly
  like the spec ("N agents at M features"). An explicit per-agent size list is equivalent and could be added
  later behind the same seam if a config ever wants irregular sizes; flagging in case you'd prefer that shape.
- **Crowd manifest ≠ results manifest.** W2-03 is a mechanism ticket (like W2-02): no *experiment* ran, so no
  results manifest is owed (§6.3 N/A). The `CrowdManifest` is the crowd's own artifact; a sample rendered from
  `crowd_smoke.yaml` is in the PR description below. The committed results manifest arrives with W2-04.
- **`README.md` shows ` M` in `git status`** — that's a pre-existing CRLF line-ending artifact of the
  Windows-checkout/Linux-sandbox mount, **not** a change of mine. Do **not** `git add` it. Add only the five
  W2-03 paths (§5).

## 5. Branch recipe (run on your machine, where git is unconstrained)

The branch `rootwij/w2-03-feature-assignment-crowd` already exists (created this session off
`w2-02-classifier-train-eval`). Add only the five W2-03 paths:

```bash
git switch rootwij/w2-03-feature-assignment-crowd
git add src/wocbots/agents/crowd.py \
        configs/crowd_hollywood_26agent.yaml \
        configs/crowd_hollywood_5agent.yaml \
        configs/crowd_smoke.yaml \
        tests/unit/test_w2_03_crowd.py \
        AGENT_HANDOFF.md            # updated this session (see §7)
git status                          # confirm README.md is NOT staged (CRLF noise)
pytest                              # expect: full suite green, 1 slow test skipped (W1-05)
git commit -m "W2-03: feature-assignment policy + crowd builder (§5.1/§9.3); sanity agent barred (§10.9)"
```

## 6. Remaining close-checklist items (yours / a second set of eyes)

- ☐ **Independent review (§8)** — the hard gate. Not this Claude session's lineage and not you-as-implementer;
  a teammate (consumer-reviews-producer: CORE reviews AGENTS) or a different AI (e.g. Codex), findings
  adjudicated by a human. This is what flips the ticket ✅.
- ☐ **`00_INDEX.md` status flip** with `✅ (reviewed: <who/what>, <date>)` — after review. (Left unflipped; I'm
  the implementer.)
- ☑ Tests land with the feature (same change set). ☑ Check suite green. ☑ No spec discrepancy found (§5.1/§9.3
  and the ticket agree). ☑ `AGENT_HANDOFF.md` updated (§7). Results manifest: N/A (no experiment ran).

## 7. Sample crowd manifest (from `crowd_smoke.yaml`, seed 7)

```json
{
  "name": "crowd_smoke", "policy": "seeded", "anchors": ["f0"], "schema_version": 1,
  "composition": {"n_assigned": 6, "n_kept": 6, "n_pruned": 0, "size_histogram": {"2": 3, "3": 2, "5": 1}},
  "agents": [
    {"features": ["f0","f1","f3","f2","f4"], "eval_accuracy": 1.0, "eval_precision": 1.0, "eval_recall": 1.0,
     "certainty": 1.0, "trust_score": 1.0, "confidence": 1.0, "architecture": [32, 32]},
    "… five more kept agents (2- and 3-feature), each with metrics + initialized §2 state …"
  ],
  "pruned": [],
  "roster": [["f0","f1","f3","f2","f4"], ["f0","f1","f3"], "… full assigned roster, in order …"]
}
```
