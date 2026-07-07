# W1-06 — Feature-correlation anchor analysis

**Wave:** W1. **Blocked by:** W1-05. **Blocks:** W2-03 (crowd configs read the RESULT).
**Binding spec sections:** §5.1 (anchor features), §9.2 (the feature sets the analysis should explain).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The anchor set is the crowd's shared knowledge base (spec §5.1) and must be a principled, recorded choice —
run once per dataset, configuration ever after. Pure analysis: small ticket, one RESULT block, no toolkit
code paths.

## Grounding (read before starting)

- Spec §5.1, §9.2; W1-05's train split (the analysis runs on training data only).

## Specification

- **S1.** Rank features by association with the label: point-biserial correlation and first-component PCA
  loadings, seeded, train split only. Deliverable: a small script/notebook + the written ranking.
- **S2.** Verify (not assume) the expectation: `budget` and `vote_count` top the list. Choose the anchor set
  (1–4 features per spec §5.1); fill the RESULT block. The set becomes config consumed by W2-03.

## Forbidden shortcuts

- Ranking on anything but the train split; hard-coding anchors without the analysis artifact existing.

## Test requirements

1. Analysis smoke: runs seeded, emits the artifact, `budget` present in the top set.
2. The RESULT block filled before close (preamble §6.5).

## Acceptance criteria

- Ranking artifact + RESULT block; anchor set stated as configuration. W1 wave complete.

---

## RESULT — anchor analysis (fill before closing)

- Feature ranking (top 6, with scores): ☐ ____
- Chosen anchor set: ☐ ____
- Matches §9.2 expectations: ☐ yes ☐ no → escalated
