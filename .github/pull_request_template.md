<!-- Process: see docs/BRANCHING.md. Integration PRs target **develop** (not main). -->

## Ticket

- **ID:** W_-__
- **Issue:** Closes / Refs #__  (link)
- **Labels:** `W_-__` + short ticket name

## Target branch

- [ ] Base branch is **`develop`** (not `main`)

## Implementer(s)

Human: ____   AI session(s): ____

## Pre-merge checklist (implementer)

- [ ] Ticket plan (`*_PLAN.md`) reviewed/approved before implementation
- [ ] Closing report (`tickets/*_CLOSING-REPORT.md`) included in this PR
- [ ] `tickets/00_INDEX.md` updated (status + Blocked-by dependencies)
- [ ] DoD / acceptance criteria verified against the diff
- [ ] CI green (`checks (3.11)`, `checks (3.12)`)

## Reviewer attestation (non-author; for ticket-closing PRs: preamble §8 independence)

- [ ] I did not implement this work (didn't write it, didn't drive the AI session that wrote it)
- [ ] Read the full diff against the ticket/plan (not a summary)
- [ ] Forbidden-shortcut register (preamble §3) checked against the actual code
- [ ] Test pins exist and assert what the ticket says they assert
- [ ] (ticket-closing PRs) index status flip includes `reviewed: <who/what>, <date>`
