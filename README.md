# WoC-Bots Reimagined

A clean-room Python reimplementation of **WoC-Bots** — a wisdom-of-crowds, swarm-based binary classifier in
which many small, feature-diverse agents train independently, exchange opinions through local interactions in
a simulated arena, and aggregate a collective prediction with an earned confidence label. The method is fully
specified in peer-reviewed publications and a dissertation; this project rebuilds it as an open, modular,
reproducible toolkit — and then runs the experiments the original never could.

**Stakeholder:** Dr. Sean Grimes. **Team:** five students, five streams (see the ticket index).

## Read these, in this order

| # | Document | What it is |
|---|---|---|
| 1 | `docs/WoC-Bots_Implementation_Spec.md` (+ PDF) | **The spec** — the source of truth. Every design question ends here. |
| 2 | `tickets/01_MANDATORY_PREAMBLE.md` | The binding rules for ALL work: session protocol, forbidden shortcuts, test discipline, independent review, the standard invocations. |
| 3 | `tickets/00_INDEX.md` | The 42-ticket map: waves (WHEN), streams (WHO), status, changelog. |
| 4 | Your ticket, then its plan if one exists | The what, then the how. W0-01 has the exemplar plan. |

Working with an AI session? It starts from `docs/agent_prompts/newAgentKickoffPrompt.txt` (paste it, fill in
ticket + mode), which routes through `AGENT_KICKOFF.md` → `CLAUDE.md` (binding AI instructions; `AGENTS.md`
points non-Claude tools there) → the preamble → `AGENT_HANDOFF.md` (the live state journal — read it, and
update it when you finish).

Precedence when documents disagree: **spec > plan > ticket** — and a disagreement is a bug to report, never
something to reconcile silently.

## How we work (the one-paragraph version)

Work is decomposed into small tickets in dependency-ordered waves; each student owns a stream (subsystem)
across all waves. A ticket starts with a written mini-plan, reviewed before code. Big tickets get formal
plans first (preamble §9 invocation); implementation follows the plan (§10 invocation). Tests land WITH the
feature; every numeric mechanism gets exact pins. Every experiment is a config + seed + git SHA producing a
committed results manifest — **a number that can't be regenerated from its manifest does not exist**. No
ticket closes until someone (or some AI) that didn't implement it reviews the diff and signs off (preamble
§8). Humans commit via PRs; nothing lands on `main` unreviewed.

## The clean-room rule

This project is built from the spec, the publications/dissertation, and the `antevorta-db` data module
**only**. No other pre-existing implementation exists as far as this repo is concerned. If you want to know
"how the original did it" beyond what the spec says, ask the stakeholder — do not go looking.

## Repository layout

```
docs/               the spec (source of truth) + project control documents
tickets/            the ticket set: index, preamble, tickets, plans
src/wocbots/        the toolkit (agents/ arena/ interaction/ aggregation/ data/ evaluation/ experiments/)
tests/              unit/ (fast, per-commit) and integration/ (slow-marked)
configs/            experiment configs — every experiment is a config file
results/manifests/  committed results manifests — the provenance chain
data/               local raw data (never committed; see data/README.md)
```

## Status & week 1

The repo is pre-W0-01: packaging, tooling, and CI arrive with ticket **W0-01** (its plan is written and
approved-pending — read it before touching anything). Week 1: all five run the W0 STEP-0 ruling meeting;
CORE + EVAL implement W0-01; DATA starts W1-01; AGENTS and ARENA draft their W2-01/W3-01 mini-plans. The
Q1 exit is W5-05: the published results, reproduced from configs.
