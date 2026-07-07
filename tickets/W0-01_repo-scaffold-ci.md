# W0-01 — Repository scaffold, packaging, check-suite ratification, CI

> **AMENDED (index v1.6; visibility re-ruled at v1.9):** the repository now EXISTS — `antevorta-capstone`,
> stakeholder-provided, **PUBLIC** — with the bare directory skeleton, a seed `.gitignore`, and the README
> pre-laid. That
> pre-does part of S1; this ticket's remaining scope is packaging (pyproject + lockfile), tool configs,
> check-suite ratification, CODEOWNERS, the PR template, branch protection, and CI. The dedicated plan's
> §7-S1 tree is now a verify-against-reality step, and its `.gitignore` spec (§7-S3) refines the seed file.

**Wave:** W0. **Blocked by:** —. **Blocks:** W0-02, W0-03, and everything after.
**Binding spec sections:** §11 (layout). **Formal plan:** `W0-01_scaffold-experiment-harness_PLAN.md` §7-S1,
S5, S6 (the plan covers all of W0; its STEP-0 rulings O1–O6 gate THIS ticket).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

"Green" must mean the same thing in every later ticket, from day one. This ticket is the repo, the toolchain,
and the ratified check suite — nothing else. No wocbots logic lands here.

## Grounding (read before starting)

- The plan §3 (rulings — delegated to the team), §7-S1 (exact tree + pyproject pins), §7-S5 (CI), §7-S6
  (README/docs).

## Specification

- **S1.** The plan §7-S1 layout: pyproject (pins incl. EXACT ruff pin, mypy strict per O4, pytest `slow`
  marker, no default marker filter), `src/wocbots/` package dirs (empty `__init__.py`s), `configs/`,
  `results/manifests/.gitkeep`, `.gitignore` (raw data out; manifests IN), LICENSE per O6, README skeleton.
- **S2.** Ratify the check suite: `ruff check .` / `ruff format --check .` / `mypy src tests` / `pytest`;
  update preamble §5 with the ratified commands (that update is a deliverable of this ticket).
- **S3.** CI per O5: per-commit workflow (lint, format, mypy, `pytest -m "not slow"`, matrix per O2) +
  scheduled/dispatch workflow (full pytest). Badge in README.

## Forbidden shortcuts

- Any wocbots logic, types, or seams (W0-02's job) sneaking in "while we're here."
- Floating ruff version; deferring CI "until there's more code."

## Test requirements

1. Fresh clone → documented setup → all four checks green locally (trivially, on the empty package).
2. CI proof: one green per-commit run + one green scheduled/dispatch run linked in the close report.
3. Marker config: a dummy `slow`-marked test is excluded by `-m "not slow"` and included by plain `pytest`.

## Acceptance criteria

- Repo live, toolchain pinned, CI green, preamble §5 ratified, STEP-0 RESULT block (in the plan) filled.
