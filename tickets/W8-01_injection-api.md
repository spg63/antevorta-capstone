# W8-01 — The incremental-feature injection API (mechanism)

**Wave:** W8. **Blocked by:** W5-05. **Blocks:** W8-02.
**Binding spec sections:** §1 (the capability claim), §3 (lifecycle continuity), §6.7 (cold start).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The architecture's flagship claim as a first-class code path: a new feature is absorbed by TRAINING NEW
AGENTS, never by retraining the crowd. The reference implementation never built this as an API — doing so
genuinely exceeds the original. Mechanism only; the study is W8-02, and the claim's honesty lives in this
ticket's untouched-crowd proof.

## Grounding (read before starting)

- Spec §1's incremental paragraph, §3, §5.1, §6.7's cold-start rules.

## Specification

- **S1.** `crowd.add_agents(new_agents)` (or equivalent): new agents train on their (new + anchor) features
  in isolation, evaluate/initialize/prune per W2-02, join the participant pool cold (`prior_performance =
  1.0`, no history — the W4-02 cold-start rules already handle newcomers).
- **S2.** The untouched-crowd guarantee: existing agents' classifier parameters and training-time state are
  frozen/hashed before and after injection. Enumerate exactly which fields MAY move afterward (the persisting
  track-record fields, evolving on the shared test stream) and pin the rest.

## Forbidden shortcuts

- Any retraining/re-evaluation of existing agents on the injection path; warm-started trust/history for
  injected agents.

## Test requirements

1. Untouched-crowd proof: pre/post hashes identical on the pinned field set.
2. Cold-start integration: injected agents enter at priorPerf 1.0/no history; ≥ 5 predictions before the
   formula moves them.
3. Lifecycle continuity: sample n pre-injection and n+1 post-injection both complete; participant accounting
   reflects the larger crowd.

## Acceptance criteria

- Injection is a tested, first-class API with the untouched-crowd guarantee proven structurally.
