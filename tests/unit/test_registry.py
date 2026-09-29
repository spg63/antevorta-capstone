from __future__ import annotations

import pytest

from wocbots.experiments.registry import register_kind, resolve_kind


def test_duplicate_registration_errors() -> None:
    register_kind("test-dup-kind", lambda cfg, rng: {})
    with pytest.raises(ValueError, match="already registered"):
        register_kind("test-dup-kind", lambda cfg, rng: {})


def test_unknown_kind_lists_registered() -> None:
    register_kind("test-known-kind", lambda cfg, rng: {})
    with pytest.raises(KeyError) as exc_info:
        resolve_kind("test-totally-unknown-kind")
    assert "test-known-kind" in str(exc_info.value)


def test_resolve_returns_registered_runner() -> None:
    def runner(cfg: object, rng: object) -> dict[str, float]:
        return {"a": 1.0}

    register_kind("test-resolve-kind", runner)
    assert resolve_kind("test-resolve-kind") is runner
