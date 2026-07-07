# WoC-Bots Reimagined — Ticket Set — INDEX

> **v1.11 (2026-07-07): THE CODEX CONTROL-PLANE REVIEW IS FOLDED IN** — the preamble §8 rule's first live
> execution, run against the governance artifacts themselves. Ten findings, all accepted:
> `02_CODEX_CONTROL_PLANE_REVIEW_2026-07-07.md` (moved to the 02_ slot; full disposition appended there).
> **The spec is at v1.2** with four method rulings: §6.1 arena capacity (near-square rows=floor(sqrt(2N)) ×
> cols=ceil(2N/rows) — the exactly-2N vs ceil-square contradiction resolved in favor of published density);
> §6.5 worked example now EXACT arithmetic (the ticket pin had baked a rounded intermediate — real bug,
> caught); §6.7/§7 prior_accuracy made total (eval-seeded → running at ≥5 scored; 50 votes = no-information
> default only); §10.8 small-N swarm fallback made exact (3–9 → trust-weighted voting @ Low; <3 → degenerate
> rule). Process fixes: W0-01 ticket re-pointed at its dedicated plan; the dedicated plan's self-dependent
> STEP-0 gate re-sequenced (protection + traversal proof move post-CI); O2–O5 status clarified (defaults
> awaiting team STEP-0, not ratified); W3-04 history cardinality ruled (1 encounter row + 2 directed rows);
> handoff and README de-staled. Tickets touched: W0-01, W3-01, W3-03, W3-04, W4-02, W4-03, W6-02.
>
> **v1.10 (2026-07-07): MIT LICENSE landed** at the repo root (stakeholder ruling by fact — O6 closes;
> W0-01's license step becomes a verify). With O1 and O6 both ruled, the team's STEP-0 scope is O2–O5 +
> O7–O9.
>
> **v1.9 (2026-07-07): the repository is PUBLIC** (stakeholder re-ruling, superseding v1.6's
> private-until-publication — rationale: clean-room reimplementation, not the original research code).
> Consequences: free CI minutes and full branch-protection features (the W0-01 plan's R1 dissolves);
> committed fixture excerpts must comply with dataset licenses/ToS (W1-01); and the clean-room boundary is
> now also a PUBLICATION boundary — nothing derived from the stakeholder's private research code may appear
> anywhere in this repo: code, comments, commit messages, issues, or PR text.
>
> **v1.8 (2026-07-07): the W0-01 dedicated plan is APPROVED** (stakeholder). W0-01 is fully startable once
> the team fills its STEP-0 RESULT block (O7–O9 + version captures; O1–O6 shared with the wave plan). No
> DRAFT artifacts remain in the set.
>
> **v1.7 (2026-07-07): PROJECT CONTROL DOCUMENTS added** (adapted from the stakeholder's templates, tuned
> for a less-experienced team — shorter mandatory reads, explicit STOP conditions, fixed fill-in
> structures): `CLAUDE.md` (binding AI-session instructions; `AGENTS.md` points non-Claude tools at it),
> `AGENT_HANDOFF.md` (the living state journal — preamble §6 gains close-item 9 for it),
> `docs/agent_prompts/AGENT_KICKOFF.md` + `newAgentKickoffPrompt.txt` (the session-start reading protocol
> with clean-room reading boundaries). Session-start order is now: kickoff prompt → CLAUDE.md → preamble →
> handoff → ticket → plan.
>
> **v1.6 (2026-07-07): MIGRATED to the standalone `antevorta-capstone` repository** (stakeholder-created;
> private until publication — this rules the O1 repo-identity question by fact; the PACKAGE is still
> `wocbots`). The spec now lives at `docs/`, tickets at `tickets/`; internal paths updated. The stakeholder
> pre-laid the bare directory skeleton, a seed `.gitignore`, the README, and `data/README.md` — W0-01 is
> AMENDED accordingly (its remaining scope: packaging, tooling, check-suite ratification, CODEOWNERS, PR
> template, branch protection, CI). Stakeholder rulings folded same day: different-AI-system review
> independence ✅; pure AI→AI review path ✅; repo private until publication ✅. The W0-01 dedicated plan
> remains **DRAFT — pending stakeholder approval**. Project control documents (adapted from the
> stakeholder's templates) will land under `docs/` in a follow-up.
>
> **v1.5 (2026-07-07):** three governance additions. (1) **INDEPENDENT REVIEW is now part of ✅** (preamble
> §8): no ticket closes until reviewed by someone/something that did NOT implement it — a different student,
> the stakeholder, or a DIFFERENT AI system than the one that implemented (a fresh session of the same system
> is not independent); sign-off recorded in the status flip. (2) The **standard invocations** are codified in
> preamble §9 (ticket → plan) and §10 (plan → implementation) — verbatim, with the project-term translation
> (uflogs → manifests/encounter logs/swarm traces; continuous/probabilistic → the §2/§7/§8.2 graded-quantity
> machinery). (3) **W0-01 now has its own dedicated plan** (`W0-01_repo-scaffold-ci_PLAN.md`, DRAFT — pending
> stakeholder approval), produced under the §9 invocation as the per-ticket exemplar; the original wave plan
> is rescoped to W0-02..04.
>
> **v1.4 (2026-07-07):** **THE SET IS RE-CUT SMALLER** (stakeholder ruling: more-and-smaller beats
> fewer-and-big — smaller diffs review better and bad decisions cascade less, especially for a team new to
> AI-assisted development). 21 tickets → **42 tickets, same 9 waves**, same dependency structure, applying one
> pattern throughout: **mechanism and experiment never share a ticket**, and infrastructure splits at its
> natural seams. Renumbering map: W0-01→W0-01..04 · old W1-01/02/03→W1-01..06 · old W2-01/02→W2-01..04 ·
> old W3-01/02→W3-01..04 · old W4-01/02→W4-01..04 · old W5-02→W5-02..05 · old W6-02→W6-02/03 ·
> old W7-01/02/03→W7-01..06 · old W8-01/02/03/04→W8-01..06. W5-01 and W6-01 carried over unchanged.
> The W0 formal plan now covers the whole W0 wave (mapping note in its header).
>
> **v1.3 (2026-07-07):** STREAMS section added for the five-student team — waves = WHEN (dependency law);
> streams = WHO (ownership lanes): CORE / DATA / AGENTS / ARENA / EVAL, one-writer-per-directory,
> consumer-reviews-producer. W1 acquisition unblocked from W0 (now structural: W1-01 has no blockers).
>
> **v1.2 (2026-07-06):** W0's six STEP-0 rulings (O1–O6) DELEGATED TO THE TEAM — named-and-dated in the
> plan's RESULT block; overruled defaults need recorded rationale. Per-section delegation only: W1-04's label
> gate and any MUST dispute still escalate to the stakeholder.
>
> **v1.1 (2026-07-06):** the W0 formal plan created — the format exemplar. Tickets and plans COEXIST;
> precedence: spec > plan > ticket.
>
> *v1.0 (2026-07-06):* initial 21-ticket decomposition.

**Source of truth:** `docs/WoC-Bots_Implementation_Spec.md` (v1.2 — "the spec"). Every ticket binds
to named spec sections. Where a ticket and the spec disagree, **the spec wins** and the discrepancy is a bug
in the ticket — report it, do not improvise.

**Before touching ANY ticket:** read `01_MANDATORY_PREAMBLE.md`, in full. Every ticket starts with a written
mini-plan presented for review — no exceptions.

**Clean-room boundary:** the team works from the spec, the publications/dissertation, and `antevorta-db`
ONLY. No other prior code exists as far as this project is concerned.

**Status legend:** ☐ not started · ◐ in progress · ✅ landed — which requires ALL of: check suite green +
results manifest committed + **independent review signed off (preamble §8: reviewed by someone or something
that did not implement it)** + status flipped here as `✅ (reviewed: <who/what>, <date>)`.

**Quarter mapping:** Q1 = W0–W5 (exit = W5-05). Q2 = W6–W7. Q3+ = W8.

## Wave W0 — Scaffold (blocks everything)

**Two plans govern this wave.** `W0-01_repo-scaffold-ci_PLAN.md` (✅ APPROVED — stakeholder, 2026-07-07) is
the dedicated, per-ticket plan for W0-01 and the exemplar of the preamble §9 invocation at full depth.
`W0-01_scaffold-experiment-harness_PLAN.md` remains the execution document for W0-02..04 and holds the
wave-shared §3 rulings (O1–O6) and STEP-0 RESULT block, which must be filled before any W0 code. Read a
ticket first (the what), then its plan (the how).

| ID | File | Title | Blocked by |
|---|---|---|---|
| W0-01 | `W0-01_repo-scaffold-ci.md` | Repo, packaging, check-suite ratification, CI | — |
| W0-02 | `W0-02_types-policy-seams.md` | Shared types + the five policy seams + stubs | W0-01 |
| W0-03 | `W0-03_config-manifest-models.md` | Experiment config, registry, manifest models | W0-01 |
| W0-04 | `W0-04_harness-runner-rng-guard.md` | Harness runner, seed discipline, RNG guard | W0-03 |

## Wave W1 — Hollywood data (DATA stream's Q1 runway)

| ID | File | Title | Blocked by |
|---|---|---|---|
| W1-01 | `W1-01_raw-data-acquisition.md` | Raw data acquisition + provenance | — (day 1) |
| W1-02 | `W1-02_ground-truth-build-extract.md` | antevorta-db ground-truth build + reference extraction | W1-01 |
| W1-03 | `W1-03_hollywood-etl-transforms.md` | ETL: join, clean, transforms (labels excluded) | W1-01 |
| W1-04 | `W1-04_labels-validation-gate.md` | Labels + validation + the reconciliation GATE (escalates) | W1-02, W1-03 |
| W1-05 | `W1-05_splits-normalization.md` | Splits + normalization + leakage guards | W1-04 |
| W1-06 | `W1-06_anchor-analysis.md` | Anchor analysis (RESULT block) | W1-05 |

## Wave W2 — Agent layer

| ID | File | Title | Blocked by |
|---|---|---|---|
| W2-01 | `W2-01_agent-state-profile.md` | Agent state (§2 table) + public profile | W0-02 |
| W2-02 | `W2-02_classifier-train-eval-prune.md` | Classifiers, train/eval/prune, sanity agent | W2-01, W0-04 (real ACs: W1-05) |
| W2-03 | `W2-03_feature-assignment-crowd.md` | Feature assignment + crowd builder | W2-02, W1-06 |
| W2-04 | `W2-04_agent-table-reproduction.md` | §9.2 agent-table reproduction (experiment) | W2-03 |

## Wave W3 — Interaction arena (pure logic — parallel with W1/W2)

| ID | File | Title | Blocked by |
|---|---|---|---|
| W3-01 | `W3-01_grid-geometry-init.md` | Grid geometry + random init | W0-02 |
| W3-02 | `W3-02_movement-rounds.md` | Movement, anti-clique, lockstep rounds | W3-01 |
| W3-03 | `W3-03_certainty-update-flip.md` | The interaction kernel (certainty/flip) | W2-01, W3-02 |
| W3-04 | `W3-04_history-trust.md` | History store + trust updates | W3-03 |

## Wave W4 — Lifecycle + voting aggregation

| ID | File | Title | Blocked by |
|---|---|---|---|
| W4-01 | `W4-01_participant-selection-loop.md` | Participant selection, per-sample loop, resets, synthetic anchor | W2-02, W3-02, W3-04 |
| W4-02 | `W4-02_ground-truth-feedback.md` | Ground-truth feedback, priorPerf, degenerate rule | W4-01 |
| W4-03 | `W4-03_voting-aggregators.md` | UWM, WVM, trust-weighted (mechanism) | W4-01 |
| W4-04 | `W4-04_tiers-mechanism-comparison.md` | Tiers + the 3>2>1 comparison (experiment) | W4-02, W4-03 |

## Wave W5 — Baseline + Q1 reproduction (Q1 exit)

| ID | File | Title | Blocked by |
|---|---|---|---|
| W5-01 | `W5-01_baseline-mlp.md` | The monolithic MLP baseline | W1-05 |
| W5-02 | `W5-02_matched-comparison.md` | Matched head-to-head + epoch sweep (experiment) | W2-03, W4-04, W5-01 |
| W5-03 | `W5-03_robustness-contrasts.md` | Feature-removal contrasts (experiment) | W5-02 |
| W5-04 | `W5-04_crowd-scaling.md` | 26-agent scaling run (experiment) | W5-02 |
| W5-05 | `W5-05_q1-report-exit.md` | Q1 report + exit audit — **Q1 EXIT** | W2-04, W5-02, W5-03, W5-04 |

## Wave W6 — Honeybee swarm aggregation

| ID | File | Title | Blocked by |
|---|---|---|---|
| W6-01 | `W6-01_swarm-round-primitive.md` | Swarm round: presenters, fitness wheel, reassignment | W4-01 |
| W6-02 | `W6-02_confidence-ladder.md` | The confidence ladder + group interactions (mechanism) | W6-01, W3-03 |
| W6-03 | `W6-03_swarm-variance-study.md` | Variance vs WVM + band calibration (experiment) | W6-02 |

## Wave W7 — Second dataset + comparative evaluation

| ID | File | Title | Blocked by |
|---|---|---|---|
| W7-01 | `W7-01_airline-etl.md` | Airline ETL, label rule, structured missingness | W1-05, W4-01 |
| W7-02 | `W7-02_airline-anchors-scale.md` | Airline anchors, crowd configs, scale posture | W7-01 |
| W7-03 | `W7-03_baseline-models.md` | XGBoost / RF / logreg wrappers | W5-01 |
| W7-04 | `W7-04_comparison-grid.md` | The full comparison grid (experiment) | W6-03, W7-02, W7-03 |
| W7-05 | `W7-05_deletion-protocol.md` | Missing-data deletion masks (infrastructure) | W7-01 |
| W7-06 | `W7-06_missing-data-study.md` | Missing-data tolerance curves (experiment) | W7-04, W7-05 |

## Wave W8 — Distinctive capabilities (the publication)

| ID | File | Title | Blocked by |
|---|---|---|---|
| W8-01 | `W8-01_injection-api.md` | Incremental-feature injection API (mechanism) | W5-05 |
| W8-02 | `W8-02_incremental-holdback-study.md` | Holdback lift/cost study (experiment) | W8-01 |
| W8-03 | `W8-03_external-agent-audit.md` | External-prediction agent + privacy audit (mechanism) | W6-03 |
| W8-04 | `W8-04_federated-experiment.md` | Federated meta-swarm study (experiment) | W7-03, W8-03 |
| W8-05 | `W8-05_auto-tuned-thresholds.md` | Auto-tuned confidence thresholds (research) | W6-03 |
| W8-06 | `W8-06_report-assembly.md` | Report / paper foundation (accretes from W5-05) | W5-05 |

## Streams (team of 5) — who works on what, in parallel

**Waves answer WHEN (dependency order); streams answer WHO (ownership lanes).** A stream is one student
owning a subsystem across many waves; a wave contains tickets from several streams running concurrently.
Blocked-by edges are the only ordering law — everything else is parallel.

| Stream | Owns (one-writer rule) | Q1 | Q2 | Q3+ |
|---|---|---|---|---|
| **CORE** | `experiments/`, `aggregation/`, `protocols.py` | W0-01→02→03→04 (EVAL pairs) → W4-01→02→03→04 | integration; W6-02 (pair) | W8-03 → W8-04 |
| **DATA** | `data/` | W1-01→02→03→04→05→06 | W7-01 → W7-02; W7-05 | student-supplied datasets |
| **AGENTS** | `agents/` | W2-01→02→03→04 | W6-01 (pair w/ ARENA) | W8-01 → W8-02 |
| **ARENA** | `arena/`, `interaction/` | W3-01→02→03→04 | W6-01→02 (swarm lead) → W6-03 | W8-05 |
| **EVAL** | `evaluation/`, baselines, the report | W0 pair; W5-01→02→03→04; W5-05 (pair w/ CORE) | W7-03 → W7-04 → W7-06 | W8-06 |

**Ownership rules:**
- **One writer per directory:** a stream's directories are edited by that stream; cross-stream changes land
  via PR reviewed by the owning stream.
- **Consumer reviews producer:** DATA reviewed by AGENTS; AGENTS and ARENA by CORE; CORE by EVAL; EVAL by
  DATA. Every PR gets a reviewer who depends on it being right.
- Streams are defaults, not cages — pairing on convergence tickets is expected; Q2/Q3 cells re-dealt when the
  team gets there.

**Week 1:** all five run the W0 STEP-0 ruling meeting together; CORE + EVAL start W0-01; DATA starts W1-01
(no blockers); AGENTS and ARENA read their spec sections and draft their W2-01/W3-01 mini-plans.

**Convergence points (the schedule risks):** W4-01 (CORE consumes AGENTS' W2-02 and ARENA's W3-02/04 — first
hard cross-stream integration) and W5-05 (everything converges for the Q1 exit). The Q1 critical path is
W0 → W1-01..05 → W2-02..03 / W4-01..04 → W5-02 → W5-05.

## Cross-cutting rules (duplicated in the preamble; here for visibility)

- A ticket starts only when its Blocked-by column is ✅.
- Every reported number is a mean over 10 seeded runs with std (spec §9.1). Single runs are not results.
- Every experiment = config + seed + git SHA in a results manifest. A number that can't be regenerated from
  its manifest does not exist.
- Tests land WITH the feature, in the same ticket.
- No ticket is ✅ without an implementer-independent review sign-off (preamble §8).
- Plans are produced under the preamble §9 invocation; implementations under §10. Both end at the ruling
  authority, never at improvisation.
- The sanity-check agent (budget+revenue) appears in pipeline-validation tests ONLY (spec §10.9).
- No dataset-specific vocabulary in the toolkit core (spec §11, preamble §7).
