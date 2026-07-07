# W0-02 — Shared types and the five policy seams

**Wave:** W0. **Blocked by:** W0-01. **Blocks:** W2-01, W3-01 (they bind these seams).
**Binding spec sections:** §11 (policy protocols), §6.5 (the public-profile boundary rationale).
**Formal plan:** `W0-01_scaffold-experiment-harness_PLAN.md` §7-S2 (exact signatures — normative).
**Preamble:** `01_MANDATORY_PREAMBLE.md` applies in full.

## Why this ticket exists (system meaning)

The seams exist BEFORE the things they connect, so W2/W3/W4/W6 grow into interfaces instead of getting
refactored apart later. Smallest ticket in the set; highest forward blast radius (plan §11).

## Grounding (read before starting)

- The plan §7-S2 verbatim: `Cell`, `Prediction`, the five `@runtime_checkable` Protocols, the stub rule.

## Specification

- **S1.** `types.py`: `Cell = tuple[int, int]`; `Prediction` (pydantic, frozen, `extra="forbid"`,
  `class_label: Literal[0,1]`, optional `tier`/`margin`).
- **S2.** `protocols.py`: `InitPolicy.place`, `MovementPolicy.move`,
  `InteractionPolicy.should_interact/truth/update_trust`, `ScoringPolicy.update_prediction` (partner as
  read-only `Mapping` — the §6.5 privacy boundary), `Aggregator.aggregate`. Docstrings cite owning spec
  sections and owning tickets.
- **S3.** `Agent`/`Arena` stubs: every method `raise NotImplementedError("W2-01 owns Agent")` (resp. W3-01).
  Later tickets replace internals and may tighten types; renaming/loosening a seam is a cross-ticket contract
  change routed through the index.

## Forbidden shortcuts

- Typing `partner_profile` as `Agent` (the exact hole the boundary closes).
- Speculative fields/methods for imagined future needs — seams grow when their owning ticket arrives.

## Test requirements

1. A trivial fake per seam passes `isinstance` (runtime_checkable) and mypy strict.
2. Stub methods raise `NotImplementedError` naming the owning ticket.
3. `Prediction`: `class_label` outside {0,1} rejected; frozen; unknown keys rejected.

## Acceptance criteria

- The five seams + stubs exist exactly per plan §7-S2; check suite green.
