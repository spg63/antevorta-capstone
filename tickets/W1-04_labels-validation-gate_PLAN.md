# W1-04 — Labels and reconciliation gate — IMPLEMENTATION PLAN

**Status: APPROVED for implementation by the session driver, 2026-10-25.**  
**Session mode:** PLAN.  
**Ticket:** `W1-04_labels-validation-gate.md`.

## 1. Metadata

The DATA stream owns this work. W1-02 and W1-03 are marked complete in the index;
W1-05 depends on this ticket. Changes in another stream's directory require review
by that stream's owner. The mandatory preamble and ticket remain binding.

## 2. Why this ticket exists

The target label underlies every downstream accuracy measurement. The ticket requires
the stated 2× rule to be compared with the reference computation and requires a
stakeholder decision if its reconciliation gate fires.

## 3. Decisions

- The user's proposed shipped label is `1` when revenue is strictly greater than
  twice budget and `0` otherwise, including equality, as specified in §4.3.7.
- The reference-derived candidate is for reconciliation; computing it does not
  authorize it as the shipped label.
- The session driver also directed that the computed SQLite `movies` table persist
  the selected label in a `label` column. A repeatable W1-04 step runs after the
  feature-only database build and feature extraction remains label-free.
- After the measured gate failed, the session driver explicitly waived the
  published-balance requirement on 2026-10-25. Stakeholder acceptance remains to be
  confirmed before closure.
- The session driver directed that the reference's exact-5× fall-through be treated
  as a bug, not reproduced. The 1.5× comparison corrects it and is therefore not an
  exact reproduction of the reference column.

## 4. Verified grounding facts

- `variant_a_label` already implements the strict 2× comparison; focused tests pin
  both sides and equality.
- The current reference helper extracts a precomputed column; it does not compute
  the reference candidate. The ticket's RESULT block is empty despite comments in
  code and tests claiming it contains a waiver.
- In the preceding review, the user supplied the location of `antevorta-db`, and the
  active Kotlin computation was inspected. For positive budgets it gives binary 1
  above 1.5× except at exactly 5×, which falls through to performance class -1 and
  yields binary 0. This differs from the ticket and spec's description of the
  reference. This session's kickoff forbids reading outside the repository; the
  earlier inspection is the basis for this observation.
- Spec §4.2 does not require executing `antevorta-db` or validating against its
  database output. The ticket requires computing both variants from available code.

## 5. Execution-path map

W1-03 produces cleaned features including budget and revenue. Reconciliation computes
both candidate labels on the same rows and records balances and disagreements. The
selected label feeds the existing Hollywood experiment loader and split path. A
manifest and the ticket RESULT record the definition and gate decision.

## 6. Pre-code gates

- Plan approval and the session driver's ruling on the exact-5× fall-through are
  recorded above. Report the discrepancy in §4 and the resulting corrected comparison
  to the stakeholder.
- Confirm the intended full-data input and its provenance without copying raw data
  into context or the repository. Do not require executing `antevorta-db`.
- If the measured gate selects variant (b) or neither variant matches cleanly,
  request stakeholder adjudication before ticket closure; do not infer a waiver.

## 7. Specification

1. Retain `variant_a_label(df, budget_col="budget", revenue_col="revenue")`.
2. Add a reference-computation function taking the same columns and returning an
   index-aligned binary Series, subject to the §6 ruling. Preserve the reference's
   relevant edge cases, and distinguish comparison from independent validation.
3. Add a reconciliation function that calculates candidate labels on identical
   rows and returns row count, class counts and percentages, disagreement count,
   and match status against the ticket's tolerance. Define and test empty and invalid
   input handling; do not impute.
4. Add a reproducible runner under `scripts/` using the W1-03 output, recording
   provenance and results in a manifest. Preserve the full precision needed to
   assess the ±1 percentage-point boundary; round only for display.
5. Ensure downstream paths use the chosen label consistently and correct misleading
   assertions of prior ratification. No reference candidate should become a feature.

## 8. Observability

The reconciliation manifest records input identity, row count, definitions, class
counts and percentages for both variants, disagreements, match outcome, proposed
shipped label, and any stakeholder decision. Include configuration, seed where
applicable, and git SHA under the repository's manifest rules. Populate the ticket's
RESULT block from measured evidence, with a named and dated ruling where required.

## 9. Sequenced implementation steps

1. Resolve §6 gates and obtain plan approval.
2. Implement the reference candidate and reconciliation in
   `src/wocbots/data/labels.py`; adjust exports in `src/wocbots/data/__init__.py`
   if needed.
3. Add the runner and manifest output; use the existing data pipeline and manifest
   conventions after inspecting their relevant execution paths in full.
4. Add tests in `tests/unit/data/test_labels.py` and runner/integration tests as
   appropriate. Verify downstream consumers, including
   `src/wocbots/experiments/hollywood_data.py` and `scripts/build_w1_05_splits.py`.
5. Run a fixture smoke test, then reconciliation on the identified full dataset.
   Record the actual gate outcome and escalate if required.
6. Run the required checks, obtain independent review, and update the ticket,
   index, manifest and handoff as applicable. Humans commit unless explicitly
   authorized otherwise.

## 10. Test plan

- Variant (a): below, at, and above 2× produce 0, 0, and 1.
- Variant (b): pin both sides and equality at 1.5× and 5×, including the exact-5×
  fall-through if confirmed; cover any relevant missing-data behavior.
- Reconciliation: hand-computed counts, percentages, disagreements and aligned
  rows; empty and invalid inputs; both single-class outcomes.
- Gate: match and non-match cases on both sides of the ±1 percentage-point boundary,
  including cases requiring escalation.
- Integration: confirm downstream output uses variant (a) and excludes the
  comparison label from features.
- Full dataset: assert the ticket's published-balance requirement on the identified
  dataset. If it fails, retain and report the failure and escalate; do not replace it
  with a different balance pin or treat a skipped check as a pass.
- Run `ruff check .`, `ruff format --check .`, `mypy src tests`, and `pytest`.

## 11. Blast radius

The data labeling module and its tests are primary. The runner, manifest, ticket,
and potentially downstream experiment and split paths are affected. Coordinate
CORE-owned changes with its owner. Existing results based on the current label may
need reassessment if measured inputs or gate decisions differ.

## 12. Risks and open items

- The ticket's description of the reference conflicts with the previously inspected
  code. The corrected comparison is not exact reference-column reproduction.
- The existing test claims a 43.93/56.07 snapshot; that claim is not independently
  verified in this plan and would fall outside the ticket's published-balance gate.
- The session driver waived the failed balance requirement; confirm stakeholder
  acceptance before closure.
- Full dataset availability, provenance, and manifest output location must be checked
  before the reconciliation run. Do not commit raw data.

## 13. Definition of done

Both variants and disagreement are measured; the gate and stakeholder rulings are
recorded; the selected label is documented in the manifest and used downstream;
required tests and checks pass or unresolved failures are reported; independent
review is signed off; and ticket, index, and handoff bookkeeping satisfy preamble
§6. No status flip is made before those requirements are met.
