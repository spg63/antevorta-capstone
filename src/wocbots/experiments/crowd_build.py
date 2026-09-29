"""W2-03 closure — the named Hollywood crowd configs, built against the REAL split.

W2-03 shipped its assignment policy, crowd builder, and two named §9.2/§9.3 configs, and its
thirty unit tests pass. Every one of those tests builds a SYNTHETIC frame with its own
invented column names, so nothing in the suite ever asked whether the shipped Hollywood
configs name columns the actual W1-03 ETL produces. They did not: both files said
`popularity` where the ETL emits `tmdb_popularity`, so either config raised
`KeyError: feature 'popularity' is not in this dataset` on first contact with real data. The
configs are fixed; this kind is the standing proof, run through the normal harness so the
evidence lands as a manifest like every other number in the project.

No new mechanism: `build_crowd` is W2-03's, merged and untouched. What is new is that the
crowd is now constructed from real Hollywood features on the train-side split, ten seeded
times, with composition and eval-accuracy reported as mean ± std (spec §9.1).

The anchor set stays `budget` — provisional per W1-06, whose RESULT block is blank and whose
measured ranking on this snapshot puts `budget` last. Re-anchoring is W1-06's ruling.

This module calls NO RNG of its own: it only advances the Generator the harness hands it
(the W0-04 RNG-discipline guard — `experiments/harness.py` is the one seed origin).
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from wocbots.agents.crowd import BuiltCrowd, CrowdConfig, build_crowd
from wocbots.experiments.config import ExperimentConfig
from wocbots.experiments.hollywood_data import (
    DEFAULT_RAW_ROOT,
    load_labeled_hollywood,
    materialize_split,
)
from wocbots.experiments.registry import register_kind

# The two named configs spec §9.2 (crowd-level matched five) and §9.3 (the 26-agent mix) call
# for. Kept here as the canonical list so a test can assert both are exercised on real data.
HOLLYWOOD_CROWD_CONFIGS: tuple[str, ...] = (
    "configs/crowd_hollywood_5agent.yaml",
    "configs/crowd_hollywood_26agent.yaml",
)


def build_hollywood_crowd(
    crowd_config_path: str,
    rng: np.random.Generator,
    raw_root: str = DEFAULT_RAW_ROOT,
) -> BuiltCrowd:
    """Load a crowd config, materialize the real split, build the crowd.

    One Generator threads split → assignment → per-agent classifier seeds, so the whole crowd
    is reproducible from one master seed (spec §9.1). `eval_data` is the train-side 90/10
    slice; the test split is never touched (spec §10.5).
    """
    config = CrowdConfig.from_yaml(crowd_config_path)
    labeled = load_labeled_hollywood(raw_root)
    split = materialize_split(labeled, rng)
    return build_crowd(
        config=config,
        train_data=split.train_data,
        eval_data=split.eval_data,
        rng=rng,
    )


def _crowd_runner(config: ExperimentConfig, rng: np.random.Generator) -> Mapping[str, float]:
    """One seeded build of one named Hollywood crowd.

    Reports composition (how many agents survived §5.3 pruning) and the eval-accuracy spread
    across the crowd. `pruned_agents` is a first-class number, not a footnote: a config that
    prunes half its crowd is telling you the feature assignment is bad (spec §5.3).
    """
    crowd_config_param = config.params.get("crowd_config")
    if not isinstance(crowd_config_param, str):
        raise ValueError(f"{config.kind!r} requires params.crowd_config (a path to a crowd YAML)")

    raw_root_param = config.params.get("raw_root", DEFAULT_RAW_ROOT)
    raw_root = raw_root_param if isinstance(raw_root_param, str) else DEFAULT_RAW_ROOT

    crowd = build_hollywood_crowd(crowd_config_param, rng, raw_root)
    manifest = crowd.manifest

    accuracies = np.array([record.eval_accuracy for record in manifest.agents], dtype=float)
    return {
        "roster_size": float(len(manifest.roster)),
        "kept_agents": float(len(manifest.agents)),
        "pruned_agents": float(len(manifest.pruned)),
        "eval_accuracy_mean": float(accuracies.mean()) if accuracies.size else 0.0,
        "eval_accuracy_min": float(accuracies.min()) if accuracies.size else 0.0,
        "eval_accuracy_max": float(accuracies.max()) if accuracies.size else 0.0,
    }


register_kind("w2_03_hollywood_crowd", _crowd_runner)
