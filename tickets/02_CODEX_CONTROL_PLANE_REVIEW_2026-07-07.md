# Review Findings — 2026-07-07

Mode: REVIEW. Scope: repository control plane, full ticket set, both W0 plans, spec v1.1, current tree state,
and available observability artifacts.

Code execution-path note: there are no source implementation files yet under `src/wocbots/`; only `.gitkeep`
placeholders exist. There were therefore no functions to inspect beyond the documented execution paths in the
spec and plans. Uflog cross-check: `results/manifests/` contains only `.gitkeep`; no encounter logs or swarm
traces exist; `logs/` is absent. The only live evidence available was the git tree/history and control docs.

## Findings

[High] `AGENT_HANDOFF.md` is stale, and the file itself says stale handoff must be fixed first. The header
claims the repo is at the initial commit (`AGENT_HANDOFF.md:3`), and the five-minute test expects exactly the
initial commit (`AGENT_HANDOFF.md:40`-`AGENT_HANDOFF.md:42`). Live history has two commits:
`bfd18f3 Public-repo re-ruling, MIT license, re-cut reference fixes` and `c25f470 Initial commit...`.
Because every session is required to read this current state before work, this can send implementers into an
already-known-bad startup path. Clarification: should this review-only session leave it stale, or should the
next authorized HANDOFF session update it before any implementation starts?

[High] W0-01's ticket points implementers at the superseded W0 wave plan instead of the dedicated W0-01 plan.
The index states that `W0-01_repo-scaffold-ci_PLAN.md` is the approved per-ticket plan for W0-01 and that
`W0-01_scaffold-experiment-harness_PLAN.md` is for W0-02..04 (`tickets/00_INDEX.md:86`-`tickets/00_INDEX.md:90`).
The W0-01 ticket, however, names `W0-01_scaffold-experiment-harness_PLAN.md` as its formal plan
(`tickets/W0-01_repo-scaffold-ci.md:10`-`tickets/W0-01_repo-scaffold-ci.md:12`) and its grounding points to
that plan (`tickets/W0-01_repo-scaffold-ci.md:20`-`tickets/W0-01_repo-scaffold-ci.md:23`). That is a high-risk
routing bug: following the ticket literally pulls W0-02/W0-03/W0-04 scope into W0-01, including types,
protocols, manifest models, and the harness. Clarification: should W0-01's ticket be corrected to name only
`W0-01_repo-scaffold-ci_PLAN.md`, with the wave plan cited only for shared O1-O6 rulings?

[High] The W0-01 dedicated plan has a pre-code gate that appears self-dependent. It requires branch protection
and an empty-commit PR to traverse CI + review + auto-merge before coding (`tickets/W0-01_repo-scaffold-ci_PLAN.md:127`-`tickets/W0-01_repo-scaffold-ci_PLAN.md:135`,
`tickets/W0-01_repo-scaffold-ci_PLAN.md:289`-`tickets/W0-01_repo-scaffold-ci_PLAN.md:292`). But the same ticket
is supposed to create the CI workflows and PR template (`tickets/W0-01_repo-scaffold-ci_PLAN.md:239`-`tickets/W0-01_repo-scaffold-ci_PLAN.md:261`).
In the current tree, `.github/` does not exist. This can block W0-01 before the files needed to satisfy the
gate exist. Clarification: is the intended sequence “rule O7-O9 first, implement CI/PR template, then prove a
traversal before close,” rather than requiring traversal before coding?

[Medium] The ruling status for W0 O2-O5 is inconsistent across documents. The index says O1 and O6 are ruled,
and the team's STEP-0 scope is O2-O5 plus O7-O9 (`tickets/00_INDEX.md:3`-`tickets/00_INDEX.md:5`). The
dedicated W0-01 plan says O2-O5 are “Inherited and NOT re-opened” (`tickets/W0-01_repo-scaffold-ci_PLAN.md:51`-`tickets/W0-01_repo-scaffold-ci_PLAN.md:59`),
while also saying the wave STEP-0 must be filled first (`tickets/W0-01_repo-scaffold-ci_PLAN.md:127`-`tickets/W0-01_repo-scaffold-ci_PLAN.md:130`).
The wave plan still has blank O1-O6 result lines (`tickets/W0-01_scaffold-experiment-harness_PLAN.md:447`-`tickets/W0-01_scaffold-experiment-harness_PLAN.md:455`).
Clarification: are O2-O5 already stakeholder/team-ratified, or are they still recommendations awaiting the
team meeting?

