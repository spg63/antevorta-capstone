# MANDATORY PREAMBLE — binding on every ticket in this directory

You are implementing one ticket from the WoC-Bots Reimagined set. This file is part of every ticket's text. If
you have not read it in your current session (or, for a human team, recently enough to state its rules from
memory), read it now, in full.

## 0. The non-negotiable session protocol

1. **Plan first.** Before writing ANY code:
   a. Read this preamble, the ticket file in full, and every spec section the ticket names as binding
      (`docs/WoC-Bots_Implementation_Spec.md` — "the spec").
   b. Read whatever the ticket's "Grounding" section lists — spec sections, antevorta-db files, published
      figures/tables. For antevorta-db cites, read the actual code, not just this ticket's summary of it.
   c. Produce a written mini-plan: sequenced steps, files to touch, interfaces/signatures, the test list with
      what each test asserts, and open questions. Present it for review before implementing (for agent
      sessions: for approval; for the student team: to another team member or the stakeholder).
2. **Where the ticket and the spec disagree, STOP and report** — the spec wins; the discrepancy is a ticket
   bug. Do not reconcile silently. Where the spec leaves a genuine choice (it marks these MAY), choose,
   document the choice in the results manifest, and move on. Where a MUST seems wrong, escalate to the
   stakeholder — never silently deviate from a MUST.
3. **Verify cheap before expensive.** Before a 10-run experiment sweep, run the single-seed smoke version.
   Before training 26 agents, train one.

## 1. Binding documents, in precedence order

1. The spec (`docs/WoC-Bots_Implementation_Spec.md`, v1.2) — the ticket's named sections. Its
   MUST/SHOULD/MAY vocabulary (spec §0) is the normative language of every ticket here.
2. The dissertation and publications — for published reference numbers and method rationale. Where spec and
   publication disagree, the spec's ruling stands (it says so where it happens); flag anything material.
3. `antevorta-db` — ground truth for Hollywood data preparation (spec §4.2). The ONLY prior code in scope.
4. The ticket file itself.

**The clean-room boundary is absolute:** no other pre-existing implementation is consulted, referenced, or
ported from. If you find yourself wanting to know "how the original did it" beyond what the spec says — that
question goes to the stakeholder, not to a codebase.

## 2. Hard implementation rules (from the spec; restated because each one is the cheap path to violate)

- **One RNG.** A single seeded `numpy.random.Generator` threads from the experiment config into everything
  stochastic (splits, init, movement, presenter selection, sklearn seeds). No module-level `np.random.*`, no
  unseeded `random`, no wall-clock anywhere in behavior-affecting code.
- **Every experiment = config + seed + git SHA**, written to a results manifest by the W0-01 harness. Reported
  numbers are 10-run means ± std (spec §9.1).
- **Per-sample everything.** Participant set, arena size (2×N), interaction iterations (max(10, round(0.1×N))),
  presenter count — all derived from THIS sample's participants (spec §10.7). Nothing crowd-sized is a constant.
- **The two performance scales stay separate** (spec §2): `prior_performance` is a multiplier in [0.7, 1.3];
  `prior_accuracy` is a rate in [0, 1]. Influence math uses the former; vote allocation uses the latter.
- **Certainty is clamped** to [0.01, 0.99] at every update (spec §6.5) and **reset per sample** to its
  training-time value (spec §6.6). Trust, prior_performance, prior_accuracy, and interaction history persist.
- **Missing features = sit out** (spec §3). The method never imputes. (Imputation appears only inside W7-03's
  comparison baselines, clearly labeled as the thing being compared against.)
- **Policies are seams** (spec §11): init, movement, interaction, scoring, aggregation live behind small
  interfaces. Reference implementations are configs, not hard-coding.
- **Eval data is training-side data.** Agent eval metrics (which seed certainty/trust/confidence and drive
  pruning) come from a held-out slice of the TRAINING split — never the test split (spec §10.5).

## 3. The forbidden-shortcut register

Each of these is the locally-cheapest path. Each is banned by name. If your mini-plan contains one, it will be
rejected; the landing tests are designed to fail on it.

