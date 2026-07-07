# W1-03 — Hollywood ETL: join, clean, and feature transforms (labels excluded)

**Wave:** W1. **Blocked by:** W1-01. **Blocks:** W1-04.
**Binding spec sections:** §4.3 items 1–6 (normative preparation rules).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

Path B's transform half: raw files → one tidy feature dataframe. Labels are deliberately NOT here — they are
W1-04's job, where the reconciliation gate lives — so a labeling mistake can't hide inside a 500-line ETL
diff.

## Grounding (read before starting)

- Spec §4.3 items 1–6, each rule normative: links-join (keep both-dataset movies only); drop budget ≤ 0,
  revenue ≤ 0, missing features (zeros are missing-coded, not "free movies"); ML ratings ×2; per-movie ML
  aggregates; combined `vote_count` (sum) and `vote_average` (count-weighted mean); genre intersection
  (optional feature).

## Specification

- **S1.** `wocbots.data.hollywood`: a pure, testable pipeline implementing rules 1–6. Output: one row per
  usable movie, feature columns + provenance ids (tmdbId, mlId) + raw `revenue`/`budget` retained for W1-04's
  labeling. No label columns.
- **S2.** Pipeline stage boundaries visible (join / clean / transform as separate functions) so each rule is
  unit-testable in isolation on the W1-01 fixtures.

## Forbidden shortcuts

- TMDb-only vote columns masquerading as the combined `vote_average`/`vote_count`.
- Labeling logic "just to see" — W1-04 owns it, gate and all.

## Test requirements

1. Per-rule unit tests on fixtures: join keys; each drop condition (including revenue == 0); the ×2 scaling;
   the count-weighted average with a hand-computed pin; genre intersection.
2. Full-pipeline row count (slow, needs real data) recorded in the manifest — compared against W1-02's
   reference in W1-04, but the raw number lands here.

## Acceptance criteria

- Rules 1–6 implemented as a pure pipeline with per-rule tests; output dataframe versioned for W1-04.
