# W4-02 — Ground-truth feedback, prior-performance mapping, and the degenerate-crowd rule

**Wave:** W4. **Blocked by:** W4-01. **Blocks:** W4-04.
**Binding spec sections:** §6.7 (feedback — formulas normative), §3 (degenerate-crowd ruling), §2.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The crowd's learning-from-outcomes half: revealed labels update each agent's track record, which is what the
vote weights (W4-03) and the swarm fitness (W6-01) consume. Includes the cold-start rule that stops two lucky
guesses from minting a 1.3× influencer, and the ruling for crowds too small to aggregate.

## Grounding (read before starting)

- Spec §6.7 in full (the priorPerf formula and cold start); §3's degenerate-crowd ruling.

## Specification

- **S1.** After each sample's prediction: update each participant's track record — `prior_accuracy` stays at
  its eval_accuracy seed until ≥ 5 scored inference predictions, then is REPLACED by the running fraction
  correct (spec §6.7 v1.2 ruling; replaced, not blended); `prior_performance = clamp(1.0 + 0.6 ×
  (running_acc − 0.5), 0.7, 1.3)`, held at 1.0 until the same ≥ 5 threshold; back-fill history correctness
  via W3-04's hook. Label-free samples leave all track-record state untouched (deployment tolerance).
- **S2.** Degenerate-crowd rule (spec §3): < 3 participants → skip arena and aggregation mechanism;
  certainty-weighted vote of whoever is present (crowd of one = its own prediction); result flagged Low
  confidence; occurrence counted in the manifest.

## Forbidden shortcuts

- priorPerf moving before 5 scored predictions; feedback mutating anything but the named track-record fields.

## Test requirements

1. priorPerf pins: running_acc 0.5 → 1.0; 1.0 → 1.3; 0.0 → 0.7; 4 correct → still 1.0; fifth scored →
   formula engages. prior_accuracy cold-start pin: eval-seeded value unchanged through 4 scored predictions;
   fifth scored → replaced by the running fraction (both transitions asserted at the boundary).
2. Degenerate: 2 participants → no arena, Low-confidence certainty-weighted result, counter increments;
   1 participant → its own prediction.
3. Label-free tolerance: unlabeled samples change nothing.
4. Back-fill integration: history correctness fields flip; nothing else in the store moves.

## Acceptance criteria

- Track records evolve exactly per §6.7; degenerate crowds handled per §3; pins green.