1. Test-set leakage into agent eval metrics or normalization statistics (spec §4.3.9, §10.5).
2. Skipping the per-sample certainty reset — looks fine for 50 samples, then the crowd ossifies (spec §10.6).
3. Unclamped certainty, or acceptance pinned to exactly 0 (spec §10.1).
4. Fixed agent iteration order in arena rounds — shuffle per round (spec §10.3).
5. Hard-coded crowd/arena/presenter sizes anywhere (spec §10.7, §10.8).
6. The budget+revenue sanity agent participating in a reported run (spec §10.9).
7. Chasing exact published decimals or reporting single-run numbers (spec §9.2, §10.10).
8. Imputing missing features inside the method instead of sitting agents out.
9. "Interact once, classify everything" — the arena runs per test sample (spec §3).
10. Porting or consulting any pre-existing implementation other than antevorta-db (the clean-room rule).
11. Conflating `prior_performance` with `prior_accuracy` (spec §10.2).
12. Silently deviating from a spec MUST, or silently "fixing" a spec ruling you disagree with — escalate.

## 4. Test discipline

- Tests land WITH the feature, in the same ticket. A ticket with owed tests is not closeable.
- Every numeric mechanism gets: (a) **exact-arithmetic pins** at the values the ticket specifies (the spec's
  §6.5 worked example is a mandatory pin for W3-03; formulas like the vote allocation and fitness wheel get
  hand-computed cases), to explicit tolerances; (b) **boundary tests on BOTH sides** of every threshold
  (certainty 0.5 flip, prune at 0.50, ladder thresholds 100/90/75, tier edges); (c) a degenerate-input test
  where applicable (empty participant set, crowd of one, all-agree round one).
- Deterministic by construction: seeded Generator everywhere; same config + same seed → byte-identical results
  manifest. A test that can flake is a defect.
- The end-to-end anchor: a synthetic linearly-separable dataset on which the full pipeline MUST reach ~100%
  accuracy (spec §11). It lands in W4-01 and every later wave keeps it green.
- Reference-number reproductions (the §9.2 bands) are integration tests marked slow — run on demand and in CI's
  scheduled job, not per-commit.

## 5. The check suite (all green before a ticket is closeable)

```bash
ruff check .
ruff format --check .
mypy src tests
pytest
```

(Exact invocations/paths are pinned by W0-01 and recorded here when ratified; mypy strictness level is a W0-01
decision — default: on, standard strictness. Until W0-01 lands, this block is the target, not the law.)

## 6. Ticket close checklist (state each item explicitly when closing)

