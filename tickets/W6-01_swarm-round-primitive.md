# W6-01 — Honeybee swarm round: presenter selection, fitness wheel, watcher reassignment

**Wave:** W6. **Blocked by:** W4-01. **Blocks:** W6-02.
**Binding spec sections:** §8.1 (the round — normative, including the pseudocode and both rulings), §10.8
(degenerate rounds).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full. Mini-plan before code.

## Why this ticket exists (system meaning)

The swarm round is the bee-foraging analogue: a rotating 20% of agents "present" (scouts), the rest are
recruited by fitness-proportionate selection (the waggle dance), and dissenting strong watchers get a bounded
chance to move. Its deliberate quirks — re-rolls on the same wheel with no improvement guarantee, the two-move
cap stranding some dissenters — are retained diversity, not bugs to fix. This ticket builds the round pure and
pinned; the ladder that iterates it is W6-02.

## Grounding (read before starting)

- Spec §8.1 in full: the pseudocode, the fitness normalization ruling (prior_performance rescaled to [0,1] via
  `(pp − 0.7) / 0.6` before averaging), the ≤2-moves rule, the tie rule; §10.8.

## Specification

### S1. The round (pure function over participant profiles + RNG)

Per spec §8.1: presenters = seeded sample of `max(1, round(0.20 × N))`, with **k ≥ 2 enforced when N ≥ 10**
(spec §10.8); fitness = `(pp_norm + confidence + trust_score) / 3` with `pp_norm = (prior_performance − 0.7)
/ 0.6`; normalize over presenters → roulette wheel; watchers assigned by the wheel; dissenting watchers with
`prior_performance >` their presenter's re-roll on the SAME wheel, at most twice, stopping early on agreement;
votes = 1 + assigned watchers per presenter; returns `(agreement, majority_class, assignment_map)`. Exact tie
→ agreement 0.5, no threshold met (spec §8.1).

### S2. Determinism + instrumentation

Fully seeded via the harness Generator; the assignment map and per-round agreement land in a swarm trace
(W6-02's calibration analysis reads it).

## Forbidden shortcuts

- "Improving" the re-roll (steering toward agreeing presenters) — the no-guarantee wheel is the point.
- Unbounded reassignment, or skipping the early-stop on agreement.
- Averaging raw prior_performance (0.7–1.3) with [0,1] quantities — the scale-mixing bug the ruling exists
  to prevent.
- Mutating agent state — a round reads profiles and returns an assignment; interactions happen in W6-02.

## Test requirements

1. Presenter-count pins: N = 10/26/100 → k = 2/5/20; N = 9 → k = 2 not enforced (max(1, round(1.8)) = 2
   anyway — pin the actual arithmetic); N = 4 → k = 1 (degenerate, W6-02 routes it away).
2. Fitness pins: pp 0.7/1.0/1.3 → pp_norm 0/0.5/1; a hand-built 3-presenter wheel's selection frequencies
   match probabilities within statistical tolerance over 10k seeded draws.
3. Reassignment: a dissenting watcher with higher pp re-rolls; ≤ 2 moves enforced; agreement stops the
   re-rolls; a lower-pp dissenter never moves.
4. Vote conservation: presenter votes sum to N exactly, every round, property-tested.
5. Tie pin: engineered equal-vote round → agreement 0.5.
6. Determinism: same profiles + seed → identical assignment map.

## Acceptance criteria

- The round is a pure, pinned, instrumented primitive matching §8.1 exactly, ready for W6-02 to iterate.
