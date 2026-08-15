"""W1-04: the Hollywood label. See spec §4.3 item 7 and this ticket's RESULT block for the
ruling.

Variant (a) — `revenue > 2 * budget` — is the spec's stated rule (§4.3.7) and is fully
computable from W1-03's output alone. **This is the shipped label** (ratified 2026-08-15,
see the ticket's RESULT block): reference-column reconciliation was ruled out of scope
because no independent `antevorta-db` source or built ground truth was ever available (W1-02's
own `movies.sqlite` is built by the same W1-03 logic it would need to validate against, so it
is not independent). Variant (a) ships **undefended** — without row-level validation against
an independent reference, and its measured class balance (43.9/56.1) does not match the
published 47.5/52.5 within tolerance. That is a documented scope cut, not a silent one.

Variant (b) — the antevorta-db reference's `made_more_than_2x_budget` column — was never
computed and, per the ruling above, is no longer expected to be. `variant_b_from_reference` is
kept as an unexercised stub in case a genuine independent reference is supplied later; nothing
downstream depends on it.
"""

from __future__ import annotations

import pandas as pd


def variant_a_label(df: pd.DataFrame, budget_col: str = "budget", revenue_col: str = "revenue") -> pd.Series:
    """Spec §4.3.7's stated rule: 1 if revenue > 2 * budget, else 0.

    `revenue == 2 * budget` is deliberately NOT a success (strict `>`), a documented
    boundary choice pinned by `test_boundary_exactly_2x_budget_is_not_success`.
    """
    return (df[revenue_col] > 2 * df[budget_col]).astype(int)


def variant_b_from_reference(
    reference_df: pd.DataFrame, id_col: str, reference_label_col: str = "made_more_than_2x_budget"
) -> pd.Series:
    """Extract the reference's own precomputed label column, indexed by `id_col`.

    Not exercised by any test in this session (blocked — no reference table exists yet).
    Kept here, ready to call, so unblocking W1-02 doesn't require touching W1-04's code.
    """
    return reference_df.set_index(id_col)[reference_label_col]


def class_balance_pct(labels: pd.Series) -> pd.Series:
    """Class balance as percentages, index-sorted (0 then 1) for stable comparison."""
    return (labels.value_counts(normalize=True).sort_index() * 100).round(2)
