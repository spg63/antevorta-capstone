"""W1-06: feature-correlation anchor analysis. Pure analysis, no toolkit code paths —
ranks candidate agent features by association with the label (point-biserial correlation
+ first-component PCA loadings), on the TRAIN split only (spec §5.1, §9.2). Run once per
dataset; the chosen anchor set becomes configuration for W2-03.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import pointbiserialr
from sklearn.decomposition import PCA

# sklearn's `random_state` wants a plain int, never a Generator.
_SEED_UPPER_BOUND = 2**31 - 1


def _seed_from(rng: np.random.Generator) -> int:
    """One integer seed for sklearn, drawn from the threaded Generator (mirrors
    `wocbots.agents.classifier._seed_from` / `wocbots.data.splits._seed_from`).
    """
    return int(rng.integers(0, _SEED_UPPER_BOUND))


def rank_features(
    train_df: pd.DataFrame, feature_columns: list[str], label_column: str, rng: np.random.Generator
) -> pd.DataFrame:
    """Point-biserial correlation of each feature with the binary label, plus each
    feature's loading on the first PCA component (computed on min-max-scaled features so
    no single large-scale feature dominates the component by units alone).

    Takes the harness `Generator` (W0-04 RNG-discipline rule) rather than a bare seed —
    this module calls no RNG of its own, it only advances the Generator handed to it.
    """
    labels = train_df[label_column].to_numpy()
    corr_rows = []
    for col in feature_columns:
        values = train_df[col].to_numpy(dtype=float)
        r, p = pointbiserialr(labels, values)
        corr_rows.append({"feature": col, "point_biserial_r": r, "p_value": p})
    corr_df = pd.DataFrame(corr_rows)

    scaled = train_df[feature_columns].copy()
    span = scaled.max() - scaled.min()
    span = span.replace(0, 1.0)
    scaled = (scaled - scaled.min()) / span

    pca = PCA(n_components=1, random_state=_seed_from(rng))
    pca.fit(scaled.to_numpy())
    loadings = pd.Series(pca.components_[0], index=feature_columns, name="pc1_loading")

    ranking = corr_df.merge(loadings.reset_index().rename(columns={"index": "feature"}), on="feature")
    ranking["abs_point_biserial_r"] = ranking["point_biserial_r"].abs()
    ranking["abs_pc1_loading"] = ranking["pc1_loading"].abs()
    ranking = ranking.sort_values("abs_point_biserial_r", ascending=False).reset_index(drop=True)
    return ranking
