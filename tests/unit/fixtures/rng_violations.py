# ruff: noqa
# mypy: ignore-errors
"""Planted-violation fixture for the RNG/wall-clock guard's self-test.

INTENTIONALLY guard-violating. Exists only to prove the guard
(`tests/unit/test_rng_discipline.py`) can catch what it claims to catch
(W0-04 S3: "an untested guard is decoration"). This file is parsed by the
guard's AST checker, never imported/executed, and is excluded from the
ruff/mypy config precisely because it is deliberately bad code.
"""

import random  # violation: bare `import random`
import numpy as np
from datetime import datetime


def bad_rng_use() -> float:
    return np.random.rand()  # violation: numpy.random call outside harness.py


def bad_wallclock_use() -> str:
    return datetime.now().isoformat()  # violation: wall-clock read outside provenance.py


def bad_random_module_use() -> float:
    return random.random()  # also flagged as ordinary code, not just the import
