from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from wocbots.experiments.config import ExperimentConfig


def test_defaults_and_frozen() -> None:
    cfg = ExperimentConfig(name="x", kind="dummy", seed=1)
    assert cfg.n_runs == 10
    assert cfg.params == {}
    with pytest.raises(ValidationError):
        cfg.name = "y"


def test_unknown_yaml_key_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("name: x\nkind: dummy\nseed: 1\nbogus_field: 3\n", encoding="utf-8")
    with pytest.raises(ValidationError) as exc_info:
        ExperimentConfig.from_yaml(path)
    assert "bogus_field" in str(exc_info.value)


def test_unknown_constructor_key_rejected() -> None:
    with pytest.raises(ValidationError):
        ExperimentConfig(name="x", kind="dummy", seed=1, bogus_field=3)  # type: ignore[call-arg]


def test_valid_yaml_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "good.yaml"
    path.write_text("name: x\nkind: dummy\nseed: 1\nn_runs: 5\nparams:\n  n: 10\n", encoding="utf-8")
    cfg = ExperimentConfig.from_yaml(path)
    assert cfg == ExperimentConfig(name="x", kind="dummy", seed=1, n_runs=5, params={"n": 10})


def test_empty_yaml_still_requires_fields(tmp_path: Path) -> None:
    path = tmp_path / "empty.yaml"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ValidationError):
        ExperimentConfig.from_yaml(path)
