# W0-01 — Package scaffold, check suite, and the config/seed/manifest experiment harness — IMPLEMENTATION PLAN

> **READ ME FIRST — about this document.** This is the format exemplar for every `_PLAN.md` in this project.
> A plan is what a ticket becomes when it is about to be executed: every decision either made and pinned, or
> explicitly routed to whoever holds ruling authority — the stakeholder by default; §3 here shows the
> delegated case — always with a recommended default attached. The test of a good plan: an implementer who
> follows §9 step by step and pins §10 exactly ships the ticket's *intent* — not merely its wording — without
> making a single silent decision along the way. If, while implementing, you find a decision this plan didn't
> make, that is a plan bug: stop, record it, get it ruled, fold it back in. Sections: §2 why, §3 decisions,
> §4 verified facts, §5 the path of data through the design, §6 pre-code gates, §7 the specification,
> §8 observability, §9 sequenced steps, §10 exact test pins, §11 blast radius, §12 risks & open items,
> §13 definition of done.

**Tickets:** RESCOPED (index v1.5) — this plan is now the execution document for **W0-02, W0-03, W0-04
only**. Mapping: §7-S2 → `W0-02_types-policy-seams.md`; §7-S3 (models) → `W0-03_config-manifest-models.md`;
§7-S3 (harness) + §7-S4 → `W0-04_harness-runner-rng-guard.md`. §10's pins distribute accordingly.
**W0-01 has its own dedicated plan** (`W0-01_repo-scaffold-ci_PLAN.md`), which supersedes this plan's §7-S1/
S5/S6 content where they differ; this plan's §3 rulings (O1–O6) and §6 STEP-0 remain shared across the wave. **Precedence:** the spec
(`docs/WoC-Bots_Implementation_Spec.md` v1.1) > this plan > the tickets. Where the plan and spec
disagree, the spec wins and the discrepancy is a plan bug — report it.
**Wave:** W0. **Blocked by:** —. **Blocks:** every other ticket in the set.
**Binding spec sections:** §11 (toolkit shape, policy seams), §9.1 (experiment protocol), §0 (MUST/SHOULD/MAY).
**Binding preamble sections:** §2 (hard rules — the one-RNG rule and manifest rule are THIS ticket's product),
§4 (test discipline), §5 (check suite — this ticket ratifies it).
**Severity of getting it wrong:** 🔴 foundational — every later ticket builds on these seams; a bad decision
here is a cross-project migration later.
**Ruling authority for §3 (O1–O6): DELEGATED TO THE TEAM** (stakeholder ruling, 2026-07-06). The team makes
the six calls, records them named-and-dated in the STEP-0 RESULT block, and they are binding from that point —
the same discipline as a stakeholder ruling, different signature. Recommended defaults are implementable as
written; none blocks starting once STEP 0 (§6) is answered.

---

## 1. Metadata (see header above)

This plan is self-contained: an implementer following §9 and pinning §10 satisfies W0-01's acceptance criteria
in full. It was written from full reads of the spec sections and preamble sections named above; there is no
prior code to verify against (§4 records the *grounding* facts instead — for greenfield tickets, "verified
live-tree facts" become "verified source-document facts," same discipline, same re-verify-before-coding rule).

---

## 2. Why this ticket exists (system meaning)

Reproducibility is a stated deliverable of this project and the thing the publications are weakest on. It is a
property of the *harness*, not of good intentions: if running an experiment outside the config/seed/manifest
path is possible, it will happen under deadline, and the number it produces will end up in the report with no
way to regenerate it. W0-01 makes the disciplined path the only path — one RNG threaded from config, one
manifest per invocation, a check suite that means the same thing in every later ticket — and it plants the five
policy seams (spec §11) so W2/W3/W4/W6 grow *into* interfaces instead of growing tangled and being refactored
apart later. Everything here is boring on purpose; the boring parts are load-bearing.

---

## 3. Ruled-by-the-team decisions (recommended defaults; fill each ruling into §6's RESULT block)

Ruling authority for this section is **delegated to the team** (see header). Each decision ships with a
recommended default that stands unless the team overrules it WITH a recorded rationale — "we didn't like it"
is not a rationale; "we know Actions better than the alternative" is. Per preamble §0.2, these are blocked
INPUTS, not blocked work — the structure that surrounds them lands regardless. Note the delegation is
per-section, not global: gates that name the stakeholder elsewhere in the set (W1-04's label reconciliation,
any MUST dispute per preamble §0.2) still escalate to him.

- **O1 — Repository identity.** The toolkit lives in the TEAM'S OWN repository (clean-room: it must be
  buildable and publishable with no reference to any stakeholder-private code). **Recommended:** a new
  repository named `wocbots`, `src/` layout, MIT-style permissive license placeholder pending O6.
  *Alternative:* a monorepo shared with course material — rejected by default: the "open, documented toolkit"
  deliverable wants a standalone artifact.
- **O2 — Python version.** **Recommended:** `requires-python = ">=3.11"`, CI matrix on 3.11 and 3.12.
  *Alternative:* 3.10 floor for older machines — costs modern typing syntax; not worth it.
- **O3 — Config & manifest modeling.** **Recommended:** pydantic v2 models, `frozen=True`,
  `extra="forbid"` everywhere (unknown keys are ERRORS, not warnings — a typo'd config field that silently
  no-ops is how experiments lie), YAML on disk via `yaml.safe_load`. *Alternative:* stdlib dataclasses + a
  hand-rolled strict loader — fewer dependencies, but re-implements validation pydantic gives for free, badly.
- **O4 — mypy strictness.** **Recommended:** `strict = true` in pyproject, with per-module relaxations only as
  named, commented exceptions. *Alternative:* default strictness — invites the gradual-typing rot that makes
  the type gate meaningless by W4.
- **O5 — CI platform & cadence.** **Recommended:** GitHub Actions; per-commit job = lint + format + mypy +
  `pytest -m "not slow"`; scheduled weekly job (+ manual dispatch) = full `pytest` including `slow` marks.
  The ticket-close gate remains the FULL suite run locally (preamble §5).
- **O6 — License. ✅ RULED BY FACT (stakeholder, 2026-07-07): MIT**, landed as `LICENSE` at the repo root.
  No team ruling needed; W0-01's license step becomes a verify.

**Encoding rule (post-ruling):** each ruling lands as one named line in §6's RESULT block and (where it changes
a file) a comment at the site: `# O3 ruling (team, <date>): pydantic v2, extra="forbid"`. A future re-ruling
changes that site only.

