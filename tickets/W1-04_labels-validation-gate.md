# W1-04 — Labels, ground-truth validation, and the label reconciliation gate

**Wave:** W1. **Blocked by:** W1-02, W1-03. **Blocks:** W1-05.
**Binding spec sections:** §4.3 item 7 (the label + the known discrepancy), §4.2, §10.10.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full. **This ticket's gate escalates to the stakeholder
if it fires** (index v1.2 delegation does NOT cover it).

## Why this ticket exists (system meaning)

Every accuracy number in the project rides on the label, and the source material contains one known trap: the
ground-truth column named `made_more_than_2x_budget` is actually computed as "made back its budget at all"
(spec §4.3.7). This ticket computes both candidate labels, validates the whole pipeline row-level against
W1-02's reference, and rules — loudly — which label ships.

## Grounding (read before starting)

- Spec §4.3 item 7; `antevorta-db` `dbcreator/hollywood/TMDBMoviesPusher.kt` (`determinePerformanceClass` /
  `madeBackBudget` — read the computation, not the column name); W1-02's reference table.

## Specification

- **S1.** Row-level validation of W1-03's output against the reference: matched/dropped counts vs
  **4,722 / 1,023 / 3,699**; per-feature value agreement (documented tolerances). Deviations investigated and
  explained, not waved through.
- **S2.** Compute BOTH label variants: (a) `revenue > 2 × budget` (the spec's stated rule); (b) the reference
  `made_more_than_2x_budget` column. Record each variant's class balance; which matches the published
  **47.5 / 52.5**; disagreement row count.
- **S3.** THE GATE: the variant matching the published balance ships as THE label. If neither matches
  cleanly, or the shipped definition differs from the spec's stated rule → escalate to the stakeholder before
  closing. Fill the RESULT block.

## Forbidden shortcuts

- Trusting the column name over its computation; picking a label silently; eyeball-validation.

## Test requirements

1. Boundary pin: `revenue == 2 × budget` exactly → label 0 under variant (a).
2. Validation (slow): counts vs reference targets; label agreement vs the shipped variant ≥ 99% with
   disagreements enumerated.
3. Class-balance pin: shipped label within ±1 point of 47.5/52.5.

## Acceptance criteria

- Pipeline validated row-level; RESULT block filled; shipped label stated in the manifest and (if divergent
  from spec §4.3.7's stated rule) stakeholder-ratified. Downstream consumes only this labeled output.

---

## RESULT — label reconciliation (fill before closing)

- Variant (a) `revenue > 2×budget` balance: ☐ ____ / ____
- Variant (b) reference-column balance: ☐ ____ / ____
- Matches published 47.5/52.5: ☐ (a) ☐ (b) ☐ neither → escalated
- Disagreement rows: ☐ ____
- Shipped label: ☐ ____ — ratified by: ☐ ____ (date)
