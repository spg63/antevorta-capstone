"""The runner registry (W0-03 S2).

Kinds are code, registered at import of the module that defines them — there
is no config-driven or dynamic-import way to reach a runner. This registry is
the harness's only side door, and by construction it doesn't have one: a
`kind` string resolves to exactly the callables that were registered, or it
errors listing what IS registered.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

import numpy as np

from wocbots.experiments.config import ExperimentConfig

RunnerFn = Callable[[ExperimentConfig, np.random.Generator], Mapping[str, float]]

_REGISTRY: dict[str, RunnerFn] = {}


def register_kind(key: str, runner: RunnerFn) -> None:
    """Register `runner` under `key`.

    Re-registering an already-registered key is an error — silent overwrite
    is exactly the kind of "which runner actually ran" ambiguity this
    registry exists to prevent.
    """
    if key in _REGISTRY:
        raise ValueError(
            f"experiment kind {key!r} is already registered; duplicate registration is not allowed"
        )
    _REGISTRY[key] = runner


def resolve_kind(key: str) -> RunnerFn:
    """Look up the runner registered under `key`.

    An unknown key raises `KeyError` listing every currently registered
    kind, so the failure mode is "here's what you can spell it as," not a
    bare lookup miss.
    """
    try:
        return _REGISTRY[key]
    except KeyError:
        known = ", ".join(sorted(_REGISTRY)) or "<none registered>"
        raise KeyError(f"unknown experiment kind {key!r}; registered kinds: {known}") from None


def registered_kinds() -> tuple[str, ...]:
    """Snapshot of currently registered kind names, for diagnostics/tests."""
    return tuple(sorted(_REGISTRY))
