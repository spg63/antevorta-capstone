"""W1-04 test requirements.

1. Boundary pin: revenue == 2*budget -> label 0 under variant (a). This is a pure logic
   pin, unaffected by which raw-data snapshot is on disk — always runs, always must pass.
2. Row-level validation against W1-02's reference: still does not exist. Reference-column
   reconciliation (variant (b)) was ruled OUT OF SCOPE (ticket RESULT block, ratified
   2026-08-15) rather than merely blocked — there is no reference to validate against and
   none is expected. Adding this test back is only in scope if a genuine independent
   reference is supplied later.
3. Class-balance pin: NOT a "matches 47.5/52.5" assertion anymore. That gate fired, was
   escalated, and was resolved by ruling variant (a) shipped **undefended** — i.e. the
   ticket explicitly does not require this match. What remains testable is that the
   shipped label is reproducible: `test_shipped_label_balance_matches_ratified_result`
   pins the actual measured balance (43.93/56.07 on `data/processed/movies.sqlite`, n=3,032) so a
   silent change to the label definition or the underlying data would be caught, without
   re-imposing the published-balance requirement the ruling deliberately waived.
"""

import pandas as pd

from wocbots.data.labels import class_balance_pct, variant_a_label


def test_boundary_exactly_2x_budget_is_not_success() -> None:
    df = pd.DataFrame({"budget": [1000.0], "revenue": [2000.0]})
    labels = variant_a_label(df)
    assert labels.iloc[0] == 0


def test_boundary_just_above_2x_budget_is_success() -> None:
    df = pd.DataFrame({"budget": [1000.0], "revenue": [2000.01]})
    labels = variant_a_label(df)
    assert labels.iloc[0] == 1


def test_boundary_just_below_2x_budget_is_not_success() -> None:
    df = pd.DataFrame({"budget": [1000.0], "revenue": [1999.99]})
    labels = variant_a_label(df)
    assert labels.iloc[0] == 0


def test_shipped_label_balance_matches_ratified_result() -> None:
    """Regression pin for the ratified RESULT block, not a published-balance check — the
    ticket's own ruling (2026-08-15) waived the 47.5/52.5 match requirement when it shipped
    variant (a) undefended. This test only catches an accidental drift in the label
    definition or the underlying `movies.sqlite` snapshot.
    """
    df = pd.read_csv("data/hollywood_features_labeled_variant_a.csv")
    balance = class_balance_pct(df["label_a"])
    assert balance.loc[0] == 43.93
    assert balance.loc[1] == 56.07
    assert len(df) == 3032
