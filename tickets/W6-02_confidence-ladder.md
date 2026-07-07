# W6-02 — The confidence ladder: schedule, group interactions, fallback

**Wave:** W6. **Blocked by:** W6-01, W3-03 (group interactions reuse the kernel). **Blocks:** W6-03, W8-03,
W8-05.
**Binding spec sections:** §8.2 (the ladder — normative, incl. the Very-High MUST), §8.1 (between-round
interactions), §10.8.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The method's most distinctive output: a confidence LABEL earned by how hard consensus was to reach. The
Very-High rule — achievable ONLY on the first vote, before any swarm-phase interaction — is the purity that
bought 100% accuracy in that band; it is a MUST. Mechanism only; the variance study is W6-03.

## Grounding (read before starting)

- Spec §8.2 in full: schedule, fallback mechanics, thresholds-as-configuration; §8.1's between-round
  interaction rule.

## Specification

- **S1.** A `HoneybeeSwarm` Aggregator: round 1 agreement = 100% → Very High, stop; rounds 2–101 ≥ 90% →
  High; rounds 102–151 ≥ 75% → Medium; else certainty-weighted vote of ALL agents (`score_c = Σ certainty`;
  tie → class 1) → Low. Thresholds (100/90/75) and budgets (1/100/50) are named config with these defaults.
  N < 10 → route to the W4-02 degenerate/voting posture, flagged (spec §10.8).
- **S2.** Between failed votes: within each presenter's group, every watcher interacts with each co-watcher
  and the presenter — W3-03's kernel minus the spatial part — then a fresh W6-01 round. Certainty evolution
  lands in the swarm trace (W6-03 and W8-05 read it).

## Forbidden shortcuts

- Very High reachable after round 1, or "softened" because it captures few samples (its near-empty coverage
  on some datasets is a published finding). Hard-coded thresholds.

## Test requirements

1. Schedule pins via scripted round sequences: agreement 1.0 @ round 1 → VH; 0.92 @ 50 → High; 0.80 @ 120 →
   Medium; never-met → Low; round boundaries 101/151 both-sides.
2. VH purity: agreement 1.0 at round 2 → High, NOT Very High.
3. Fallback pin: hand-built certainties → hand-computed scores; tie → class 1.
4. Group interactions: 1 presenter + 10 watchers → each watcher performs exactly 10 interactions, counted;
   certainty moves per W3-03 pins.

## Acceptance criteria

- The ladder matches §8.2 exactly, knobs config-exposed, swarm trace recorded; check suite green.
