"""Dataset ETL, labels, splits (DATA stream). W1 lands the Hollywood pipeline: raw-file
provenance verification (W1-01), TMDb+MovieLens join/clean/feature-build (W1-03), label
variants + the reconciliation gate (W1-04), seeded splits + scaling (W1-05), and anchor-
feature ranking (W1-06).
"""

from wocbots.data.anchor_analysis import rank_features
from wocbots.data.hollywood import (
    OUTPUT_COLUMNS,
    aggregate_ml_ratings,
    build_hollywood_features,
    clean,
    combine_vote_features,
    genre_intersection,
    join_datasets,
)
from wocbots.data.labels import class_balance_pct, variant_a_label, variant_b_from_reference
from wocbots.data.provenance import RAW_FILES, FileProvenance, sha256_of, verify
from wocbots.data.splits import (
    DEFAULT_FEATURE_COLUMNS,
    EXCLUDED_FROM_FEATURES,
    SplitArtifact,
    apply_scaling,
    build_feature_matrix,
    make_split,
)

__all__ = [
    "DEFAULT_FEATURE_COLUMNS",
    "EXCLUDED_FROM_FEATURES",
    "OUTPUT_COLUMNS",
    "RAW_FILES",
    "FileProvenance",
    "SplitArtifact",
    "aggregate_ml_ratings",
    "apply_scaling",
    "build_feature_matrix",
    "build_hollywood_features",
    "class_balance_pct",
    "clean",
    "combine_vote_features",
    "genre_intersection",
    "join_datasets",
    "make_split",
    "rank_features",
    "sha256_of",
    "variant_a_label",
    "variant_b_from_reference",
    "verify",
]