---

## 4. Verified grounding facts (re-verify these reads before coding)

- **Spec §11** prescribes the package layout (`data/ agents/ arena/ interaction/ aggregation/ experiments/
  evaluation/` + `tests/`) and the five policy protocols with these EXACT seams: `InitPolicy.place`,
  `MovementPolicy.move`, `InteractionPolicy.should_interact/truth/update_trust`,
  `ScoringPolicy.update_prediction`, `Aggregator.aggregate`. Signatures there are indicative; §7-S2 pins them.
- **Spec §9.1** requires: every reported number = mean ± std over 10 seeded runs; every experiment = config +
  seed + git SHA; one `numpy.random.Generator` "passed down from the experiment config."
- **Spec §9.1 / preamble §4** require determinism: same config + same seed → identical results. This plan
  interprets "identical" as byte-identical on the manifest's `results` block (provenance block excluded — it
  carries a timestamp by design). That interpretation is a plan ruling; it is testable and strict.
- **Preamble §5** names the four checks (`ruff check`, `ruff format --check`, `mypy src tests`, `pytest`) as
  a TARGET pending this ticket's ratification — updating that block is a deliverable here (§9 step 10).
- **Ticket W0-01 S3** requires manifests to carry: resolved config, seed(s), git SHA, package versions,
  per-run metrics, aggregate mean ± std, timestamped filename.
- **Greenfield fact:** there is no existing code; `antevorta-db` is NOT a dependency of this ticket (it enters
  at W1-01, and only as an external data producer — never as a package dependency).
- **Downstream facts this ticket must not contradict (IDs per the index v1.4 re-cut):** W2-01/W2-02 need the
  Generator threading and the classifier seam room; W3-01/W3-02 bind `InitPolicy`/`MovementPolicy`; W4-01
  binds the runner loop, W4-03/W6-02 bind `Aggregator`; W5-05 and W8-06 consume manifests as their provenance
  layer (figures regenerate from manifests by script).

---

## 5. Execution-path map (the life of one experiment)

```
experiment config (YAML on disk)
  └─ load + validate (pydantic, extra="forbid")          → ExperimentConfig (frozen)
       └─ resolve runner by config.kind from the registry → RunnerFn
            └─ SeedSequence(config.seed).spawn(config.n_runs)
                 └─ for each run i: rng_i = default_rng(child_i)
                      └─ RunnerFn(config, rng_i)          → {metric: float, ...}   (pure w.r.t. rng_i)
            └─ aggregate per-metric mean, std over runs
       └─ stamp provenance (UTC timestamp, git SHA(+dirty), package versions, platform)
  └─ write Manifest JSON → results/manifests/<name>_<UTCstamp>_<shortsha>.json
```

