# W3-04 — Interaction history store and trust updates

**Wave:** W3. **Blocked by:** W3-03. **Blocks:** W4-01.
**Binding spec sections:** §6.5 (trust update), §2 (trust_score), §10.2.
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The crowd's long-term social memory: who told whom what, and — once ground truth arrives — who was right.
The history store is both the trust mechanism's substrate and the project's primary analysis instrument
("who convinced whom, and were they right" must be a query, not an archaeology project).

## Grounding (read before starting)

- Spec §6.5's trust paragraph and history note; §10.2 (the two performance scales).

## Specification

- **S1.** History store, per (agent, partner, sample): partner's prediction at encounter time, agreement,
  certainty delta, round. **Cardinality ruling (review 2026-07-07):** one encounter produces exactly ONE
  undirected row in W3-02's arena encounter log and exactly TWO directed history rows here (one per
  receiving side — trust math consults each side's own view of the partner). Queryable (tidy dataframe or
  SQLite); exposes a correctness back-fill hook (W4-02 calls it when labels arrive).
- **S2.** Trust update per §6.5: `b_trust += 0.05 × (b_percCorrect × b_priorPerf) × doAgree`,
  `doAgree ∈ {+1, −1}`, NO update without prior history with that partner, clamp [0, 1]. `percCorrect` reads
  the store. Replaces W3-03's no-op stub in `InteractionPolicy.update_trust`.

## Forbidden shortcuts

- Trust updates on first contact; an unclamped trust walk; nested-dict history nobody can query.
- `prior_performance`/`prior_accuracy` confusion in the update (spec §10.2).

## Test requirements

1. No-history encounter → no trust update.
2. Capped movement: single-interaction |Δtrust| ≤ 0.05; both signs exercised; clamped at 0 and 1.
3. percCorrect over a scripted history: hand-computed and pinned.
4. Store completeness: every encounter yields exactly one encounter-log row and exactly two directed history
   rows (asserted against a scripted arena run); the back-fill hook flips correctness fields without touching
   anything else.

## Acceptance criteria

- History is queryable and back-fillable; trust dynamics pinned; W3 wave complete — the arena track is ready
  for W4-01 integration.
