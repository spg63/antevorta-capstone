# Agent Handoff

**Last updated:** 2026-08-08 (Manan Patel, CORE W4-04 — branch
`manan/w4-04-tiers-mechanism-comparison` @ `2c19b25`, pending manual PR merge)


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

## CURRENT STATE (2026-08-08, W4-04 on branch — pending review + manual merge)

- **Done:** W4-04 on `manan/w4-04-tiers-mechanism-comparison` (Manan Patel): tiers, mechanism-comparison +
  synthetic-anchor kinds, evaluation loop, tests. Plan + closing report in `tickets/W4-04_*`. Process doc
  `docs/BRANCHING.md`. W4-01/02/03 on `develop` (PR #17); W4-04 **not** merged yet.
- **In flight / blocked:** Manual PR merge to `develop`. W4-01 arena integration blocked on W3-02/04. Branch
  protection on `main`/`develop` not enabled — needs repo admin.
- **Owner-attention:** **Manan** — PR to `develop`, label W4-04, link Issue #9, independent review. **Admin
  (spg63)** — enable branch protection per `docs/BRANCHING.md`.
- **Next step:** Open/refresh PR; merge after CI + review; flip W4-04 status in index with reviewer line.
- **Five-minute test:** `git log develop -1 --oneline` → no W4-04 tiers; branch tip → `2c19b25` or later.

## PRIOR (2026-07-31, W3-01 implemented on branch, pending review)

- **Done:** W3-01 (grid geometry + random init) implemented on branch
  `ticket/w3-01-plan`. `Arena` (rows/cols per §6.1 v1.2, occupancy ≤ 2 via
  `_GridCell`) + `RandomInitPolicy` (uniformly random empty cell, spec §6.2)
  land in `src/wocbots/arena/`, replacing the W0-02 constructor-only stub.
  Check suite green: ruff / ruff-format / mypy-strict / pytest all pass
  (arena scope: 21 passed). Pure-mechanism ticket: results manifest N/A.
  Check suite green: ruff / ruff-format / mypy-strict / pytest all pass (136
  passed, 1 skipped — the skip is test_w2_02_classifier.py's W1-05 real-data
  band check, pre-existing, unrelated to W3-01).
  Closing report: `../W3-01_grid-geometry-init_CLOSING-REPORT.md`.
- **In flight / blocked:** W3-01 close blocked on independent review (§8 —
  someone who didn't implement it). W3-02 (movement/rounds) can start its
  mini-plan now that `Arena`/`RandomInitPolicy` exist, but stays blocked on
  W3-01's review sign-off per the index.
- **Owner-attention:** Reviewer needed for W3-01 — read the diff vs. the
  ticket and plan, check the forbidden-shortcut register, confirm the test
  pins (N=5/10/26 geometry, density sweep 3–200, occupancy-cap, init
  determinism).
- **Next step:** independent review of W3-01 → flip W3-01 in `00_INDEX.md` →
  W3-02 fully unblocked.
- **Five-minute test:** `uv run pytest tests/unit/test_grid_geometry.py
  tests/unit/test_random_init_policy.py -q` → 12 passed;
  `python -c "from wocbots.arena import Arena, RandomInitPolicy"`.

## PRIOR (2026-07-25, W1 DATA stream merged into this tree — needs review)

- **Done:** Reconciled the W1 DATA-stream tree (drafted independently on a divergent branch, never committed,
  no shared git history with this tree) into `develop` by file-level merge — no `git merge` was possible, so
  every overlapping file was diffed and resolved by hand, then validated by actually running the check suite.
  Brought in: `src/wocbots/data/{provenance,hollywood,labels,splits,anchor_analysis}.py`,
  `tests/unit/data/` (6 files) + `tests/fixtures/{tmdb5000,movielens20m}/`, `data/DATA_PROVENANCE.md`,
  `docs/WAVE_GUIDE.md`, and the completed `tickets/W1-04_labels-validation-gate.md` /
  `tickets/W1-06_anchor-analysis.md` (over develop's blank templates). Rewrote `src/wocbots/data/__init__.py`
  (was a placeholder stub) to export the public API, matching the sibling-package convention. Two real
  conflicts had to be resolved, not just copied over: (1) `splits.py`/`anchor_analysis.py` called
  `numpy.random.default_rng()` directly, which trips the W0-04 RNG-discipline guard (only
  `experiments/harness.py` may originate a Generator) — refactored both to take a threaded
  `rng: np.random.Generator` param instead (mirrors `agents/classifier.py`'s `_seed_from` pattern); the W1
  tests that called `make_split(..., seed=N, ...)` / `rank_features(..., seed=N)` were updated to pass
  `rng=np.random.default_rng(N)`. (2) `pyproject.toml` was missing `scipy` (used by `anchor_analysis.py`'s
  point-biserial correlation) and `pandas-stubs` (mypy-strict needs it now that `data/` imports pandas) — added
  both, plus a named `scipy.*` mypy override alongside the existing `sklearn.*` one, and regenerated `uv.lock`
  (`uv lock`) so the two stay in sync. Also dropped `data/hollywood_features_labeled_variant_a.csv`, which the
  W1 tree carried but which contradicts this repo's own `.gitignore`/`data/README.md` policy (derived CSVs are
  never committed — only `DATA_PROVENANCE.md` belongs in `data/`) and isn't documented anywhere as an intended
  deliverable; looked like session scratch output. ~40 W1 test functions got `mypy --strict` return/param
  annotations they were missing (develop's test suite is fully strict-typed; W1's wasn't). Check suite green
  via the documented `uv` workflow: `uv run ruff check .` / `uv run ruff format --check .` / `uv run mypy src
  tests` all clean; `uv run pytest -q` → **156 passed, 11 skipped, 1 xfailed** (the xfail is W1-04's own
  documented class-balance pin, not new). The pre-existing git-repo-dependent test failures in
  `test_harness.py`/`test_manifest.py`/`test_provenance.py` (they shell out to `git rev-parse HEAD`) are
  unrelated to this merge — confirmed identical on unmodified `develop` before touching anything; they'll pass
  once this lands inside a real git checkout.
- **In flight / blocked:**
  1. **Carried forward, still open — W1-04's gate is escalated, not closed; W1-02 is still blocked.** Merging
     the code did NOT resolve this. Variant (a) `revenue > 2×budget` label balance measured 43.9/56.1 against
     the spec's published 47.5/52.5 (±1pt tolerance) — outside tolerance, root-caused (not confirmed) in
     `data/DATA_PROVENANCE.md` §6 to a likely MovieLens `link.csv`/`movie.csv` snapshot-vintage mismatch. W1-02
     (the `antevorta-db` ground-truth reconciliation that would confirm or refute this) never ran — no
     `antevorta-db` source or built SQLite has been supplied. **No label has shipped.** W1-06's anchor ranking
     (`budget` ranks last against spec's §9.2 expectation that it tops the list) is provisional for the same
     reason and hasn't been re-run against a validated label.
  2. W2-03's own upstream note (see the demoted entry below) — the Hollywood crowd configs
     (`configs/crowd_hollywood_*.yaml`) encode `budget` as anchor **provisionally**, pending exactly this. That
     dependency is now unblocked at the code level (the DATA modules exist) but not at the data-quality level
     (item 1 above) — re-running W1-06 for real numbers is still gated on W1-02/a stakeholder ruling.
  3. This merge itself has had no independent review (preamble §8) — I (Claude) did both the reconciliation and
     its own validation; that doesn't count. Not committed (AI sessions don't commit).
  4. W2-03 is also still pending its own independent review, unchanged by this merge (see demoted entry).
- **Owner-attention (Dr. Grimes / the team):**
  1. Same asks as the W1 branch originally raised, still outstanding: supply `antevorta-db` (source or built
     SQLite) to unblock W1-02, or rule on how to proceed without it; rule on whether the W1-04 join shortfall
     (4,227 matched movies vs. spec reference 4,722) is a data-vintage issue, a pipeline defect, or grounds to
     accept revised reference numbers for this dataset snapshot.
  2. A human or different-AI reviewer (not this session): check the merge diff, in particular (a) whether
     dropping `hollywood_features_labeled_variant_a.csv` was the right call, and (b) the `seed: int` →
     `rng: Generator` signature change to `make_split`/`rank_features` — a real API change, not a mechanical
     port, worth a second pair of eyes before anything downstream (W2-04, W5-*) builds on it.
  3. Rutvij: W2-03 still needs committing per its own closing report, independent of this merge.
- **Next step:** get an `antevorta-db` artifact (or a stakeholder ruling on the MovieLens snapshot question)
  to unblock W1-02, then re-run the W1-03→W1-04 chain for real and choose/ratify a shipped label; re-run W1-06
  once that lands. In parallel, get this merge independently reviewed and committed.
- **Five-minute test:** `uv sync && uv run pytest -q` → expect `156 passed, 11 skipped, 1 xfailed` (needs a
  real git repo for the harness/manifest/provenance tests to pass; they'll show as failures with `fatal: not a
  git repository` in a bare working copy — that's the pre-existing baseline, not new). `uv run mypy src tests`
  → `Success: no issues found`. If `src/wocbots/data/hollywood.py` is absent, this entry is stale — fix it
  FIRST.

## PRIOR (2026-07-20, W2-03 implemented on branch, pending review)

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
