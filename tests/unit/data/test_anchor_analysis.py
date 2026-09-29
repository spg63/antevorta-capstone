import numpy as np
import pandas as pd

from wocbots.data.anchor_analysis import rank_features

FEATURES = ["budget", "vote_count", "vote_average", "tmdb_popularity", "runtime"]


def test_anchor_analysis_smoke_runs_seeded_and_ranks_budget_high() -> None:
    rng = np.random.default_rng(0)
    n = 500
    budget = rng.uniform(1_000, 100_000_000, n)
    noise = rng.normal(0, 1, n)
    # construct a label strongly (but not perfectly) driven by budget so the analysis
    # has something real to find, plus pure-noise features that should rank lower.
    label = (budget + noise * 5_000_000 > np.median(budget)).astype(int)
    df = pd.DataFrame(
        {
            "budget": budget,
            "vote_count": rng.uniform(0, 5000, n),
            "vote_average": rng.uniform(0, 10, n),
            "tmdb_popularity": rng.uniform(0, 200, n),
            "runtime": rng.uniform(60, 200, n),
            "label": label,
        }
    )
    ranking = rank_features(df, FEATURES, "label", rng=np.random.default_rng(1))
    assert set(ranking["feature"]) == set(FEATURES)
    assert "budget" in set(ranking["feature"].head(1))
