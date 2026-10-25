# W1-04 — Labels, ground-truth validation, and the label reconciliation gate

**Wave:** W1. **Blocked by:** W1-02, W1-03. **Blocks:** W1-05.
**Binding spec sections:** §4.3 item 7 (the label + the known discrepancy), §4.2, §10.10.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full. **This ticket's gate escalates to the stakeholder
if it fires** (index v1.2 delegation does NOT cover it).

## Why this ticket exists (system meaning)

Every accuracy number in the project rides on the label, and the source material contains one known trap: the
ground-truth column named `made_more_than_2x_budget` is actually computed as "made back its budget at all"
(spec §4.3.7). This ticket computes both candidate labels using the available code as a reference and rules
— loudly — which label ships.

## Grounding (read before starting)

- Spec §4.3 item 7; `antevorta-db` `dbcreator/hollywood/TMDBMoviesPusher.kt` (`determinePerformanceClass` /
  `madeBackBudget` — read the computation, not the column name). Inspect the code; do not require executing it.

## Specification

- **S2.** Compute BOTH label variants: (a) `revenue > 2 × budget` (the spec's stated rule); (b) the reference
  `made_more_than_2x_budget` computation as understood from the code. Record each variant's class balance;
  which matches the published **47.5 / 52.5**; disagreement row count.
- **S3.** THE GATE: the variant matching the published balance ships as THE label. If neither matches
  cleanly, or the shipped definition differs from the spec's stated rule → escalate to the stakeholder before
  closing. Fill the RESULT block.

## Forbidden shortcuts

- Trusting the column name over its computation; picking a label silently; eyeballing the class balance.

## Test requirements

1. Boundary pin: `revenue == 2 × budget` exactly → label 0 under variant (a).
2. Class-balance pin: shipped label within ±1 point of 47.5/52.5.

## Acceptance criteria

- RESULT block filled; shipped label stated in the manifest and (if divergent
  from spec §4.3.7's stated rule) stakeholder-ratified. Downstream consumes only this labeled output.

---

## RESULT — label reconciliation (fill before closing)

- Variant (a) `revenue > 2×budget` balance: ☐ ____ / ____
- Variant (b) reference-computation balance: ☐ ____ / ____
- Matches published 47.5/52.5: ☐ (a) ☐ (b) ☐ neither → escalated
- Disagreement rows: ☐ ____
- Shipped label: ☐ ____ — ratified by: ☐ ____ (date)
