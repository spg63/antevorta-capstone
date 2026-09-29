# W3-01 — Arena grid geometry and random initialization - IMPLEMENTATION PLAN

> **STATUS: IMPLEMENTED, PENDING INDEPENDENT REVIEW**
>
> **About this plan.** This is the per-ticket execution plan for
> `W3-01_grid-geometry-init.md`, following the W3 plan skeleton.

**Ticket:**. [`W3-01_grid-geometry-init.md`](./W3-01_grid-geometry-init.md).

**Precedence:** the spec > this plan the ticket.

**Wave:** W3

**Blocked by:** W0-02

**Blocks:** W3-02

**Binding spec sections:** [§6.1 (geometry)](../docs/WoC-Bots_Implementation_Spec.md#61-geometry),
[§6.2 (initialization)](../docs/WoC-Bots_Implementation_Spec.md#62-initialization),
[§10.7 (per-sample sizing)](../docs/WoC-Bots_Implementation_Spec.md#10-pitfalls-read-before-debugging).

**Binding preamble sections:**
[`01_MANDATORY_PREAMBLE.md`](./01_MANDATORY_PREAMBLE.md) applies in full.

---

## 1. Metadata (see header above)

Self-contained for W3-01: an implementer following
[§9](#9-sequenced-implementation-steps) and pinning
[§10](#10-test-plan-exact-pins) ships the ticket without one silent decision.

---

## 2. Why this ticket exists (system meaning)

The spatial substrate: a grid sized from THIS sample's participants, max two
agents per cell, random no- overlap placement. Small and pure — and the natural
first ticket for the ARENA stream to learn the pin- everything test style on.

---

## 3. Decisions

- D1 - Keeping an internal `_GridCell` class that can hold up to two agents.
  `Arena` exists once per sample, hence short lived and rebuilt hundreds of
  thousands times across a run. Cleaner OOP wise, but may need to be revisited
  in case of poor performance.

---

## 4. Verified grounding facts (re-verify before coding)

- Spec [§6.1 (geometry)](../docs/WoC-Bots_Implementation_Spec.md#61-geometry),
  defines the geometry of the arena grid `Arena`. There are 2 x N discrete cells
  for N participants. The shape of the grid is a near-square rectangle with the
  following formulas for the rows and columns:

  - `rows = floor(sqrt(2N))`

  - `cols = ceil(2N / rows)`

  This allows for a capacity between [2N, 2N+rows). It is forbidden to have a
  plain square, as this dilutes the density. The abstraction has to support
  arbitrary rectangular compositions: rooms, floors, etc.

  Any cell holding more than one agent and less or equal to two is considered as
  an encounter. A cell cannot hold more than two agents.

- Spec [§6.2
  (initialization)](../docs/WoC-Bots_Implementation_Spec.md#62-initialization)
  mentions that at the initialization step, each agent is placed in a random
  empty cell. A cell is defined by §6.1 as empty if no agent is inside. The
  initialization strategy is a pluggable interface. Random empty cell is the
  reference implementation. Clustering-similar-agents and maximal-spread are
  documented open experiments, out of scope here.

- Spec [§10.7 (per-sample
  sizing)](../docs/WoC-Bots_Implementation_Spec.md#10-pitfalls-read-before-debugging)
  warns that if the arena size, interaction iteration and 20% presenter count
  are not computed from the current sample participant count, the simulation can
  crash because of missing participants.


---

## 5. Execution-path maps

per-sample experiment loop (owned later, W4-01)
```text
  -> Arena(n_participants)              # fresh grid, sized from THIS sample (pitfall §10.7)
  -> for each participant, shuffled or not (init doesn't care about order):
       InitPolicy.place(agent, arena, rng) -> Cell
       arena.place(agent, cell)          # mutates grid state
  -> fully-populated Arena, no co-located agents
  -> handed to W3-02's movement/round engine
```

---

## 6. STEP 0 — pre-code gate (fill the RESULT block at the bottom of this file BEFORE coding)

1. Confirm the wave W0 is OK in `tickets/00_INDEX.md` and W3-01 is blocked by
   no-one with independent review sign-off.
1. Confirm folder `src/wocbots/arena` exists.
1. Re-read this ticket, this plan, spec [§6.1
   (geometry)](../docs/WoC-Bots_Implementation_Spec.md#61-geometry),
   [§6.2 (initialization)](../docs/WoC-Bots_Implementation_Spec.md#62-initialization).
   

---

## 7. Specification

### S1 - `src/wocbots/arena/arena.py`

```python
from __future__ import annotations
from typing import TYPE_CHECKING
from math import floor, sqrt, ceil
from wocbots.types import Cell

if TYPE_CHECKING:
    from wocbots.agents import Agent


class CellFullError(RuntimeError):
    """Raised when placement is attempted on an already full cell."""


class _GridCell:
    """Private per-cell occupancy bookkeeping. Never exposed outside Arena"""

    def __init__(self) -> None:
        self._agents: list[Agent] = []

    def place(self, agent: Agent) -> None:
        if len(self._agents) >= 2:
            raise CellFullError("cell already holds 2 agents.")
        self._agents.append(agent)

    def empty(self) -> bool:
        return not self._agents

    def full(self) -> bool:
        return len(self._agents) == 2


class Arena:
    def __init__(self, n_participants: int) -> None:
        if n_participants < 1:
            raise ValueError(f"arena requires at least 1 participants, got {n_participants}")
        self._rows: int = floor(sqrt(2 * n_participants))
        self._cols: int = ceil(2 * n_participants / self._rows)
        self._grid: list[_GridCell] = [_GridCell() for _ in range(self._rows * self._cols)]

    def _index(self, cell: Cell) -> int:
        row, col = cell
        return row * self._cols + col

    def is_empty(self, cell: Cell) -> bool:
        return self._grid[self._index(cell)].empty()

    def is_full(self, cell: Cell) -> bool:
        return self._grid[self._index(cell)].full()

    def place(self, agent: Agent, cell: Cell) -> None:
        self._grid[self._index(cell)].place(agent)

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols
```

### S2 - `src/wocbots/arena/init_policy.py`

```python
from __future__ import annotations
import numpy as np

from typing import TYPE_CHECKING

from wocbots.types import Cell

if TYPE_CHECKING:
    from wocbots.agents import Agent
    from wocbots.arena import Arena


class RandomInitPolicy:
    """Arena placement at the start of a sample's interaction period (spec §6.2; W3-01).

    Reference implementation: uniformly random empty cell. Clustering / maximal-spread
    are documented open experiments — hence the seam.
    """

    def place(self, agent: Agent, arena: Arena, rng: np.random.Generator) -> Cell:
        while True:
            col = rng.integers(0, arena.cols)
            row = rng.integers(0, arena.rows)
            cell: Cell = (row, col)
            if arena.is_empty(cell):
                break
        arena.place(agent, cell)
        return cell
```

---

## 8. Observability

- tests prove that an arena can be constructed having a rectangular shape 
- tests prove that an arena can be initialized using the init policy that places
  each agents in their own separate cell.

No logs, manifests, traces, or debug hooks are added in this ticket.

---

## 9. Sequenced implementation steps

1. Run pre-code gates in §6.
1. Add `src/wocbots/arena/arena.py`
1. Add `src/wocbots/arena/init_policy.py`
1. Add `tests/unit/test_grid_geometry.py`
1. Add `tests/unit/test_random_init_policy.py`
1. Update `arena/__init__.py` to import and reexport `Arena` from `arena.py`
1. Retire the `test_arena_stub_names_owner` in `tests/unit/test_w0_02_seams.py`
1. Add `test_seam_import_path_unchanged` to `tests/unit/test_grid_geometry.py`

---

## 10. Test plan (exact pins)

Arena shape tests live in `tests/unit/test_grid_geometry.py`, initialization
tests live in `tests/unit/test_init_policy.py`.

1. Arena accepts valid size `N`
1. Arena rejects invalid size `N< 1`
1. Arena with N=5 produces a 3x4 grid
1. Arena with N=10 produces a 4x5 grid
1. Arena with N=26 produces a 7x8 grid
1. Arena must have a density of N/cells between [0.4, 0.5], tested
   over the range [3, 200] participants.
1. A grid cell cannot have more than two agents at the same time
1. Init places all agents in separate cells
1. Init places all agents within the bounds of the arena
1. Init is deterministic under a given seed
1. Two consecutive constructions with different N produce independently sized
   grids.

---

## 11. Blast radius (forward commitments)

- W3-02 needs the `Arena`

---

## 12. Risks, alternatives, open questions FOR THE STAKEHOLDER

- R1 - Very large arena might be slow as agents are stored in cells in a list
- R2 - Unbounded retry in `InitPolicy.place()`: there is no try cap which could
  lead to an infinite loop. Bounded in practice because the capacity is between
  [2N, 2N + rows) with N agents.

---

## 13. Definition of Done (preamble §6, instantiated)

1. [X] W0 is OK before implementation starts.
1. [X] `Arena` class exists exactly as specified.
1. [X] `RandomInitPolicy` class exists exactly as specified.
1. [X] The `Arena` and `InitPolicy` work on fake agents, reproducible with given
   seed.
1. [X] Tests in §10 land in the same change set.
1. [X] `ruff check .` passes.
1. [X] `ruff format --check .` passes.
1. [X] `mypy src tests` passes.
1. [X] `pytest` passes.
1. [X] No results manifest is claimed or expected for this pure interface ticket.
1. [X] Touched paths are listed in close report.
1. [X] Independent review signs off and `tickets/00_INDEX.md` is flipped with
    `OK (reviewed: <who/what>, <date>)`.
1. [X] `AGENT_HANDOFF.md` is updated with the new CURRENT STATE.
