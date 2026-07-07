# AGENT KICKOFF — the targeted reading protocol

You are starting a work session in the WoC-Bots Reimagined repository. Complete this protocol BEFORE writing
any code, in this order. The boundaries exist to keep your context spent on what governs your work — and to
keep the clean-room intact.

## 1. Read IN FULL (mandatory, no skimming — order matters)

1. `CLAUDE.md` (repo root) — the binding session instructions, hard rules, and STOP conditions.
2. `tickets/01_MANDATORY_PREAMBLE.md` — the contract every ticket runs under.
3. `AGENT_HANDOFF.md` — the header line + the CURRENT STATE section only (see §3).
4. The ticket you were assigned, in full.
5. That ticket's `_PLAN.md`, in full, if one exists. If it says DRAFT, STOP — a draft plan is not
   implementable; report and wait.

## 2. Read IN PART (targeted — only what your work binds)

- **The spec** (`docs/WoC-Bots_Implementation_Spec.md`): ONLY the sections your ticket's "Binding spec
  sections" line names — but those sections in full, including their worked examples. Do not read the whole
  spec into context; do not guess at a section you didn't read.
- **`tickets/00_INDEX.md`**: the changelog blockquote (newest few entries), your ticket's wave table row
  (Blocked-by must be ✅ before you start), and the Streams section if your work crosses a directory you
  don't own.
- **Code**: every file and function your ticket/plan cites — read the cited functions IN FULL, not their
  signatures. If a function you must change calls another whose behavior matters, read that too.
- **Results manifests / swarm traces / encounter logs**: only the specific artifacts your ticket names
  (e.g., a reproduction target or a STEP-0 gate) — never wholesale.

## 3. NEVER read (hard boundaries)

- **Anything outside this repository.** The clean-room rule: no original WoC-Bots code, no other
  implementations, no going hunting. The spec, the publications, and `antevorta-db` (provided separately)
  are the entire universe. Wanting more = STOP and ask the stakeholder.
- **`AGENT_HANDOFF.md`'s `## PRIOR` sections** — history, not state. Read them only if explicitly
  investigating how something came to be, and never implement from them.
- **Raw datasets into context.** Work with the committed fixture excerpts; datasets are for code to read,
  not for you to paste.
- **Closed tickets' bodies** (status ✅ in the index) — reference their code and tests instead; the tree is
  the truth about what landed.

## 4. Then, before any code

1. State your session mode (`CLAUDE.md` §Session modes).
2. Restate your ticket's acceptance criteria in your own words — one sentence each. If you can't, you
   haven't read enough; go back.
3. Produce the written mini-plan (preamble §0.1c): sequenced steps, files to touch, the test list with what
   each test asserts, open questions. For plan-backed tickets this is the SESSION plan reconciling the
   formal plan against your fresh reads — flag any drift, do not reconcile silently.
4. Present it for review and WAIT for approval (a different team member, the stakeholder, or the session
   driver acting as reviewer — someone other than you says "go").
5. Only then: implement. Close per preamble §6 — including the independent review (§8) and the
   `AGENT_HANDOFF.md` update.
