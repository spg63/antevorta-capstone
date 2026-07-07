# W0-04 — The harness runner, seed discipline, and the RNG guard test

**Wave:** W0. **Blocked by:** W0-03. **Blocks:** every experiment-bearing ticket.
**Binding spec sections:** §9.1 (one Generator from the config seed; 10-run statistics).
**Formal plan:** `W0-01_scaffold-experiment-harness_PLAN.md` §5 (execution-path map), §7-S3 (harness),
§7-S4 (the guard), §10 (pins 1–3, 6).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The behavior half of the harness: config → seeded runs → aggregated manifest, with determinism structural
(SeedSequence spawning — naive `seed+i` gives correlated streams) and the one-RNG rule enforced by a test
rather than by vigilance.

## Grounding (read before starting)

- The plan §5 map and §7-S3/S4; plan §12-R3 (the standing library-nondeterminism warning this ticket hands to
  W2-02).

## Specification

- **S1.** `experiments/harness.py`: `run_experiment(config | Path) -> Path` per the plan §5 map exactly;
  `SeedSequence(seed).spawn(n_runs)` → per-run Generators; aggregate mean/std; provenance stamp; manifest
  write. Determinism contract: `model_dump(exclude={"provenance"})` byte-stable for (config, code version).
- **S2.** The `dummy` kind + `configs/dummy_smoke.yaml`; its manifest committed as the harness's first
  artifact.
- **S3.** The guard test (plan §7-S4): AST walk of `src/wocbots/` flagging module-level numpy randomness
  (allowlist: `default_rng`/`SeedSequence` in harness.py only), any `random` import, wall-clock outside
  provenance.py. Named in-test allowlist, comment per entry, self-tested against a planted-violation fixture.

## Forbidden shortcuts

- `seed+i` per-run seeding; any second entry point that runs experiments without a manifest.
- A guard without its planted-violation self-test (an untested guard is decoration).

## Test requirements

1. Round-trip: `dummy_smoke.yaml` → valid manifest, 3 runs, aggregates, correct filename.
2. Determinism pin: same config twice → byte-equal `results` block; first 3 runs of `n_runs=5` == the
   `n_runs=3` runs (spawn order, not run count).
3. Independence: per-run metrics pairwise distinct under one master seed.
4. Guard self-test: each planted violation class flagged; real tree → zero flags.

## Acceptance criteria

- One command runs an experiment reproducibly; the manifest is the only output path; the RNG rule is
  test-enforced; check suite green. W0 wave complete → all streams unblocked.
