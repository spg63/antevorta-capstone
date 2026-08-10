# Branching and merge policy

This repo uses a **two-branch integration model** during the capstone quarter:

| Branch | Role |
|--------|------|
| **`develop`** | Integration branch — all ticket PRs merge here after review |
| **`main`** | Release / quarter-end snapshot — updated when `develop` is promoted (end of quarter) |

**Do not push directly to `main` or `develop`.** All changes land via pull request.

## Workflow (every ticket)

1. **Plan first** — write or read the ticket's `*_PLAN.md`; get it reviewed/approved before coding (preamble §9).
2. **Branch** — create a feature branch from `develop`:
   ```bash
   git fetch origin
   git checkout develop
   git pull origin develop
   git checkout -b <your-name>/<ticket-id>-short-description
   ```
3. **Implement + test** — check suite green locally (`uv run ruff check .`, `ruff format --check .`, `mypy src tests`, `pytest -m "not slow"` minimum).
4. **Open PR** — base branch **`develop`** (not `main`).
   - Use [`.github/pull_request_template.md`](../.github/pull_request_template.md) (fill every section).
   - **Label** with ticket ID and title (e.g. `W4-04 tiers-mechanism-comparison`).
   - **Link** the GitHub issue in the PR description (`Closes #N` or `Refs #N`).
5. **Before merge (implementer checklist):**
   - [ ] Closing report written (`tickets/<ticket>_CLOSING-REPORT.md`)
   - [ ] `tickets/00_INDEX.md` updated — status + dependency "Blocked by" columns for your ticket and downstream tickets
   - [ ] Definition of Done checked (ticket acceptance criteria + preamble §8 independent review)
   - [ ] CI green on the PR
6. **Merge** — squash or merge commit per team preference; **only after human confirmation and review sign-off**.

## Branch protection (repo admin — required)

Direct pushes to `main` and `develop` must be **disabled** in GitHub settings. Only repository **admins** can configure this.

**Settings → Branches → Branch protection rules** (add one rule per branch: `main`, `develop`):

- Require a pull request before merging
- Require approvals: **1** (or team policy)
- Require status checks: `checks (3.11)` and `checks (3.12)` (CI workflow)
- Do not allow bypassing the above settings (including administrators)
- Restrict who can push to matching branches (optional: no one pushes directly; everyone uses PRs)
- Block force pushes

If the GitHub UI shows **Rulesets** instead of classic rules, create equivalent rules for both branches.

> **Why this matters:** This is a public capstone repo. Protected branches keep history tidy and ensure every change has a PR, CI run, and review trail — suitable for CV/resume links.

## PR template visibility

The PR template lives at `.github/pull_request_template.md`. GitHub auto-fills it for PRs **into the default branch** (`main`). Until `develop` is merged to `main` at quarter-end, PRs into `develop` may not auto-load the template — **copy the template body manually** when opening the PR.

## Related documents

- `tickets/01_MANDATORY_PREAMBLE.md` — binding process (§8 review, forbidden shortcuts)
- `tickets/00_INDEX.md` — ticket map and status legend
- `README.md` — setup and check suite
