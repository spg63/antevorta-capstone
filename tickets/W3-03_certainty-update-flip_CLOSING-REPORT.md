# W3-03 — The interaction kernel: certainty update and prediction flip — CLOSING REPORT

**Ticket:** [`W3-03_certainty-update-flip.md`](./W3-03_certainty-update-flip.md)  
**Plan:** [`W3-03_certainty-update-flip_PLAN.md`](./W3-03_certainty-update-flip_PLAN.md)  
**Implementer:** Samuel Gauthier (AI-assisted)  
**Branch:** `ticket/w3-03`  
**Date:** 2026-08-15  

---

## 1. Touched paths (project-root-relative)

**New**
- `src/wocbots/interaction/_util.py` — private `clamp()` helper ([0.01, 0.99] certainty clamp; shared with W3-04 trust)
- `src/wocbots/interaction/scoring.py` — `CertaintyFlipScoringPolicy` implementing `ScoringPolicy` seam (spec §6.5 receiving-side equations)
- `src/wocbots/interaction/policy.py` — `ReferenceInteractionPolicy` implementing `InteractionPolicy` seam (always-willing, always-truthful, no-op `update_trust` stub)
- `src/wocbots/interaction/encounter.py` — `Encounter` class, atomic per-encounter processor (compute-then-apply symmetry)
- `tests/unit/test_interaction_kernel.py` — 10 unit tests (5 ticket-mandatory + 3 discipline / degenerate-input tests)
- `tickets/W3-03_certainty-update-flip_CLOSING-REPORT.md` — this closing report

**Modified**
- `src/wocbots/interaction/__init__.py` — exports `CertaintyFlipScoringPolicy`, `ReferenceInteractionPolicy`, `Encounter`
- `tickets/W3-03_certainty-update-flip_PLAN.md` — updated status, checklist items, and finalized `Encounter` class shape (D1a)

---

## 2. Key Decisions (cross-referenced to Plan §3)

- **D1 / D1a — Atomic Per-Encounter Unit (`Encounter`):** Encapsulated the interaction kernel within `Encounter(a, b, scoring_policy, interaction_policy).process()`. Decoupled atomic encounter execution from the arena round log loop (owned by W4-01) while providing an extensible structure for W3-04 history logging (`EncounterWithHistory`).
- **D2 — File Layout:** Organized `src/wocbots/interaction/` into modular components (`scoring.py`, `policy.py`, `encounter.py`, `_util.py`) exported cleanly via `__init__.py`.
- **D3 — Defensive Profile Validation:** Read `partner_profile: Mapping[str, object]` strictly with `_require_float` (explicitly excluding `bool` to prevent numeric truncation) and `_require_prediction` (validating `0` or `1`), providing clear errors on malformed profiles and satisfying `mypy --strict`.
- **D4 — Phase 2 Invariant Guard:** Enforced non-`None` `agent.current_prediction` at the start of `update_prediction`, raising `ValueError` if invoked before Phase 2 inference.
- **D5 — Compute-Then-Apply Symmetry:** Ensured strict call-order independence by taking immutable `public_profile()` snapshots of both agents prior to executing `update_prediction` in either direction.

---

## 3. Definition of Done & Test Verification

| Requirement | Plan / Test Pin | Status |
| :--- | :--- | :--- |
| **S1 (Receiving Equations)** | `acceptance`, `influence`, `corrected` under spec names; clamp $[0.01, 0.99]$; flip on $< 0.50$ | ✅ |
| **S2 (Symmetry & Boundary)** | Compute-then-apply pre-snapshot; access partner exclusively via `public_profile()` | ✅ |
| **S3 (Policy Seams)** | Implements `ScoringPolicy` & `InteractionPolicy`; `update_trust` no-op stub for W3-04 | ✅ |
| **Test 1 (Mandatory Pin)** | §6.5 worked example: $a(0.62, 1)$ meets $b(0.80, 0, 0.71, 0.78, 1.1) \rightarrow a$ flips to $0$, certainty $0.56519072$ ($<1\text{e-}9$) | ✅ |
| **Test 2 (Agreement Mirror)** | Mirror setup agreeing on prediction $\rightarrow$ certainty $0.80519072$ ($<1\text{e-}9$), no flip | ✅ |
| **Test 3 (Flip Boundary)** | Both-sides boundary: post-update $0.499 \rightarrow$ flips ($0.501$); $0.501 \rightarrow$ no flip | ✅ |
| **Test 4 (Clamp Saturation)** | 10 consecutive agreements clamp at exactly $0.99$; acceptance ($1 - \text{cert}$) never hits $0$ | ✅ |
| **Test 5 (Symmetry Order)** | Swapped encounter constructor/processing order yields byte-identical agent states | ✅ |
| **Test 6 (Degenerate Input - Agent)** | Agent with `current_prediction = None` raises `ValueError` | ✅ |
| **Test 7 (Degenerate Input - Profile)** | Partner profile with invalid prediction or non-numeric certainty raises `ValueError`/`TypeError` | ✅ |
| **Test 8 (Interaction Policy Stub)** | `should_interact` & `truth` return `True`; `update_trust` returns `None` leaving trust unchanged | ✅ |

---

## 4. Check Suite Results

```
uv run ruff check .          -> All checks passed!
uv run ruff format --check . -> 72 files already formatted
uv run mypy src tests        -> Success: no issues found in 72 source files
uv run pytest                -> 218 passed, 11 skipped, 1 xfailed (95.97s)
```

- **Delta:** $+10$ passed tests (from baseline of $208 \rightarrow 218$).
- **Skips/Xfails:** Pre-existing, named, and unrelated to W3-03 ($11$ skipped in data/provenance and classifier slow bands, $1$ xfailed in label class balance).

---

## 5. Results Manifest

**N/A** — Pure interface and deterministic arithmetic mechanism ticket; no stochastic experiments or harness runs required.

---

## 6. Forward Commitments & Blast Radius

- **W3-04 (`history-trust`):** Subclasses/wraps `Encounter` to record directed history rows and replaces `ReferenceInteractionPolicy.update_trust()` with the §6.5 trust update formula.
- **W4-01 (`participant-selection-loop`):** Instantiates `Encounter` and invokes `.process()` for each `((a, b), cell)` item yielded by `RoundEngine.encounter_log`.
- **W6-02 (`confidence-ladder`):** Directly consumes post-arena agent certainty values produced by this kernel.

---

## 7. Status

**Implemented & Green.** Ready for independent review sign-off per `01_MANDATORY_PREAMBLE.md` §8.
