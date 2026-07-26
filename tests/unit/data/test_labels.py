"""W1-04 test requirements.

1. Boundary pin: revenue == 2*budget -> label 0 under variant (a). This is a pure logic
   pin, unaffected by which raw-data snapshot is on disk — always runs, always must pass.
2. Row-level validation against W1-02's reference: BLOCKED. No reference table exists in
   this session (see data/DATA_PROVENANCE.md §5) — there is nothing to validate against,
   so this test cannot exist yet. Adding it back is W1-02's job, not a retrofit here.
3. Class-balance pin (shipped label within +/-1pt of 47.5/52.5): marked xfail. The actual
   run (see the ticket's RESULT block) lands at 43.9/56.1 on the raw data available this
   session — outside tolerance. Preamble §0.2 is explicit: a test pin that can't pass
   without changing the mechanism it pins is a STOP condition, not something to quietly
   loosen. This is the W1-04 gate firing; it is recorded as an escalation, not silenced.
"""

import pandas as pd
import pytest

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


@pytest.mark.xfail(
    reason=(
        "W1-04 gate: shipped variant (a) balance measured 43.9/56.1 on this session's raw "
        "data, outside the +/-1pt tolerance of the published 47.5/52.5 — escalated to the "
        "stakeholder per the ticket's own rule, not silently loosened. See RESULT block."
    ),
    strict=True,
)
def test_class_balance_within_one_point_of_published_split() -> None:
    df = pd.read_csv("data/hollywood_features_labeled_variant_a.csv")
    balance = class_balance_pct(df["label_a"])
    assert abs(balance.loc[0] - 47.5) <= 1.0
    assert abs(balance.loc[1] - 52.5) <= 1.0