1. ☐ Check suite green; no skipped tests without a named reason.
2. ☐ The ticket's tests all land in the same change set as the feature.
3. ☐ Results manifest committed for any experiment the ticket ran (config + seed + SHA + outputs).
4. ☐ Status flipped in `00_INDEX.md`; any spec discrepancy found → reported, not reconciled.
5. ☐ Any RESULT block in the ticket (W1-04's reconciliation gate, W1-06's and W7-02's anchor sets, the W0
   plan's STEP-0) is filled in the ticket file itself.
6. ☐ Touched paths listed project-root-relative in the closing report.
7. ☐ Commit discipline per team workflow: PRs reviewed by someone who didn't write them; nothing lands directly
   on main. (Agent sessions: no commits or pushes unless explicitly asked.)
8. ☐ **Independent review signed off (§8).** The ticket is not ✅ — regardless of green checks — until a
   reviewer independent of the implementation has reviewed the full diff and signed off, with reviewer
   identity and date recorded at the `00_INDEX.md` status flip.
9. ☐ `AGENT_HANDOFF.md` updated per its own HOW-THIS-FILE-WORKS box: old CURRENT demoted to PRIOR, fresh
   CURRENT STATE with all five parts (done / in-flight / owner-attention / next step / five-minute test),
   header line refreshed.

## 7. Vocabulary and generality rules

- Use the spec §2 state names (`certainty`, `trust_score`, `confidence`, `prior_performance`, `prior_accuracy`)
  EXACTLY — no synonyms, no local renames. Every equation in the spec §13 cross-reference must be findable in
  the code by these names.
- No dataset-specific vocabulary in the toolkit core (`wocbots.agents/arena/interaction/aggregation`). Movies,
  airlines, and (later) medicine live in `wocbots.data` and experiment configs. If a core name only makes sense
  for one dataset, it is wrong.
- New method vocabulary (a new policy kind, a new confidence tier scheme) must be flagged to the stakeholder
  before it becomes load-bearing — it is a spec change, and the spec is versioned.

## 8. Independent review — the second-set-of-eyes rule

*(Stakeholder-ratified 2026-07-07: different-AI-system independence required; the pure AI→AI review path is
acceptable with human adjudication of findings.)*

No ticket is fully green until its work has been reviewed **by someone or something that did not implement
it**, and the sign-off is recorded.

- **"Implementer" means:** whoever wrote the code — including whoever DROVE the AI session that wrote it. A
  student prompting an AI and then "reviewing" the same output they accepted during the session is not
  independent review; they are the implementer.
- **Acceptable reviewers:** a different team member (the consumer-reviews-producer pairing from the index is
  the default); the stakeholder; or a **different AI system** than the one that implemented (e.g., if Claude
  implemented, then Codex, a different vendor's model, or a human reviews — a fresh session of the SAME
  system is not independent; it shares the blind spots).
- **What review means:** the reviewer reads the full diff against the ticket/plan (not a summary of it),
  checks the forbidden-shortcut register (§3) against the actual code, verifies the test pins exist and
  assert what the ticket says they assert, and either signs off or files findings. Findings are addressed
  before ✅.
- **Recording:** the `00_INDEX.md` status flip carries `✅ (reviewed: <who/what>, <date>)`. An AI reviewer is
  named like a person (`reviewed: Codex, 2026-07-…`); its findings are adjudicated by a human before close.
- Review applies per TICKET CLOSE (on top of ordinary per-PR review). Small tickets exist precisely so this
  is cheap.

## 9. The standard invocation: turning a ticket into a plan

When a ticket is promoted to a formal `_PLAN.md`, the working session is opened with exactly this
instruction:

> "Create a detailed plan for an enterprise-grade solution with no shortcuts, lexical or otherwise, that is
> general, future-proof, and extensible. Deeply understand all related execution paths in the code; read all
> related function, not just their signatures, and cross check with the uflogs. Do not change anything until
> I approve the plan, and ask me for clarification for any questions or issues. Changes need to work with the
> continuous output / probabilistic system, no brittle fixes, no brittle fallbacks. Begin."

*Translation for this project:* "the uflogs" = this project's observability artifacts — results manifests,
encounter logs, swarm traces; cross-check claimed behavior against what those artifacts actually recorded.
"The continuous output / probabilistic system" = the WoC-Bots state and output machinery (continuous
certainty/trust/confidence in §2, vote margins in §7, agreement thresholds and bands in §8.2) — no boolean
gate may stand in for a graded quantity, and ties/uncertainty surface as such rather than being collapsed.
The produced plan follows the exemplar's section skeleton (`W0-WAVE_scaffold-experiment-harness_PLAN.md`'s
READ-ME-FIRST box lists it) and is approved by the ruling authority before any implementation.

## 10. The standard invocation: turning a plan into an implementation

When an approved plan is implemented, the working session is opened with exactly this instruction:

> "Implement an enterprise-grade solution with no shortcuts, lexical or otherwise, that is general,
> future-proof, and extensible. Deeply understand all related execution paths in the code; read all related
> function, not just their signatures, and cross check with the uflogs. Do not take any shortcuts or create
> any brittle fallbacks or fixes. All implementations should be consistent with continuous output /
> probabilistic system. If at any point there are questions that you cannot resolve, pause and bring them to
> my attention."

The same translation note as §9 applies. "Pause and bring them to my attention" routes to the ruling
authority for the decision in question (the stakeholder by default; the team where authority is delegated) —
pausing is the licensed behavior, improvising is the violation.
