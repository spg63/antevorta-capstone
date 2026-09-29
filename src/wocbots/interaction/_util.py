"""Small private helpers shared across the interaction kernel (W3-03) and
its future extensions (W3-04's trust clamp uses the same [lo, hi] shape).
Not part of any locked seam — nothing here is exported from the package.
"""

from __future__ import annotations


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp `value` into [lo, hi] (spec §6.5's certainty ruling; also used
    by trust's [0, 1] clamp, spec §6.5's trust paragraph)."""
    return max(lo, min(hi, value))
