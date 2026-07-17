# Agent Handoff

**Last updated:** 2026-07-16 (Rutvij driving a Claude session, mode IMPLEMENT) — branch `w0-scaffold`
(local; W0-01 + W0-02 implemented, NOT merged, NOT closed; humans commit — Rutvij commits/pushes). Plan map
unchanged: the dedicated plans own W0-01 and W0-02; the wave plan owns W0-03/04 + the shared O1–O6/STEP-0.

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

## CURRENT STATE (2026-07-16, W0-01 + W0-02 implemented on branch, pending ratification + review)

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