Two properties fall out of this shape and are pinned in §10: (1) the `results` block is a pure function of
(config, seed) — determinism is structural; (2) there is no side door — the runner registry is the only way
code executes under the harness, and the manifest writer is the only output path.

---

## 6. STEP 0 — pre-code gate (fill the RESULT block at the bottom of this file BEFORE coding)

Unlike a live-system ticket, there is no trace to pull; the gate here is the §3 ruling round. Procedure:

1. The team rules O1–O6 in one sitting (defaults + alternatives are all in §3; a decision meeting, not a
   research project — an hour is plenty). Each ruling gets a name and a date; overruled defaults get their
   rationale written down.
2. Confirm the repository exists and CI can run on it (an empty-commit workflow run counts).
3. Record both in the `## STEP 0 — RESULT` block. Only then start §9.

If any ruling overturns a default in a way that changes §7 (e.g., O3 → dataclasses), fold the change into this
plan FIRST, then implement the amended plan — never implement a plan that disagrees with its rulings.

---

## 7. Specification

### S1 — Repository and packaging

`src/` layout, exactly:

```
wocbots/
├── pyproject.toml
├── README.md                  # quickstart: setup, check suite, "run your first experiment"
├── LICENSE.pending            # O6
├── .gitignore                 # includes: data/raw/, results/manifests/*.json is COMMITTED (not ignored)
├── .github/workflows/
│   ├── ci.yml                 # per-commit: lint, format, mypy, pytest -m "not slow"  (O5)
│   └── scheduled.yml          # weekly + manual: full pytest including slow
├── src/wocbots/
│   ├── __init__.py            # __version__
│   ├── types.py               # Cell, Prediction, shared primitives
│   ├── protocols.py           # the five policy seams (S2)
│   ├── agents/__init__.py     # stub: class Agent (W2-01 owns; see S2 stub rule)
│   ├── arena/__init__.py      # stub: class Arena (W3-01 owns)
│   ├── interaction/__init__.py
│   ├── aggregation/__init__.py
│   ├── data/__init__.py
│   ├── evaluation/__init__.py
│   └── experiments/
│       ├── __init__.py
│       ├── config.py          # ExperimentConfig (S3)
│       ├── registry.py        # runner registry (S3)
│       ├── manifest.py        # Manifest models + writer (S3)
│       ├── provenance.py      # timestamp/git/versions capture — the ONLY wall-clock allowlist site (S4)
│       └── harness.py         # run_experiment() — the ONLY seed origin (S4)
├── configs/
│   └── dummy_smoke.yaml       # the S3 dummy-kind example config
├── results/manifests/         # committed manifests land here (.gitkeep)
└── tests/
    ├── unit/…                 # per-module tests incl. the guard tests (S4)
    └── integration/…          # slow-marked; empty placeholder + the harness round-trip
```

