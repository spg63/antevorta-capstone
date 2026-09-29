"""The experiment config shape (W0-03 S1).

Strict by construction: `frozen=True` (a loaded config cannot be mutated
out from under a run) and `extra="forbid"` (an unknown key is a
`ValidationError`, not a silent no-op). A typo'd config field is exactly how
an experiment quietly stops meaning what its YAML says it means; this model
makes that impossible instead of relying on review vigilance.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, JsonValue

# O3 ruling (team, 2026-07-06): pydantic v2, extra="forbid", frozen=True.


class ExperimentConfig(BaseModel):
    """One config drives one experiment invocation.

    `params` is opaque to this model on purpose — kind-specific validation
    belongs to the registered runner, not to the shared config shape
    (see `registry.py`).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    """Manifest filename stem."""

    kind: str
    """Registry key resolved via `registry.resolve_kind`."""

    seed: int
    """The ONE master seed. `harness.run_experiment` is the only place this
    is consumed to mint randomness (spec §9.1)."""

    n_runs: int = 10
    """Spec §9.1 default: every reported number is a mean ± std over 10 runs."""

    params: dict[str, JsonValue] = Field(default_factory=dict)
    """Kind-specific, opaque here; the resolved runner validates its own shape."""

    @classmethod
    def from_yaml(cls, path: Path | str) -> ExperimentConfig:
        """Load + validate a config from a YAML file via `yaml.safe_load`.

        Any key not declared above raises `pydantic.ValidationError` naming
        the offending key — this is the "strict both-sides" half of the
        harness's data-shape contract (the other half is the manifest).
        """
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if raw is None:
            raw = {}
        return cls.model_validate(raw)
