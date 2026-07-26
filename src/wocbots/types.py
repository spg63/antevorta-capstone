"""W0-02 §7-S1 — shared coordinate and output primitives.

Deliberately generic: no dataset names, method names, or confidence-tier enums land here
(spec §11 generality rule). `tier`/`margin` stay optional until W4-04/W6-02 fill them.
"""

from typing import Literal

from pydantic import BaseModel

# Grid coordinate primitive: (row, col). Owned here; consumed by the arena (W3-01+).
Cell = tuple[int, int]


class Prediction(BaseModel, frozen=True, extra="forbid"):
    """A collective binary prediction (spec §7/§8 output).

    Frozen + extra="forbid" per the O3 ruling: a typo'd field is an ERROR, not a silent
    no-op. `class_label` is the binary call; `tier` (confidence label, spec §8.2) and
    `margin` (vote margin, spec §7) arrive with their owning tickets (W4-04/W6-02).
    """

    class_label: Literal[0, 1]
    tier: str | None = None
    margin: float | None = None
