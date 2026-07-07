# W2-02 — Classifier wrappers: train, evaluate, initialize, prune (+ the sanity agent)

**Wave:** W2. **Blocked by:** W2-01, W0-04 (synthetic-data ACs); W1-05 (real-data ACs). **Blocks:** W2-03,
W4-01.
**Binding spec sections:** §5.2 (classifier), §5.3 (pruning), §9.2 (sanity agent), §10.5, §10.9.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The sklearn-facing half of the agent: train a small MLP on a feature subset, measure it on the eval slice,
feed the metrics into W2-01's initialization, prune the hopeless. Carries the plan §12-R3 standing warning:
library nondeterminism (BLAS threads, `n_jobs`) is THIS ticket's problem to pin.

## Grounding (read before starting)

- Spec §5.2–5.3; §9.2's sanity-agent row; the plan §12-R3 warning.

## Specification

- **S1.** Classifier seam: MLP variant per §5.2 — hidden layers `max(1, round(0.3 × input_size))`, width 32
  default, Adam lr 0.001, batch 32, epochs 5–50 config, one documented P(class=1) convention — plus a
  `LogisticRegression` variant (proves agent-internals don't matter). Seeded from the harness Generator;
  single-threaded/explicitly-seeded so the W0-04 determinism contract holds.
- **S2.** Train on the agent's feature subset → evaluate (accuracy/precision/recall) on the W1-05 eval slice
  → initialize W2-01 state → prune at `eval_accuracy < 0.50` (spec §5.3), pruned agents logged.
- **S3.** The sanity agent: a budget+revenue constructor on a dedicated path able to see `revenue`,
  structurally unreachable from normal crowd construction (spec §10.9). Its ~100% is the pipeline canary.

## Forbidden shortcuts

- Eval metrics from anything but the train-side eval slice (spec §10.5).
- Per-agent hand-tuned architectures; the sanity agent reachable from normal construction.

## Test requirements

1. Architecture pins: input sizes 2/3/10 → hidden layers 1/1/3.
2. Pruning both-sides: 0.499 pruned / 0.501 kept, logged.
3. Determinism: same subset + seed → identical trained metrics (twice).
4. Synthetic e2e: one agent ≥ 99% on a separable 2-feature set.
5. Real data (slow, W1-05): sanity agent ~100%; budget+vote_count agent in the §9.2 band (75.7 ± 3).

## Acceptance criteria

- Agents train seeded and reproducibly; pruning works; the canary is green on real data.
