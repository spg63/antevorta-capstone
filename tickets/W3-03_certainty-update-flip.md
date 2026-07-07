# W3-03 — The interaction kernel: certainty update and prediction flip

**Wave:** W3. **Blocked by:** W2-01 (public profiles), W3-02 (encounters). **Blocks:** W3-04, W4-01, W6-02.
**Binding spec sections:** §6.5 (the equations, worked example, clamp and symmetry rulings — normative to
the letter), §10.1.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

This is the social mechanism's kernel — how evidence held by well-trained agents propagates and flips weak
opinions. Every equation is specified exactly with a hand-worked example; the job is faithful, pinned
implementation, not interpretation. Isolated in its own ticket because it is the single most
consequences-per-line piece of math in the project.

## Grounding (read before starting)

- Spec §6.5 in full: the equations, the worked example, the [0.01, 0.99] clamp ruling, the compute-then-apply
  symmetry ruling.

## Specification

- **S1.** Receiving side, per §6.5: `acceptance = 1 − certainty`; `influence = b.confidence × acceptance ×
  (b.trust_score × b.certainty)`; `corrected = influence × b.prior_performance`, negated on disagreement;
  `certainty = clamp(certainty + corrected, 0.01, 0.99)`; flip when `< 0.50` with `certainty = 1 − certainty`.
- **S2.** Both directions per encounter, COMPUTE-THEN-APPLY (both deltas from pre-update state). All partner
  reads through `public_profile()` — no reaching into the other agent.
- **S3.** Implemented behind the `ScoringPolicy`/`InteractionPolicy` seams; consumes W3-02's encounter log
  entries. Trust updating is a no-op stub here — W3-04 owns it.

## Forbidden shortcuts

- Sequential-apply within an encounter; unclamped certainty (spec §10.1); bypassing the profile boundary.

## Test requirements

1. **The §6.5 worked-example pin (mandatory):** a(cert 0.62, pred 1) meets b(pred 0, conf 0.71, trust 0.78,
   cert 0.80, priorPerf 1.1) → corrected = −0.18480 (1e-5); a flips to 0 with certainty 0.565 (1e-9).
2. Agreement mirror: same numbers, same predictions → 0.80480, no flip.
3. Flip boundary both-sides: post-update 0.499 → flip (→ 0.501); 0.501 → no flip.
4. Clamp: ten consecutive agreeers pin certainty at 0.99; acceptance never reaches 0.
5. Symmetry: swap encounter processing order → byte-identical outcomes.

## Acceptance criteria

- Every §6.5 equation under its spec name, pinned; the worked example is a permanent regression test.
