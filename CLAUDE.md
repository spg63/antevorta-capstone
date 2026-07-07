# CLAUDE.md — WoC-Bots Reimagined project instructions

This file is read automatically by Claude at the start of every code session. Do not delete it. Do not move
it. (Other AI tools: `AGENTS.md` points here — these instructions bind every AI session in this repo,
regardless of vendor.)

## What this project is

A clean-room Python reimplementation of WoC-Bots: many small, feature-diverse classifier agents interact
socially in a simulated arena and aggregate a collective binary prediction with an earned confidence label.
The method is fully specified in `docs/WoC-Bots_Implementation_Spec.md` ("the spec") — the source of truth
for every design question. The team is five students, each owning a stream (see `tickets/00_INDEX.md`).

## Before you do anything else — in this order, no skipping

1. Read `tickets/01_MANDATORY_PREAMBLE.md` in full. Every rule in it applies to you.
2. Read `AGENT_HANDOFF.md` (header + CURRENT STATE). That is the live state of the repo.
3. Read the ticket you are working on, in full, plus its `_PLAN.md` if one exists.
4. Read the spec sections your ticket names as binding — those sections, in full, not skimmed.

If you were started with the kickoff prompt, `docs/agent_prompts/AGENT_KICKOFF.md` walks this exact protocol
with reading boundaries. Follow it.

## The clean-room rule (do not break this one)

This project is built from the spec, the publications, and the `antevorta-db` data module ONLY. Never go
looking for the original WoC-Bots implementation, other implementations, or code outside this repository.
If you want to know "how the original did it" beyond what the spec says — STOP and ask the stakeholder.

**This repository is PUBLIC**, so the boundary cuts both ways: nothing derived from the stakeholder's
private research code may ever appear here in ANY form — code, comments, commit messages, issues, or PR
text. Committed data excerpts must comply with their source datasets' licenses (see `data/README.md`).

## Hard rules (short form — the preamble is authoritative; restated here because each is the cheap path)

- ONE seeded `numpy.random.Generator`, threaded from the experiment config. No `np.random.*` module calls,
  no `import random`, no wall-clock in behavior-affecting code.
- Every experiment = config + seed + git SHA → a committed results manifest. Numbers without manifests do
  not exist. Every reported number is a 10-run mean ± std.
- Per-sample everything: participant set, arena size, round count, presenter count all derive from THIS
  sample's participants. Nothing crowd-sized is a constant.
- `prior_performance` (multiplier, 0.7–1.3) and `prior_accuracy` (rate, 0–1) are different things. Influence
  math uses the former; vote allocation uses the latter. Never swap them.
- Certainty: clamped to [0.01, 0.99] on every update; reset to its training-time value at every new sample.
  Trust, prior_performance, prior_accuracy, and history persist.
- Missing features = the agent sits out that sample. The method NEVER imputes.
- Agent eval metrics come from the train-side eval slice. The test split is untouchable except at final
  evaluation.
- Use the spec §2 state names exactly. No synonyms, no renames.
- Tests land WITH the feature, in the same ticket. Every numeric mechanism gets exact-arithmetic pins and
  both-sides boundary tests.
- Algorithmic code (interaction math, aggregation, swarm rounds, banding) carries comments explaining system
  meaning, assumptions, and what must not change casually. No line-by-line narration. Bad comments are
  contract violations.

## STOP conditions — pause and ask a human, do not improvise, if ANY of these happen

- The ticket and the spec disagree (spec wins; the discrepancy is a bug to REPORT).
- A spec MUST seems wrong or impossible.
- You cannot make a test pin pass without changing the mechanism it pins.
- Anything on the preamble §3 forbidden-shortcut register starts looking "necessary."
- You need information from outside this repo (clean-room).
- A decision arises that the ticket/plan didn't make (that's a plan bug — record it, get it ruled).

## Session modes (state your mode at the start of every session)

- **REVIEW** — read files, run checks, report findings with severity tags. Do not edit.
- **PLAN** — produce a formal plan per the preamble §9 invocation. Change nothing until it is approved.
- **IMPLEMENT** — work an approved ticket/plan per its sequence (preamble §10 invocation).
- **DIAGNOSE** — something is broken; investigate and report before fixing anything.
- **HANDOFF** — update `AGENT_HANDOFF.md` to reflect the current state, and stop.

## Ticket close checklist

The full checklist is preamble §6 — state each item explicitly in your final report. The ones most often
missed: independent review (§8 — someone/something that did NOT implement it signs off; a different AI
system, not a fresh session of the same one), the `AGENT_HANDOFF.md` update, and the results-manifest
commit. Reviewer flags use severity tags: every finding starts `[Critical]`, `[High]`, `[Medium]`, `[Low]`,
or `[Informational]`, in discovery order.

**Humans commit. AI sessions never commit or push unless a human explicitly asks in that session.**

## Check suite

Ratified by ticket W0-01 (see its plan). Until W0-01 lands, the target is:

```bash
ruff check .
ruff format --check .
mypy src tests
pytest        # full suite, slow marks included — the ticket-close gate
```

All green before any merge. If any check fails, the handoff must say which failed and why.