[High] The W3-03 required numeric pin does not match exact arithmetic from the spec formula. The spec formula
is `0.71 * (1 - 0.62) * (0.78 * 0.80) * 1.1` (`docs/WoC-Bots_Implementation_Spec.md:372`-`docs/WoC-Bots_Implementation_Spec.md:383`,
example at `docs/WoC-Bots_Implementation_Spec.md:389`-`docs/WoC-Bots_Implementation_Spec.md:393`). Exact
arithmetic gives corrected influence `0.18519072`, post-update certainty `0.43480928`, and reflected
certainty `0.56519072`. The ticket pins `corrected = -0.18480 (1e-5)` and final certainty `0.565 (1e-9)`
(`tickets/W3-03_certainty-update-flip.md:34`-`tickets/W3-03_certainty-update-flip.md:38`). That pin appears to
round the intermediate influence to `0.168` before multiplying, which would bake a brittle rounding shortcut
into the interaction kernel. Clarification: should W3-03 pin exact unrounded arithmetic, or is intermediate
rounding intended as a method ruling?

[High] Arena capacity is ambiguous: “2 x N cells” conflicts with the pinned square grid dimensions. The spec
says number of cells equals `2 * N` and also says `side = ceil(sqrt(2N))` for a square arena
(`docs/WoC-Bots_Implementation_Spec.md:314`-`docs/WoC-Bots_Implementation_Spec.md:321`). The W3-01 ticket
repeats “2 x N cells” (`tickets/W3-01_grid-geometry-init.md:17`-`tickets/W3-01_grid-geometry-init.md:21`) but
pins N=5/10/26 to 4x4/5x5/8x8 grids (`tickets/W3-01_grid-geometry-init.md:29`-`tickets/W3-01_grid-geometry-init.md:32`),
which are 16/25/64 cells, not 10/20/52. This changes density and encounter rates. Clarification: should the
implementation use `side^2` active cells with density approximately N/side^2, or exactly `2N` active cells
inside a larger square coordinate system?

[High] `prior_accuracy` lifecycle and WVM no-history behavior are underspecified and internally inconsistent.
The spec initializes `prior_accuracy` to `eval_accuracy` (`docs/WoC-Bots_Implementation_Spec.md:84`-`docs/WoC-Bots_Implementation_Spec.md:92`),
and W2-01 pins that behavior (`tickets/W2-01_agent-state-profile.md:20`-`tickets/W2-01_agent-state-profile.md:24`,
`tickets/W2-01_agent-state-profile.md:34`-`tickets/W2-01_agent-state-profile.md:38`). But W4-03 also says WVM
uses 50 votes before any track record and explicitly pins “no-history agent -> WVM 50”
(`tickets/W4-03_voting-aggregators.md:18`-`tickets/W4-03_voting-aggregators.md:21`,
`tickets/W4-03_voting-aggregators.md:32`-`tickets/W4-03_voting-aggregators.md:35`). Separately, feedback says
`prior_accuracy` becomes a running fraction over inference predictions (`docs/WoC-Bots_Implementation_Spec.md:425`-`docs/WoC-Bots_Implementation_Spec.md:430`,
`tickets/W4-02_ground-truth-feedback.md:17`-`tickets/W4-02_ground-truth-feedback.md:22`). Clarification:
before the first labeled inference sample, should votes use eval-seeded `prior_accuracy`, neutral 0.50, or a
separate “has inference track record” flag? After feedback starts, should inference accuracy replace the
eval seed or be blended with it?

[Medium] The history-store cardinality is ambiguous for directed trust updates. The spec requires history
per `(agent, partner, sample)` and says each receiving side consults its own history with the partner
(`docs/WoC-Bots_Implementation_Spec.md:396`-`docs/WoC-Bots_Implementation_Spec.md:411`). W3-04 repeats a
directed tuple shape (`tickets/W3-04_history-trust.md:17`-`tickets/W3-04_history-trust.md:24`), but its test
requirement says “every encounter recorded exactly once” (`tickets/W3-04_history-trust.md:31`-`tickets/W3-04_history-trust.md:37`).
For a two-agent encounter, trust math needs two directed advice records, while the arena encounter log likely
has one undirected pair record. Clarification: should W3-04 assert exactly one encounter-log row plus exactly
two directed history rows per interaction?

[Medium] The N<10 swarm fallback needs a precise mechanism ruling. The spec says N<10 swarm results should be
treated as “voting fallback” territory and documented (`docs/WoC-Bots_Implementation_Spec.md:632`-`docs/WoC-Bots_Implementation_Spec.md:637`).
W6-02 says N<10 routes to the “W4-02 degenerate/voting posture” (`tickets/W6-02_confidence-ladder.md:20`-`tickets/W6-02_confidence-ladder.md:25`),
but W4-02's degenerate rule is only for fewer than 3 participants and uses certainty-weighted Low-confidence
voting (`tickets/W4-02_ground-truth-feedback.md:23`-`tickets/W4-02_ground-truth-feedback.md:25`). Clarification:
for 3-9 participants under a configured swarm aggregator, should fallback be certainty-weighted Low, a chosen
W4-03 voting aggregator, or another explicitly configured voting policy?

[Low] README status is stale relative to the index and current plan state. It says the W0-01 plan is
“approved-pending” (`README.md:56`-`README.md:60`), while the index says the dedicated W0-01 plan is approved
(`tickets/00_INDEX.md:14`-`tickets/00_INDEX.md:16`, `tickets/00_INDEX.md:86`-`tickets/00_INDEX.md:90`). This is
lower severity than the handoff because the binding startup protocol routes through `CLAUDE.md` and the
handoff, but it will mislead humans using the README as their entry point.