`pyproject.toml` pins (minimums; exact figures re-checked at implementation): `numpy>=1.26`, `pandas>=2.1`,
`scikit-learn>=1.4`, `pydantic>=2.6`, `pyyaml>=6.0`; dev: `pytest>=8`, `mypy>=1.8`, and **ruff pinned EXACT**
(e.g. `ruff==0.4.*` at the current release) — `ruff format` output drifts across minors and a floating pin
turns the format gate into noise. Tool config: `[tool.mypy] strict = true` (O4); `[tool.pytest.ini_options]
markers = ["slow: multi-minute integration runs"]` with NO default `-m` filter (the closeable gate is full
`pytest`; the fast subset is CI's per-commit choice, not the local default); ruff line length and rules stated
once here and never argued about again.

### S2 — Shared types and the five policy seams

`types.py`, exact:

```python
Cell = tuple[int, int]          # (row, col); the arena grid coordinate

class Prediction(BaseModel, frozen=True, extra="forbid"):
    class_label: Literal[0, 1]
    tier: str | None = None     # vote-margin tier (spec §7) / swarm band (spec §8.2); None until W4-04
    margin: float | None = None # winning vote share in [0,1]; None until W4-04
```

`protocols.py`, exact (all `@runtime_checkable`; docstrings cite owning spec sections):

```python
@runtime_checkable
class InitPolicy(Protocol):
    def place(self, agent: Agent, arena: Arena, rng: np.random.Generator) -> Cell: ...

@runtime_checkable
class MovementPolicy(Protocol):
    def move(self, agent: Agent, arena: Arena, rng: np.random.Generator) -> Cell: ...

@runtime_checkable
class InteractionPolicy(Protocol):
    def should_interact(self, a: Agent, b: Agent) -> bool: ...
    def truth(self, a: Agent, b: Agent) -> bool: ...
    def update_trust(self, a: Agent, b: Agent) -> None: ...

@runtime_checkable
class ScoringPolicy(Protocol):
    def update_prediction(self, agent: Agent, partner_profile: Mapping[str, object]) -> None: ...

@runtime_checkable
class Aggregator(Protocol):
    def aggregate(self, participants: Sequence[Agent], rng: np.random.Generator) -> Prediction: ...
```

**Stub rule:** `Agent` and `Arena` exist NOW as minimal stub classes (docstring naming the owning ticket;
every method body `raise NotImplementedError("W2-01 owns Agent")`). W2-01/W3-01 replace stub INTERNALS and may
TIGHTEN protocol parameter types; they may not rename seams or loosen types — that is a cross-ticket contract
change (§11). `partner_profile` stays a read-only `Mapping` on purpose: it is the spec §6.5 public-profile
boundary, and typing it as `Agent` would hand every scoring policy the whole agent — the exact hole the
boundary exists to close.

### S3 — The experiment harness

`config.py`, exact:

```python
class ExperimentConfig(BaseModel, frozen=True, extra="forbid"):
    name: str                     # manifest filename stem
    kind: str                     # registry key; W0-04 ships "dummy"
    seed: int                     # the ONE master seed
    n_runs: int = 10              # spec §9.1 default
    params: dict[str, JsonValue] = Field(default_factory=dict)  # kind-specific; the kind validates
```

`registry.py`: `RunnerFn = Callable[[ExperimentConfig, np.random.Generator], Mapping[str, float]]`;
`register_kind(key: str, runner: RunnerFn)` (duplicate key = error); `resolve_kind(key)` (unknown = error
listing registered keys). Registration happens at import of the defining module — kinds are code, not config.
Ships one kind: `"dummy"` (draws `params["n"]` (default 1000) standard-normal samples from ITS rng, reports
`{"mean": …, "std": …}`) — deliberately trivial, exists so the harness is testable before any real experiment.

`manifest.py`, exact:

```python
class RunResult(BaseModel, frozen=True, extra="forbid"):
    run_index: int
    metrics: dict[str, float]

class MetricSummary(BaseModel, frozen=True, extra="forbid"):
    mean: float
    std: float                    # population std over runs; documented, never silently changed

class Provenance(BaseModel, frozen=True, extra="forbid"):
    created_utc: str              # ISO-8601; the ONE licensed timestamp
    git_sha: str                  # `git rev-parse HEAD`; "+dirty" suffix iff `git status --porcelain` nonempty
    package_versions: dict[str, str]   # wocbots, numpy, pandas, sklearn, pydantic, python
    platform: str

class Manifest(BaseModel, frozen=True, extra="forbid"):
    schema_version: int = 1
    provenance: Provenance
    config: ExperimentConfig
    runs: list[RunResult]
    aggregate: dict[str, MetricSummary]
```

`harness.py`: `run_experiment(config: ExperimentConfig | Path) -> Path` implementing §5's map exactly. Seeds:
`np.random.SeedSequence(config.seed).spawn(config.n_runs)` → `default_rng(child)` per run — the numerically
correct way to get independent per-run streams from one master seed (naive `seed+i` produces correlated
streams; this is exactly the subtle wrongness the harness exists to make unthinkable). JSON written with
`sort_keys=True`, fixed float repr (Python's default `repr` — stable within a Python minor), UTF-8, trailing
newline. **Determinism contract:** `manifest.model_dump(exclude={"provenance"})` is byte-stable for a given
(config, code version).

### S4 — Structural enforcement of the one-RNG rule

A guard test (`tests/unit/test_rng_discipline.py`) AST-walks every file under `src/wocbots/` and FAILS on:

1. Any attribute call on `numpy.random`/`np.random` EXCEPT `default_rng` and `SeedSequence`, and those two
   only inside `experiments/harness.py` (the one seed origin).
2. `import random` / `from random import …` anywhere.
3. `datetime.now`, `datetime.utcnow`, `time.time` outside `experiments/provenance.py` (the one licensed
   wall-clock site — manifests' `created_utc`).

The allowlist is a named constant IN THE TEST with a comment per entry; growing it is a reviewed, deliberate
act. The guard is itself tested (§10.6): a fixture module containing each violation, parsed by the same
checker, must be flagged — a guard that can't catch a planted violation is decoration.

### S5 — Check suite ratification and CI

Pinned commands (these go into preamble §5 verbatim at close, replacing "the target, not the law"):

```bash
ruff check .
ruff format --check .
mypy src tests
pytest            # full suite, slow included — the ticket-close gate
```

CI (O5): `ci.yml` per-commit — the first three checks plus `pytest -m "not slow"`, matrix {3.11, 3.12};
`scheduled.yml` — full `pytest` weekly + `workflow_dispatch`. Badge in README.

### S6 — Developer documentation

README: setup (venv + editable install), the check suite, "run your first experiment" (`dummy_smoke.yaml` →
manifest walk-through, pointing at each manifest block and what it's for), and a REPRODUCIBILITY section
stating the contract in four sentences: one seed, spawned streams, manifests are the only results, the
`results` block regenerates byte-identically. The preamble and spec are linked as the governing documents.

---

## 8. Observability (what the harness records, and why that's enough)

The manifest IS the observability layer at this stage: per-run metrics + aggregate + provenance answer "what
ran, from what, and what came out" for every invocation. Two deliberate non-features, recorded so nobody adds
them ad hoc: no logging framework (print-level progress in the runner loop is fine; structured logging is a
future decision owned by whichever ticket first needs it), and no run database (manifest files in git are the
database; W8-06's provenance audit consumes them as such). If a later ticket outgrows either ruling, that is a
plan-level decision for that ticket, taken loudly.

---

## 9. Sequenced implementation steps

1. **STEP 0** (§6): O1–O6 rulings recorded; repo + CI stub live.
2. **S1 packaging:** pyproject (pins, tool config per O2–O4), layout tree, .gitignore, LICENSE per O6,
   README skeleton.
3. **S2 types + seams:** `types.py`, `protocols.py`, `Agent`/`Arena` stubs with owning-ticket docstrings.
4. **S3 config + registry:** `ExperimentConfig`, registry with duplicate/unknown-key errors, the `dummy` kind.
5. **S3 manifest models + writer:** exact schemas above; canonical JSON writer.
6. **S3 harness:** `run_experiment` per §5's map; SeedSequence spawning; aggregate computation.
7. **S4 guard test:** the AST checker + its planted-violation self-test.
8. **Remaining §10 tests** (land with their features throughout, per preamble §4 — this step is the sweep for
   anything owed).
9. **S5 CI:** both workflows green on the real repo; badge.
10. **Close-out:** preamble §5 block updated with the ratified commands (a PR against the ticket set); README
    reproducibility section final; `00_INDEX.md` status flip; close checklist per preamble §6.

---

## 10. Test plan (exact pins)

1. **Harness round-trip:** `dummy_smoke.yaml` (seed 42, n_runs 3, n=1000) → manifest exists, validates as
   `Manifest`, has 3 runs, aggregate carries `mean`/`std` for both metrics, filename matches
   `dummy_smoke_<UTC>_<sha>.json`.
2. **Determinism pin (the contract):** run twice, same config — `model_dump(exclude={"provenance"})` byte-equal
   after canonical JSON serialization. Then n_runs 3 vs first 3 of n_runs 5, same seed — identical `RunResult`s
   (proves per-run streams come from spawn order, not from run count).
3. **Independence sanity:** with seed 42, the 3 per-run `mean` values are pairwise distinct (spawned streams,
   not one reused stream).
4. **Strictness both-sides:** a config YAML with an unknown key → `ValidationError` naming the key; a valid
   config loads frozen (mutation raises).
5. **Registry:** duplicate `register_kind` → error; unknown `kind` → error listing registered keys.
6. **Guard self-test (S4):** planted-violation fixture module → each of the three violation classes flagged;
   the real `src/` tree → zero flags; `provenance.py`/`harness.py` allowlist entries covered by comments
   (asserted textually).
7. **Provenance:** `git_sha` matches `git rev-parse HEAD`; touch a tracked file → suffix `+dirty` appears
   (restore after); `package_versions` carries all six named packages.
8. **Protocol conformance:** a trivial fake per seam passes `isinstance` (runtime_checkable) and mypy strict;
   `Agent`/`Arena` stub methods raise `NotImplementedError` naming their owning ticket.
9. **Prediction model:** `class_label` outside {0,1} rejected; frozen; `extra="forbid"`.
10. **CI proof (not a pytest test):** links to one green per-commit run and one green scheduled/dispatch run
    in the close report.

---

## 11. Blast radius (forward commitments — who binds to what)

Greenfield inverts blast radius: nothing existing breaks, but every surface here is an API later tickets bind
to, so *changing it later* is the cross-ticket event. Enumerated:

- **`protocols.py` seams** → W3-01 (`InitPolicy`), W3-02 (`MovementPolicy`), W3-03 (`InteractionPolicy`,
  `ScoringPolicy`), W4-03/W6-02 (`Aggregator`). Tightening parameter types in the owning ticket: allowed.
  Renaming/loosening: a ruled, index-logged contract change.
- **`Mapping`-typed `partner_profile`** → the spec §6.5 privacy boundary; W3-03 and W8-03's audit both lean on
  it. Do not "convenience" it into `Agent`.
- **`ExperimentConfig.params` + the kind registry** → every experiment ticket (W2-04, W4-04, W5-*, W6-03,
  W7-*, W8-*) adds kinds; the registry error behavior is their debugging experience.
- **Manifest schema (`schema_version: 1`)** → W5-02..05's reproduction tables, W8-06's figure regeneration and
  provenance audit. Additive evolution bumps `schema_version`; removals/renames need a migration note in the
  index changelog.
- **SeedSequence spawning discipline** → W2-02 (sklearn seeding), W3-01 (arena RNG), W6-01 (wheel draws) all
  receive Generators descended from the config seed. Nothing else may mint randomness (S4 enforces).
- **The check suite** → preamble §5 verbatim; every later close gate.

---

## 12. Risks, alternatives considered, open items

**Risks.**
- **R1 — over-engineering the config layer** for needs we can't see yet. *Mitigation:* `params` stays an
  opaque, kind-validated dict; no speculative schema. The registry is 30 lines, not a plugin framework.
- **R2 — guard-test false positives** (e.g., a legitimate future wall-clock need). *Mitigation:* the named
  in-test allowlist with per-entry comments; growing it is a one-line reviewed change, not a workaround.
- **R3 — nondeterminism seeping in via libraries** (BLAS thread counts, sklearn `n_jobs`). Not exercised by
  the dummy kind; recorded here as a STANDING WARNING for W2-02: single-thread or explicitly-seeded paths in
  anything that feeds a manifest, and the determinism pin (§10.2 pattern) must be replicated in every
  experiment-bearing ticket.
- **R4 — float-repr instability across Python versions** breaking byte-compares. *Mitigation:* determinism is
  claimed per-Python-minor (CI runs the pin on both matrix versions independently); cross-version identity is
  explicitly NOT promised.
- **R5 — ruff format drift** (pinned exact, O-noted in pyproject comments; upgrading ruff is a deliberate
  chore that reformats the tree in its own commit).

**Alternatives considered.** Hydra/OmegaConf for configs (rejected: heavyweight, teaches the tool instead of
the discipline); storing manifests outside git with an index file (rejected: the git history IS the audit
trail at this scale); making the harness a CLI framework (deferred: `python -m wocbots.experiments.harness
configs/x.yaml` is enough until someone needs more).

**Open items.** O1–O6 (§3) → STEP-0 RESULT block. Nothing else.

---

## 13. Definition of Done (inherited from preamble §6, instantiated for this ticket)

1. ☐ Check suite green (all four, full pytest) locally AND both CI workflows green on the real repo.
2. ☐ Every §10 pin exists and passes; the guard self-test proves the guard.
3. ☐ STEP-0 RESULT block filled with all six rulings (named, dated).
4. ☐ Preamble §5 updated with the ratified commands; the closing ticket's `00_INDEX.md` status flipped ✅
   (this plan closes ticket-by-ticket: W0-02, W0-03, W0-04).
5. ☐ `dummy_smoke.yaml`'s manifest committed under `results/manifests/` as the harness's own first artifact.
6. ☐ Close report lists every created path project-root-relative and links the CI runs.
7. ☐ Commit discipline per team workflow (preamble §6.7).

---

## STEP 0 — RESULT (fill before coding)

- O1 repository: ☐ ____ (ruled by ____, date ____)
- O2 Python floor / CI matrix: ☐ ____
- O3 config modeling: ☐ ____
- O4 mypy strictness: ☐ ____
- O5 CI platform & cadence: ☐ ____
- O6 license: ☐ ____
- Repo live + empty CI run green: ☐ (link: ____)
