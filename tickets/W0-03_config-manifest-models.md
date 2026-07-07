# W0-03 — Experiment config, runner registry, and manifest models

**Wave:** W0. **Blocked by:** W0-01. **Blocks:** W0-04.
**Binding spec sections:** §9.1 (what an experiment must record).
**Formal plan:** `W0-WAVE_scaffold-experiment-harness_PLAN.md` §7-S3 (exact schemas — normative).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The data shapes of reproducibility: a strict config in, a strict manifest out. Models only — no runner logic
(W0-04). Strictness is the feature: an unknown config key that silently no-ops is how experiments lie.

## Grounding (read before starting)

- The plan §7-S3 verbatim: `ExperimentConfig`, registry semantics, `RunResult`/`MetricSummary`/`Provenance`/
  `Manifest`, canonical-JSON rules.

## Specification

- **S1.** `experiments/config.py`: `ExperimentConfig` (frozen, `extra="forbid"`; name/kind/seed/`n_runs=10`/
  opaque `params`). YAML loading via `safe_load` → model validation.
- **S2.** `experiments/registry.py`: `register_kind` (duplicate = error) / `resolve_kind` (unknown = error
  listing registered keys). Kinds are code, registered at import.
- **S3.** `experiments/manifest.py`: the four models per plan §7-S3; canonical JSON writer (`sort_keys`,
  UTF-8, trailing newline); filename convention `<name>_<UTCstamp>_<shortsha>.json`.
- **S4.** `experiments/provenance.py`: UTC timestamp, git SHA with `+dirty` suffix, package versions,
  platform. The ONE licensed wall-clock site (W0-04's guard will enforce that).

## Forbidden shortcuts

- Loose models anywhere (`extra="ignore"`, mutable configs).
- Runner logic creeping in — this ticket ships shapes, not behavior.

## Test requirements

1. Strictness both-sides: unknown YAML key → `ValidationError` naming the key; valid config loads frozen
   (mutation raises).
2. Registry: duplicate registration → error; unknown kind → error listing known keys.
3. Manifest round-trip: build → write → read → validate → equal.
4. Provenance: `git_sha` matches `git rev-parse HEAD`; dirty tree → `+dirty` (restore after); all six named
   package versions present.

## Acceptance criteria

- Config in / manifest out shapes exist exactly per plan §7-S3, strict by construction; check suite green.
