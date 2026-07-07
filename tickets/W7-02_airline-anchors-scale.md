# W7-02 — Airline anchors, crowd configs, and the scale posture

**Wave:** W7. **Blocked by:** W7-01. **Blocks:** W7-04.
**Binding spec sections:** §5.1 (per-dataset anchor analysis), §9.3 ("many, many agents"), §4.4 (scale).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

Airline's crowd-side onboarding: the anchor analysis rerun (per-dataset, always), reference crowd configs
for a 22-feature space, and the runtime reality check — 120k samples × per-sample arenas is where naive
implementations die, and the posture toward that is decided HERE, with numbers, not discovered in W7-04's
grid.

## Grounding (read before starting)

- Spec §5.1, §9.3, §4.4's scale warning; W1-06's analysis pattern; the published mid-90s accuracy ballpark.

## Specification

- **S1.** Anchor analysis on the airline train split (W1-06 pattern, RESULT block below); reference crowd
  configs proposed in the mini-plan (the feature count supports a large crowd).
- **S2.** Scale posture: a profiled smoke run (~1k samples) with per-phase timing in the manifest; projected
  full-test-set runtime. If impractical: the spec-compliant levers are a documented, seeded test-subset
  protocol and targeted vectorization of hot paths behind unchanged seams. Changing method semantics for
  speed escalates.

## Forbidden shortcuts

- Skipping the profile and hoping; semantic shortcuts dressed as optimizations.

## Test requirements

1. Anchor smoke: seeded, artifact emitted, RESULT filled.
2. Smoke run (slow): 1k samples complete; agents clear pruning on real features; timings recorded.

## Acceptance criteria

- Anchors + crowd configs recorded; runtime posture documented with numbers and a chosen, named protocol.

---

## RESULT — airline anchor analysis (fill before closing)

- Feature ranking (top 6): ☐ ____
- Chosen anchor set: ☐ ____
- Crowd config(s) proposed: ☐ ____
