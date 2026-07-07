# W8-03 — The external-prediction agent and the privacy audit (meta-swarm mechanism)

**Wave:** W8. **Blocked by:** W6-03. **Blocks:** W8-04.
**Binding spec sections:** §1 (the privacy claim), §6.5 (the profile boundary), §2/§5.4 (initialization from
a validation statement).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The meta-swarm's mechanism: an agent whose "classifier" is an EXTERNAL model's prediction, participating in
interaction and swarm aggregation while the source model and its data stay private. If W2-01 kept the
classifier seam honest and W3-03 kept partner reads behind the profile, this ticket is small — its real size
is the audit of those boundaries, and the audited guarantees are a paper section.

## Grounding (read before starting)

- Spec §1's meta-swarm paragraph, §6.5's privacy note; W2-01's profile; W7-03's baselines (they become the
  external sources in W8-04).

## Specification

- **S1.** An `Agent` variant whose predict path calls an opaque `predict_fn(declared_features) → (class,
  score)`, and whose eval metrics (seeding certainty/trust/confidence per §2/§5.4) come from the source's OWN
  validation statement — a small typed manifest (accuracy/precision/recall on ITS eval data), never from
  access to its internals. Everything else — state, profile, interaction, voting, swarming — is stock.
- **S2.** The privacy audit as executable assertions: partners read only `public_profile()`; the external
  `predict_fn` receives only the current sample's declared features; no import path from the external module
  to other agents' training data. Plus one written paragraph stating the audited guarantees.

## Forbidden shortcuts

- Computing external eval metrics ourselves on data the source "shouldn't have" (the validation-statement
  discipline IS the claim's honesty). `isinstance(ExternalAgent)` special-casing outside the agents module.

## Test requirements

1. Stock participation: an external agent runs the full W4 lifecycle and W6 swarm with zero core changes
   (structural).
2. The audit assertions (S2), each as a test.
3. Init pin: a validation statement (0.85, 0.80, 0.75) seeds state exactly per §2/§5.4.

## Acceptance criteria

- External agents are first-class and privacy-audited; the guarantees paragraph is written.
