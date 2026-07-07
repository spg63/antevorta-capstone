# Agent Handoff

**Last updated:** 2026-07-07 (stakeholder + Claude, Codex-review fold-in) — branch `main` @ `bfd18f3` +
UNCOMMITTED review-disposition tree (commits happen at explicit stakeholder direction; the standing rule
remains: humans commit).

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

## CURRENT STATE (2026-07-07, repo bring-up)

- **Done:** Repository created by the stakeholder (**PUBLIC**, MIT-licensed). Pre-laid: directory skeleton,
  seed `.gitignore`, `README.md`, control documents (`CLAUDE.md`, `AGENTS.md`, this file,
  `docs/agent_prompts/`). Ticket set in `tickets/` (index v1.11: 42 tickets, 9 waves, 5 streams); spec at
  `docs/WoC-Bots_Implementation_Spec.md` (**v1.2**). The Codex control-plane review (preamble §8's first
  live execution) is folded in: ten findings accepted — four spec method rulings (arena capacity,
  exact-arithmetic example, prior_accuracy totality, small-N swarm fallback) + process fixes — full
  disposition in `tickets/02_CODEX_CONTROL_PLANE_REVIEW_2026-07-07.md`. Stakeholder rulings live in the
  index changelog (v1.2–v1.11) and the W0-01 plan §12.
- **In flight / blocked:** No code exists; no ticket has started. Nothing is blocked: the W0-01 plan is
  **APPROVED (stakeholder, 2026-07-07)** — the only gate left before W0-01 code is the team's own STEP-0.
- **Owner-attention:** (1) Team: run the W0 STEP-0 ruling meeting — the wave plan's O1–O6 (O1 and O6
  already ruled by fact: the repo exists, MIT license landed) and the W0-01 plan's O7–O9; record rulings in
  both RESULT blocks. (2) Team: fill stream-owner GitHub handles (index streams table → the plan's
  CODEOWNERS §7-S4).
- **Next step:** the STEP-0 meeting, then CORE + EVAL implement W0-01 while DATA starts W1-01 (no
  blockers) and AGENTS/ARENA draft their W2-01/W3-01 mini-plans.
- **Five-minute test:** `ls tickets/ | wc -l` → 47 files (42 tickets + index + preamble + 2 plans + the
  02_ review doc); the FIRST changelog entry in `tickets/00_INDEX.md` is v1.11 (Codex review fold-in);
  `grep -c "RULED" tickets/02_CODEX_CONTROL_PLANE_REVIEW_2026-07-07.md` ≥ 3. If the newest changelog entry
  or the git history describes work this CURRENT STATE doesn't mention, this handoff is stale — fix it
  FIRST.
