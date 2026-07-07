# W0-01 — Repository scaffold, packaging, check-suite ratification, CI — IMPLEMENTATION PLAN

> **STATUS: ✅ APPROVED (stakeholder, 2026-07-07).** Implementation may begin once the §6 STEP-0 RESULT
> block is filled (team rulings O7–O9 + version captures).
>
> **About this plan.** Produced under the preamble §9 invocation, as the per-ticket exemplar: every decision
> made and pinned or routed to the ruling authority with a recommended default; grounding facts re-verified
> against the binding documents (this is a greenfield ticket — "read all related functions" resolves to
> full re-reads of the spec/preamble/wave-plan sections named in §4, and "cross check with the uflogs"
> resolves to §4's honest statement that no observability artifacts exist yet to check against); open
> questions surfaced in §12 rather than improvised around. Section skeleton per the wave plan's READ-ME-FIRST
> box.

**Ticket:** `W0-01_repo-scaffold-ci.md`. **Precedence:** the spec > this plan > the ticket. This plan
supersedes the wave plan's §7-S1/S5/S6 for W0-01; the wave plan's §3 rulings (O1–O6) and STEP-0 are SHARED
wave inputs and are not re-opened here.
**Wave:** W0. **Blocked by:** —. **Blocks:** W0-02, W0-03, and every ticket in the set (this repo is where
they all land).
**Binding spec sections:** §11 (layout), §0 (MUST/SHOULD/MAY). **Binding preamble sections:** §5 (check
suite — ratified HERE), §6 (close checklist this repo's PR machinery must carry), §8 (independent review —
made STRUCTURAL here via branch protection).
**Severity of getting it wrong:** 🔴 foundational — this ticket is every later ticket's developer experience
and the enforcement substrate for the review rule.
**Ruling authority:** O1–O6 inherited from the wave plan (team-ruled, its STEP-0). NEW decisions O7–O9 (§3)
are likewise **delegated to the team** (index v1.2's delegation pattern) — recommended defaults below;
overruling needs recorded rationale.

---

## 1. Metadata (see header above)

Self-contained for W0-01: an implementer following §9 and pinning §10 ships the ticket without one silent
decision. Written from full re-reads of: spec §11/§9.1/§0; preamble §§0–10 (including the new §8 review rule
this plan operationalizes); the wave plan §3/§6/§7-S1/S5/S6/§12; the W0-01 ticket; the index v1.5 streams
table (CODEOWNERS encodes it).

---

## 2. Why this ticket exists (system meaning)

Everything the project produces — mechanism code, experiments, the report — lands through this repository's
machinery. Three properties must be true from the first commit, because they cannot be retrofitted cheaply:
(1) **"green" is unambiguous** — one ratified check suite, identical locally and in CI; (2) **the disciplined
path is the only path** — protected main, PR-only merges, review-before-merge enforced by the platform rather
than by memory; (3) **ownership is structural** — the index's one-writer-per-directory streams rule encoded
in CODEOWNERS so the platform requests the right reviewer automatically. This ticket contains zero wocbots
logic on purpose: its whole job is to make every subsequent ticket's job smaller.

---

## 3. Decisions (team-ruled; fill into §6's RESULT block)

Inherited and NOT re-opened: **O1 — ✅ RULED BY FACT (stakeholder, 2026-07-07): the repo is
`antevorta-capstone`** (stakeholder-created; the PACKAGE remains `wocbots`; src layout; PRIVATE until
publication per §12-Q3; bare directory skeleton, seed `.gitignore`, and README pre-laid — §7-S1 becomes
verify-and-complete rather than create-from-nothing), **O2** (Python ≥3.11, CI matrix 3.11/3.12), **O3**
(pydantic v2, `extra="forbid"`), **O4** (mypy strict), **O5** (GitHub Actions; fast per-commit + scheduled
full), **O6** (license: MIT recommended) — all per the wave plan §3.

New, surfaced by this plan's depth:

- **O7 — Dependency locking.** **Recommended: `uv`** — pyproject-native, a committed `uv.lock`, fast installs
  in CI, one tool for venv+lock+install. *Alternatives:* pip-tools (`requirements.lock`, more familiar, more
  moving parts); bare pip with only pyproject minimums (rejected as default: unlocked transitive dependencies
  make "same config + same seed" quietly false across machines — reproducibility is a stated deliverable and
  the lockfile is its dependency-level half).
- **O8 — Branch protection & merge policy.** **Recommended:** `main` protected: PRs only; 1 approving review
  from a non-author (the platform floor under preamble §8 — §8's independence rule still applies on top);
  required checks = the fast CI job; stale approvals dismissed on new pushes; force-pushes and deletions
  blocked; admins included. Auto-merge enabled so "approved + green" lands without babysitting. *Alternative:*
  2 approvals — rejected as default for a 5-person team (throughput cost exceeds the marginal catch rate at
  this scale; revisit if review quality degrades).
- **O9 — Coverage posture.** **Recommended:** `pytest --cov` REPORTING in CI logs, **no threshold gate**.
  A coverage floor this early is a brittle vanity metric that punishes deleting dead code and rewards
  assertion-free tests; the preamble §4 pin discipline is the real coverage policy. Revisit at Q1 exit with
  data. *Alternative:* an 80% gate — rejected as default for exactly those failure modes.

**Encoding rule:** as the wave plan §3 — one named line per ruling in §6's RESULT block; a site comment
(`# O7 ruling (team, <date>): uv + committed lockfile`) where a file embodies it.

---

## 4. Verified grounding facts (re-verify before coding)

- **Spec §11** prescribes the package layout this repo hosts; the layout lands here as EMPTY packages —
  W0-02..04 fill them (wave plan owns those). Spec §0 defines the MUST/SHOULD/MAY the tool configs must not
  contradict.
- **Preamble §5** currently carries the check-suite TARGET with the note "until W0-01 lands, this block is
  the target, not the law." Replacing that note with ratified, exact commands is a named deliverable (§7-S7).
- **Preamble §8** (independent review) requires: non-implementer review per ticket close, recorded sign-off.
  The platform can enforce the per-PR floor (O8) and this plan wires it; the per-ticket-close sign-off and
  the different-AI-system rule remain process (the PR template carries them as checkboxes — §7-S5).
- **Index v1.5 streams table** defines directory ownership: CORE `experiments/ aggregation/ protocols.py`;
  DATA `data/`; AGENTS `agents/`; ARENA `arena/ interaction/`; EVAL `evaluation/`. CODEOWNERS (§7-S4) is its
  direct transcription; if the table is re-dealt (the index allows it), CODEOWNERS changes in the same PR.
- **Wave plan §12-R5** flags ruff-format drift → exact pin (carried into §7-S2's pyproject).
- **Greenfield facts:** no code exists; no manifests/encounter logs/swarm traces exist yet, so there is
  nothing to cross-check against observability artifacts — the FIRST such artifact is produced by W0-04
  (`dummy_smoke` manifest). This plan therefore creates the conditions for future cross-checking (CI links,
  committed manifests) rather than consuming any.
- **Cross-platform fact:** five students, unknown mix of macOS/Windows/Linux. CI pins truth on
  `ubuntu-latest`; local tooling must be OS-agnostic (uv is; the check-suite commands are; nothing in this
  ticket may assume a shell beyond POSIX-or-PowerShell-neutral invocations documented in the README).

---

## 5. Execution-path maps

**The life of a change:**
```
branch → commits → PR opened
  └─ CI fast job: ruff check · ruff format --check · mypy src tests · pytest -m "not slow"   (matrix 3.11/3.12)
  └─ CODEOWNERS auto-requests the owning stream's review
  └─ non-author approval (preamble §8 floor) + green checks → auto-merge to protected main
       └─ scheduled/dispatch job (weekly): FULL pytest incl. slow marks on main
```
**The life of a fresh clone:**
```
git clone → uv sync (creates venv from uv.lock) → the four check-suite commands → all green in <5 min
```
Two structural properties fall out: an unreviewed or red change cannot reach main (platform-enforced), and a
new machine reproduces the toolchain exactly (lockfile-enforced). Both are pinned in §10.

---

## 6. STEP 0 — pre-code gate (fill the RESULT block before coding)

1. The wave plan's STEP-0 (O1–O6) must be filled FIRST — it is the shared wave gate. If already filled, cite
   it; do not re-rule.
2. The team rules O7–O9 (one sitting; record rationale for any overruled default).
3. Capture the exact tool versions being pinned (current ruff release, uv version, Python patch versions on
   the CI images) — they go into pyproject/lockfile and are recorded below.
4. Confirm repository + branch protection settings are applied (screenshot or settings-as-code) and one
   empty-commit PR has traversed the full path (CI + review + auto-merge) end to end.

If any O-ruling overturns a default in a way that changes §7, fold the change into this plan first, then
implement the amended plan.

---

## 7. Specification

### S1 — Repository layout (this ticket's slice)

```
wocbots/
├── pyproject.toml               # S2
├── uv.lock                      # O7 (committed)
├── README.md                    # S6
├── LICENSE                      # O6
├── .gitignore                   # S3
├── CODEOWNERS                   # S4 (root or .github/ — pick one, document)
├── .github/
│   ├── pull_request_template.md # S5
│   └── workflows/
│       ├── ci.yml               # S5
│       └── scheduled.yml        # S5
├── configs/                     # (.gitkeep — W0-04 adds dummy_smoke.yaml)
├── results/manifests/           # (.gitkeep — manifests are COMMITTED artifacts)
├── src/wocbots/
│   ├── __init__.py              # __version__ = "0.1.0" only
│   ├── agents/__init__.py       # empty — W2 fills
│   ├── arena/__init__.py        # empty — W3 fills
│   ├── interaction/__init__.py  # empty — W3 fills
│   ├── aggregation/__init__.py  # empty — W4/W6 fill
│   ├── data/__init__.py         # empty — W1 fills
│   ├── evaluation/__init__.py   # empty — W5 fills
│   └── experiments/__init__.py  # empty — W0-03/04 fill
└── tests/
    ├── unit/test_scaffold.py    # §10.1/.2 pins
    └── integration/             # (.gitkeep; slow-marked tests arrive with W0-04)
```

NOTE deliberately absent from this ticket (owned elsewhere): `types.py`, `protocols.py`, stubs (W0-02);
`experiments/*.py` modules (W0-03/04). Empty packages land now so imports and CODEOWNERS paths are stable.

### S2 — pyproject.toml (exact content, modulo STEP-0 version captures)

```toml
[project]
name = "wocbots"
version = "0.1.0"
description = "A modular Python toolkit for swarm-based classification (WoC-Bots)"
requires-python = ">=3.11"                    # O2
license = {file = "LICENSE"}                  # O6
dependencies = [
  "numpy>=1.26", "pandas>=2.1", "scikit-learn>=1.4", "pydantic>=2.6", "pyyaml>=6.0",
]

[dependency-groups]                            # O7: uv-managed
dev = [
  "pytest>=8", "pytest-cov>=5", "mypy>=1.8",
  "ruff==<STEP-0 exact>",                      # wave plan §12-R5: format drift → EXACT pin
]

[tool.ruff]
line-length = 110
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]     # errors, pyflakes, isort, pyupgrade, bugbear, simplify

[tool.mypy]                                    # O4
strict = true
# per-module relaxations: NONE at scaffold time; any later exception is named + commented (wave plan §3-O4)

[tool.pytest.ini_options]
markers = ["slow: multi-minute integration runs"]
addopts = "--strict-markers"                   # unknown marks are ERRORS, not silent no-ops
# NO default -m filter: plain `pytest` = the full closeable gate (wave plan §7-S1 ruling)

[tool.coverage.run]                            # O9: report-only
source = ["src/wocbots"]
```

### S3 — .gitignore (the load-bearing entries)

Standard Python ignores PLUS, explicitly commented: `data/raw/` ignored (provenance doc is the tracked
artifact, W1-01); `results/manifests/*.json` **NOT ignored** — a comment states manifests are committed
deliverables, because the default reflex is to ignore generated files and that reflex is wrong here.

### S4 — CODEOWNERS (the streams table, transcribed)

```
/src/wocbots/experiments/   @<CORE>
/src/wocbots/aggregation/   @<CORE>
/src/wocbots/protocols.py   @<CORE>
/src/wocbots/data/          @<DATA>
/src/wocbots/agents/        @<AGENTS>
/src/wocbots/arena/         @<ARENA>
/src/wocbots/interaction/   @<ARENA>
/src/wocbots/evaluation/    @<EVAL>
/configs/                   @<CORE>
/results/                   @<EVAL>
*                           @<CORE>            # default owner: the integration stream
```
GitHub handles filled at STEP-0. Re-dealing streams (index allows it) = editing this file in the same PR as
the index change — CODEOWNERS drifting from the streams table is a defect class, pinned by §10.5.

### S5 — CI workflows + PR template (review made structural)

`ci.yml` (per-commit): job `checks` on `ubuntu-latest`, matrix Python {3.11, 3.12}; steps: checkout → install
uv → `uv sync --frozen` (the lockfile IS the environment; `--frozen` fails loud on drift) → `ruff check .` →
`ruff format --check .` → `mypy src tests` → `pytest -m "not slow" --cov` (coverage printed, not gated — O9).

`scheduled.yml`: weekly cron + `workflow_dispatch`; same setup; full `pytest --cov`.

`pull_request_template.md` — the process half of preamble §8, as checkboxes the reviewer ticks:
```
## Ticket
Closes: W_-__  (link)
## Implementer(s)
Human: ____   AI session(s): ____            # who DROVE the AI counts as implementer (preamble §8)
## Reviewer attestation (non-author; for ticket-closing PRs: preamble §8 independence)
- [ ] I did not implement this work (didn't write it, didn't drive the AI session that wrote it)
- [ ] Read the full diff against the ticket/plan (not a summary)
- [ ] Forbidden-shortcut register (preamble §3) checked against the actual code
- [ ] Test pins exist and assert what the ticket says they assert
- [ ] (ticket-closing PRs) index status flip includes `reviewed: <who/what>, <date>`
```
Branch protection per O8 enforces: PR-only, 1 non-author approval, required check = `checks`, stale-approval
dismissal, no force-push, admins included, auto-merge on.

### S6 — README (structure, not prose)

Sections, in order: what this is (3 sentences + spec link); setup (`uv sync`, one command per OS caveat);
**the check suite** (the four commands, verbatim from preamble §5); **the reproducibility contract** (four
sentences: one seed, spawned streams, manifests only, results-block byte-stability — wave plan §7-S6);
**the workflow** (branch → PR → review per preamble §8 → auto-merge; who owns what per CODEOWNERS); pointers
to the governing docs (spec, preamble, index). CI badge at top.

### S7 — Preamble §5 ratification

A PR against the ticket set replacing preamble §5's "target, not the law" note with the ratified commands +
the `uv sync --frozen` setup line, and recording the O7–O9 rulings' locations. (Cross-repo change: it edits
the stakeholder's docs tree, so it rides the ticket-set's own review path.)

---

## 8. Observability

CI runs and the README badge are this ticket's entire observability surface — appropriate to its scope. The
first data-bearing artifact (the `dummy_smoke` manifest) arrives with W0-04, at which point future plans gain
something to cross-check against (the preamble §9 invocation's "uflogs" clause becomes live). Deliberately
absent, recorded so nobody adds them ad hoc: logging frameworks, run databases, coverage gates (O9), docs
sites. Each is a future ticket's loud decision if ever needed.

---

## 9. Sequenced implementation steps

1. **STEP 0** (§6): wave STEP-0 confirmed filled; O7–O9 ruled; versions captured; repo + branch protection
   live; empty-commit PR traverses CI + review + auto-merge end to end.
2. **S1 layout** — the tree, empty packages, .gitkeeps.
3. **S2 packaging** — pyproject exactly as specified (STEP-0 versions inserted); `uv lock` → committed
   `uv.lock`.
4. **S3/S4** — .gitignore with the commented load-bearing entries; CODEOWNERS with real handles.
5. **S5** — both workflows + PR template; branch protection settings applied per O8; auto-merge on.
6. **S6** — README.
7. **§10 tests** — land with their features (this list is the owed-sweep).
8. **S7** — the preamble §5 ratification PR (separate PR, ticket-set repo).
9. **Close-out** — preamble §6 checklist INCLUDING §8 review: this ticket's own close is the review rule's
   first live execution — the reviewer must not be whoever drove this implementation, and the index flip
   records `reviewed: <who/what>, <date>`.

---

## 10. Test plan (exact pins)

1. **Fresh-environment pin:** in CI (which IS a fresh environment every run): `uv sync --frozen` succeeds and
   the four check-suite commands pass — proving clone→green with no undocumented steps.
2. **Marker discipline:** a `slow`-marked dummy test is excluded by `-m "not slow"`, included by plain
   `pytest`; an UNREGISTERED mark fails the run (`--strict-markers` pin).
3. **Lockfile honesty:** CI uses `--frozen` — a pyproject/lock mismatch fails loud (assert by the workflow
   definition; exercised naturally on the first dependency PR).
4. **Version import pin:** `import wocbots; wocbots.__version__ == "0.1.0"`; all eight packages import.
5. **CODEOWNERS↔streams consistency:** a unit test parses CODEOWNERS and asserts its path→owner mapping
   matches a small checked-in table mirroring the index streams table — drift between the two is a test
   failure, not a surprise review request.
6. **Structural review proof (not pytest):** the close report links (a) one PR blocked on red CI, or the
   settings screen showing required checks, (b) one PR showing a non-author approval requirement, (c) the
   empty-commit PR that traversed the whole path.

---

## 11. Blast radius (forward commitments)

- **Every later ticket's DX:** the check suite, lockfile, and PR path defined here are consumed by all 41
  remaining tickets. Changing them later is an index-changelog event.
- **CODEOWNERS** encodes the streams table — re-deals must co-edit both (pinned by §10.5).
- **The PR template** operationalizes preamble §8 — if §8's rules evolve (e.g., the stakeholder tightens the
  AI-reviewer policy, §12-Q1), the template is the second edit site.
- **`--strict-markers` + no default filter** define what `pytest` MEANS for every close-out.
- **O9's no-gate coverage** is a standing decision future tickets may re-open at Q1 exit — with data.

---

## 12. Risks, alternatives, open questions FOR THE STAKEHOLDER

**Risks.**
- **R1 — GitHub Actions limits on a private repo** (Q3 ruling: private until publication, so the minutes
  quota is live). *Mitigation:* ubuntu-only, 2-Python matrix (modest burn); scheduled job weekly not daily;
  revisit at the public flip. Escalate only if the quota actually bites.
- **R2 — Branch-protection friction for a 5-person team** (review latency stalls parallel streams).
  *Mitigation:* auto-merge + CODEOWNERS routing + small tickets (the v1.4 re-cut exists for this); if latency
  still bites, the escape hatch is a team ruling relaxing O8 — recorded, not improvised.
- **R3 — uv unfamiliarity.** *Mitigation:* README one-liners; uv is one binary; fallback documented (`pip
  install -e .` works from the same pyproject for anyone stuck — but CI truth is uv+lockfile).
- **R4 — Windows-local breakage** (paths, shells) invisible to ubuntu CI. *Mitigation:* OS-agnostic tooling
  choices here; first Windows-specific failure triggers a team decision on adding a Windows CI job (cost vs
  the actual OS mix — decide with data, not upfront).

**Stakeholder questions — ✅ ALL RULED (2026-07-07):**
- **Q1 — AI-reviewer independence: RULED — different system required.** A fresh session of the same model is
  NOT independent. Preamble §8 stands as written; the PR template's attestation inherits it.
- **Q2 — Human-in-the-loop floor: RULED — pure AI→AI acceptable.** AI implements, a different AI reviews, a
  human adjudicates the reviewer's findings; no mandatory human full-diff read at ticket close. §8 stands as
  written.
- **Q3 — Repo visibility: RULED — PRIVATE until publication**, then flipped public at paper submission. This
  constrains the team's O1 ruling (they choose name/structure; visibility is fixed) and resolves R1
  conservatively: ubuntu-only matrix, watch the Actions minutes, revisit at the public flip.

---

## 13. Definition of Done (preamble §6, instantiated)

1. ☐ Check suite green locally AND both workflows green on the real repo.
2. ☐ Every §10 pin exists and passes; the structural review proofs linked.
3. ☐ STEP-0 RESULT filled (wave rulings cited; O7–O9 ruled named-and-dated; versions captured).
4. ☐ Preamble §5 ratified via the S7 PR; index W0-01 flipped `✅ (reviewed: <who/what>, <date>)` — the
   review rule's first live execution.
5. ☐ Close report lists every created path and links the CI runs and traversal PR.
6. ☐ This plan's DRAFT banner replaced with APPROVED (stakeholder, date) before step 2 of §9 began.

---

## STEP 0 — RESULT (fill before coding)

- Wave STEP-0 (O1–O6): ☐ filled at `W0-01_scaffold-experiment-harness_PLAN.md` (date: ____)
- O7 dependency locking: ☐ ____ (ruled by ____, date ____)
- O8 branch protection & merge policy: ☐ ____
- O9 coverage posture: ☐ ____
- Pinned versions (ruff / uv / CI Python patches): ☐ ____
- Repo + protection live; empty-commit PR traversed CI + review + auto-merge: ☐ (links: ____)
