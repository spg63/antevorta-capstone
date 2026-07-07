# W5-05 — The Q1 report and exit audit (Q1 EXIT)

**Wave:** W5. **Blocked by:** W2-04, W5-02, W5-03, W5-04. **Blocks:** W8-01, W8-06.
**Binding spec sections:** §12 (Q1 exit criterion), §9.1 (provenance discipline), §10.10.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The moment the toolkit is shown to BE WoC-Bots rather than something WoC-Bots-shaped — and the seed of the
final report (W8-06). Assembly and audit only: every reproduced table/figure beside its published
counterpart, every number tracing to a manifest, every deviation explained.

## Grounding (read before starting)

- All Q1 results manifests (W2-04, W5-02/03/04); spec §12's Q1 exit criterion.

## Specification

- **S1.** The Q1 report (version-controlled; the W8-06 skeleton's first real content): agent table, matched
  comparison curves, robustness contrasts, scaling result — published vs reproduced, with deltas and prose
  explanations of any deviation.
- **S2.** The exit audit: a script cross-checking that every number in the report traces to a manifest
  (config + seed + SHA), and that the spec §12 exit criterion — "the §9.2 reference results regenerate from
  configs" — holds by actually re-running the regeneration.

## Forbidden shortcuts

- Prose describing results that differ from current manifests; hand-assembled figures (plots regenerate by
  script).

## Test requirements

1. The audit script passes: zero untraced numbers.
2. Regeneration proof (slow): the report's figures rebuild from manifests byte-stably.

## Acceptance criteria

- The Q1 report exists and is audit-clean. **This ticket ✅ = Q1 exit (spec §12).** Persistent out-of-band
  results are escalated with manifests — the exit is honest or it isn't an exit.
