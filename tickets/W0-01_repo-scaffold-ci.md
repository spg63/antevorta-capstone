# W0-01 — Repository scaffold, packaging, check-suite ratification, CI

> **AMENDED (index v1.6; visibility re-ruled at v1.9):** the repository now EXISTS — `antevorta-capstone`,
> stakeholder-provided, **PUBLIC** — with the bare directory skeleton, a seed `.gitignore`, and the README
> pre-laid. That
> pre-does part of S1; this ticket's remaining scope is packaging (pyproject + lockfile), tool configs,
> check-suite ratification, CODEOWNERS, the PR template, branch protection, and CI. The dedicated plan's
> §7-S1 tree is now a verify-against-reality step, and its `.gitignore` spec (§7-S3) refines the seed file.

**Wave:** W0. **Blocked by:** —. **Blocks:** W0-02, W0-03, and everything after.
**Binding spec sections:** §11 (layout). **Formal plan:** `W0-01_repo-scaffold-ci_PLAN.md` — the dedicated,
APPROVED plan for this ticket (review fix 2026-07-07: this line previously mis-pointed at the wave plan). The
wave plan (`W0-WAVE_scaffold-experiment-harness_PLAN.md`) is cited ONLY for the shared O1–O6 rulings and wave
STEP-0; its implementation content covers W0-02..04, not this ticket.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

"Green" must mean the same thing in every later ticket, from day one. This ticket is the repo, the toolchain,
and the ratified check suite — nothing else. No wocbots logic lands here.

## Grounding (read before starting)

- The DEDICATED plan (`W0-01_repo-scaffold-ci_PLAN.md`) in full — its §3 (O7–O9 rulings), §7-S1..S7 (the
  exact specification), §9 (sequence), §10 (pins). The wave plan's §3/§6 only for the shared O1–O6 rulings.

## Specification

- **S1.** The dedicated plan §7-S1/S2/S3 layout + packaging: pyproject (pins incl. EXACT ruff pin, mypy
  strict per O4, pytest `slow` marker, no default marker filter), lockfile per O7, package `__init__.py`s,
  `.gitignore` refined per §7-S3 (raw data out; manifests IN), LICENSE (landed — verify), README per §7-S6.
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
