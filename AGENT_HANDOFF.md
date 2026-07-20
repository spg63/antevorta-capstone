# Agent Handoff

**Last updated:** 2026-07-20 (Rutvij driving a Claude session, mode IMPLEMENT) — W2-03 implemented in the
working tree on branch `rootwij/w2-03-feature-assignment-crowd` (off `w2-02-classifier-train-eval`),
uncommitted, pending independent review (humans commit — Rutvij commits/pushes). Lineage: W2-02 was
implemented 2026-07-20 on `w2-02-classifier-train-eval` (= W2-01 + the W0-03/04 harness), also pending review.

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

## CURRENT STATE (2026-07-20, W2-03 implemented on branch, pending review)

- **Done:** W2-03 (feature-assignment policy + crowd builder) implemented on
  `rootwij/w2-03-feature-assignment-crowd` (based off `w2-02-classifier-train-eval`; implementer: Claude
  session driven by Rutvij — preamble §8 review independence). Paths: `src/wocbots/agents/crowd.py`
  (`AssignmentPolicy` seam + `SeededRandomAssignment` (§5.1) / `ExplicitAssignment`; `CrowdConfig` +
  `SeededAssignmentConfig` / `ExplicitAssignmentConfig` / `AgentGroup` with `from_yaml`; `build_crowd`
  config→roster→train_crowd→prune; `CrowdManifest` + `write_/read_crowd_manifest`),
  `configs/crowd_hollywood_26agent.yaml` (§9.3 seeded 1/5/10/10 mix), `configs/crowd_hollywood_5agent.yaml`
  (§9.2 explicit matched crowd), `configs/crowd_smoke.yaml` (synthetic, runnable), and
  `tests/unit/test_w2_03_crowd.py` (30 tests: the 3 ticket reqs + §10.9 barrier + edges). Assignment yields
  feature-name rosters only (decoupled from agent internals — the forbidden shortcut); one Generator threads
  deal→train so same config+seed ⇒ byte-identical crowd manifest; `revenue` barred at config validation AND by
  the builder's roster guard (§10.9). Check suite green (ruff / ruff-format / mypy-strict / pytest:
  **112 passed, 1 skipped**, the skip = W2-02's W1-05 slow band test). No source outside this ticket touched
  (`agents/__init__.py`, `pyproject.toml`, W2-02 modules all unchanged). Pure-mechanism ticket: results
  manifest N/A. Closing report: `../W2-03_feature-assignment-crowd_CLOSING-REPORT.md`.
- **In flight / blocked:** W2-03 close blocked on independent review (§8 — NOT Rutvij or this Claude lineage;
  a CORE teammate reviewing AGENTS, or a different AI e.g. Codex). Upstream: **W1-06 (the anchor RESULT) is
  unfilled** and the W1 DATA wave hasn't landed — so the Hollywood configs encode the spec-named anchor
  (`budget`, §5.1) + §9.2 columns as **provisional**, and W2-04's real §9.2 reproduction stays gated on W1-05
  (eval slice) + W1-06 (final anchors/column names). W2-02 is likewise implemented-but-unreviewed on its branch.
- **Owner-attention:** (1) Reviewer (CORE/consumer-reviews-producer, or Codex): read the full W2-03 diff vs the
  ticket, check the forbidden-shortcut register (assignment⊥internals; §10.9 barrier) against the code, confirm
  the test pins (26-agent mix, prune integration, determinism). (2) DATA: W1-05 + W1-06 unblock W2-04's
  reproduction and let the Hollywood configs' names be finalized. (3) Rutvij: commit the branch (recipe in the
  closing report §5) — add only the 5 W2-03 paths + this handoff; **do NOT stage `README.md`** (CRLF mount
  noise, not a real change).
- **Next step:** independent review of W2-03 → flip W2-03 in `00_INDEX.md` to `✅ (reviewed: <who>, <date>)` →
  W2-04 / W5-02 unblock.
