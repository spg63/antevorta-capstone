# W8-06 — The technical report / paper foundation (accretes from W5-05 onward)

**Wave:** W8. **Blocked by:** W5-05 (its Q1 report is the seed); consumes W6-03, W7-04/06, W8-02/04/05 as
they land. **Blocks:** — (the last deliverable).
**Binding spec sections:** §12 (the deliverable), §9.1 (provenance discipline); the proposal's Deliverables.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The proposal's final deliverable is a written report structured to found a publication, students as
co-authors. Reports assembled in the last two weeks are bad; this ticket makes the report a living artifact
every results ticket feeds ON CLOSE, so writing quality and result quality get debugged together.

## Grounding (read before starting)

- The proposal's Deliverables; spec §12; every results manifest.

## Specification

- **S1.** Skeleton (lands with W5-05): Introduction/Background (the team's own understanding, not paraphrased
  spec), Method (as built, including every recorded ruling and deviation — W1-04's label RESULT, the anchor
  RESULTs, ratified MAY choices), Experiments (one subsection per results ticket), Discussion, Limitations,
  Future Work. Version-controlled beside the code; format (Markdown/LaTeX) ruled once by the team.
- **S2.** The accretion rule: every results ticket (W5-02/03/04, W6-03, W7-04/06, W8-02/04/05) adds its
  subsection — protocol, table/figure, finding, manifest reference — in ITS close checklist. This ticket owns
  the skeleton, connective prose, editorial consistency, and the figures pipeline (plots regenerate from
  manifests by script; never hand-edited).
- **S3.** The provenance appendix: auto-generated — every number/figure → its manifest (config, seed, SHA).
  The report makes no claim the appendix can't back.

## Forbidden shortcuts

- Prose describing results that differ from current manifests; hand-tweaked figures; writing deferred to
  "after the experiments."

## Test requirements

1. Figures regenerate: one script rebuilds every figure from manifests; scheduled CI runs it and fails on
   drift.
2. Provenance audit: numeric claim markers cross-checked against the appendix (extends the W5-05 audit).
3. Per-results-ticket subsections present, checked at each such ticket's close.

## Acceptance criteria

- From Q1 exit onward, the report could be handed to the stakeholder at any moment as an honest statement of
  what the project has shown — culminating submission-ready when W8's experiments land.