## Current Tree Evidence

- `git status --short`: clean.
- Branch: `main`.
- Git history: `bfd18f3` then `c25f470`.
- Source/test/config tree: placeholder directories only; no `pyproject.toml`, no `uv.lock`, no `.github/`,
  no package `__init__.py`, no tests, no implementation modules.
- Observability artifacts: no manifests except `results/manifests/.gitkeep`; no logs directory.

## Clarification Questions

1. Should a HANDOFF-mode session update `AGENT_HANDOFF.md` before W0-01 implementation starts?
2. Should W0-01's ticket be corrected to point at `W0-01_repo-scaffold-ci_PLAN.md` as its formal plan?
3. Should W0-01's PR/branch-protection traversal proof move from pre-code STEP 0 to close-out after CI exists?
4. Are W0 O2-O5 already ratified, or still awaiting the team STEP-0 meeting?
5. Should W3-03 use exact unrounded arithmetic for the worked-example test pin?
6. Should arena active capacity be exactly `2N` cells or `ceil(sqrt(2N))^2` cells?
7. What is the intended `prior_accuracy`/WVM behavior before and after inference feedback begins?
8. Should interaction history store two directed rows per encounter, plus one arena encounter-log row?
9. What exact fallback should `HoneybeeSwarm` use for participant counts 3 through 9?

---

## DISPOSITION (Claude + stakeholder adjudication, 2026-07-07) — ALL TEN FINDINGS ACCEPTED

Recorded per preamble §8 (findings adjudicated before close). Method rulings are folded into spec v1.2;
process fixes are folded into the named documents. This file moved to the `02_` review slot on acceptance.

1. **[High] Stale handoff → FIXED.** Header + five-minute test rewritten (and made less brittle: the test
   now keys on the index changelog head, not an exact commit count).
2. **[High] W0-01 plan mis-pointer → FIXED.** The ticket's Formal-plan line and Grounding section now name
   the dedicated plan; the wave plan is cited only for shared O-rulings.
3. **[High] Self-dependent STEP-0 gate → FIXED (sequencing ruling).** STEP-0 confirms repo access + Actions
   enabled only; O8 branch protection applies at §9.5 (after `ci.yml` exists); the traversal PR is the
   §10.6 close-out proof. Codex's proposed sequence adopted verbatim.
4. **[Medium] O2–O5 status ambiguity → CLARIFIED.** "Inherited and NOT re-opened" ≠ ratified: O1/O6 are
   ruled by fact; O2–O5 + O7–O9 await the team's wave STEP-0. Stated in the dedicated plan §3.
5. **[High] W3-03 rounded pin → FIXED (spec v1.2 + ticket).** Exact arithmetic is now normative: corrected
   = −0.18519072, post-flip certainty = 0.56519072, mirror = 0.80519072 (1e-9). The spec's worked example
   shows exact values with an explicit never-pin-rounded-values rule. The pre-v1.2 pin (−0.18480/0.565)
   baked a rounded intermediate — a genuine caught bug.
6. **[High] Arena capacity contradiction → RULED (spec §6.1 v1.2).** Near-square rectangle: rows =
   floor(sqrt(2N)), cols = ceil(2N/rows); capacity ∈ [2N, 2N+rows). Preserves the published ~0.5 agents/cell
   density (load-bearing for encounter rates); the ceil-square reading was rejected (dilutes to ~0.31 at
   small N). W3-01 pins updated: N = 5/10/26 → 3×4/4×5/7×8.
7. **[High] prior_accuracy / WVM totality → RULED (spec §2/§6.7/§7 v1.2).** One total variable: eval-seeded,
   REPLACED (not blended) by running inference accuracy at ≥ 5 scored predictions (shared cold-start with
   prior_performance). The published 50-vote clause survives only as the no-information default
   (prior_accuracy = 0.5 when no eval metrics exist — external agents lacking a validation statement).
   W4-02/W4-03 updated with boundary pins.
8. **[Medium] History cardinality → RULED (W3-04).** One undirected encounter-log row (W3-02) + exactly two
   directed history rows (one per receiving side) per encounter; test updated to assert both counts.
9. **[Medium] Small-N swarm fallback → RULED (spec §10.8 v1.2 + W6-02).** 3 ≤ N ≤ 9: HoneybeeSwarm delegates
   to trust-weighted voting (§7 mechanism 3), labels Low, counts the occurrence; N < 3: the W4-02 degenerate
   rule. Boundary pins added (N = 2/6/10).
10. **[Low] Stale README → FIXED** ("approved-pending" → APPROVED).

**Meta-finding accepted implicitly:** the reviewer's note that no uflogs/manifests exist yet is expected
pre-implementation state (the first artifact arrives with W0-04); no action.