- **Five-minute test:** `pytest -q` → 112 passed, 1 skipped; `ls src/wocbots/agents` → `__init__.py agent.py
  classifier.py crowd.py training.py`; `python -c "from wocbots.agents.crowd import build_crowd, CrowdConfig"`
  imports clean; `git log w2-02-classifier-train-eval..rootwij/w2-03-feature-assignment-crowd` non-empty once
  committed. If `crowd.py` is absent or the index shows W2-03 ✅, this entry is stale — fix it FIRST.

## PRIOR (2026-07-17, W2-01 implemented, pending mini-plan ratification + review)

- **Done:** W2-01 (Agent state + public profile) implemented per its mini-plan
  (`W2-01_agent-state-profile_MINIPLAN.md`, drafted 2026-07-16, DRAFT — its proposed Q1–Q6 rulings are
  applied but NOT yet ratified; implementer: Claude session driven by Rutvij — preamble §8 review
  independence). Paths: `src/wocbots/agents/agent.py` (`ConfidenceWeights`, `HOLLYWOOD_WEIGHTS`,
  `Agent` with the §2 table + §6.5 `public_profile()` + §6.6 `reset_certainty()`),
  `src/wocbots/agents/__init__.py` (stub replaced, seam import path unchanged),
  `tests/unit/test_w2_01_agent_state.py` (15 tests incl. the ticket's 1e-12 init pins). One mechanical
  completion to adjudicate at review (the W0 D1/D2 pattern): `test_w0_02_seams.py`'s Agent-stub
  assertion retired (the stub no longer exists — its contract said W2-01 replaces it). Check suite
  green locally: 36 passed, ruff check + format clean, mypy strict clean. Pure-code ticket: results
  manifest N/A (mini-plan §2-S6).
- **In flight / blocked:** W2-01 close blocked on: (a) mini-plan Q1–Q6 ratification + independent
  review (must not be Rutvij or this Claude lineage — CORE teammate or a different AI system), (b) PR
  review + merge to `develop`, (c) index flip with a `reviewed:` line. Separately, W0-01/W0-02
  governance close-out was never done: PR #11 merged with NO recorded independent review, index not
  flipped, `AGENT_HANDOFF` was stale until this entry, STEP-0 RESULT blocks still unfilled, CODEOWNERS
  handles still `*-TBD`, GitHub issues #2/#3 (W0-01/02) still open. PR #13 (W0-03/04) has no filled
  template and no reviewer.
- **Owner-attention:** (1) CORE (Anurag): ratify/adjust the W2-01 mini-plan's Q1–Q6, review the W2-01
  PR; also a post-merge review of PR #11 so W0-01/02 can flip with a `reviewed:` line. (2) Team: fill
  both STEP-0 RESULT blocks (named-and-dated), send GitHub handles for CODEOWNERS. (3) EVAL: review
  PR #13 (consumer-reviews-producer). (4) Stakeholder: O8 branch protection now that CI exists, and on
  `develop` too if it stays the integration branch (ruling wanted: is `develop` official? Nothing in
  the control plane names it).
- **Next step:** Rutvij (native git, not the sandbox): `git fetch origin`, `git switch -c
  w2-01-agent-state origin/develop`, commit ONLY `src/wocbots/agents/`, the two test files, and this
  handoff (the tree shows ~58 CRLF-noise "modified" files — do NOT `git add -A`), push, open a PR to
  `develop` with the template filled, Q1–Q6 listed for ratification in the PR body.
- **Five-minute test:** `uv run pytest -q` → 36 passed; `grep -l current_prediction
  src/wocbots/agents/agent.py` non-empty. If the index shows W2-01 ✅ or `agents/agent.py` doesn't
  match the description above, this entry is stale — fix it FIRST.

## PRIOR (2026-07-16, W0-01 + W0-02 implemented on branch, pending ratification + review)

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
