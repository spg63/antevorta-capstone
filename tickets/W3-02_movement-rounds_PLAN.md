# W3-02 — Manhattan movement, anti-clique rules, and the lockstep round engine - IMPLEMENTATION PLAN

> **STATUS: DRAFT**
>
> **About this plan.** This is the per-ticket execution plan for
> `W3-02_movement-rounds.md`, following the W3 plan skeleton.

**Ticket:**. [`W3-02_movement-rounds.md`](./W3-02_movement-rounds.md).

**Precedence:** the spec > this plan the ticket.

**Wave:** W3

**Blocked by:** W3-01

**Blocks:** W3-03, W4-01

**Binding spec sections:** [§6.3 Movement](../docs/WoC-Bots_Implementation_Spec.md#63-movement),
[§6.4 Interaction period length](../docs/WoC-Bots_Implementation_Spec.md#64-interaction-period-length),
[§10.3 Interaction ordering artifacts](../docs/WoC-Bots_Implementation_Spec.md#10-pitfalls-read-before-debugging).

**Binding preamble sections:**
[`01_MANDATORY_PREAMBLE.md`](./01_MANDATORY_PREAMBLE.md) applies in full.

---

## 1. Metadata (see header above)

Self-contained for W3-01: an implementer following
[§9](#9-sequenced-implementation-steps) and pinning
[§10](#10-test-plan-exact-pins) ships the ticket without one silent decision.

---

## 2. Why this ticket exists (system meaning)

The information-dispersal engine: randomized local movement with anti-clique
rules preventing pair echo chambers, run in lockstep rounds. The easiest place
in the project to bake in ordering artifacts that surface later as
irreproducible crowd behavior — hence the shuffle proof in the tests.

---

## 3. Decisions

- D1 `Arena`:
    - the class needs a modification to `place(self, agent: Agent, cell: Cell)`
      to add a mapping between Agent and its current position
    - a new method `move_to(self, agent: Agent, cell: Cell)` moving an agent to
      a new cell if it can
    - a new method `cell(self, agent: Agent)` returning the cell where an agent
      is
    - a new method `agents_at(self, cell: Cell)` returning a list of agents
      currently in that cell

- D2 `RoundEngine` and `RandomMovementPolicy`: both are coupled on the current
  round index. Both need the current round index:
  - `RoundEngine` becuase it needs to know when a run is finished
  - `RandomMovementPolicy` because it needs to keep track of the interaction
    between agents (same agents cannot meet twice in a row and more than twice
    within a 5 round window).
  The current interface of `MovementPolicy` cannot be touched, so
  `RandomMovementPolicy` keeps track of the number of times `move()` was called
  with each agent, and infers based in this information the the current round
  number. This means that it assumes that `RoundEngine` always moves every
  agent only once in a round. Furthermore, unit tests need to take into account
  this coupling.

---

## 4. Verified grounding facts (re-verify before coding)

- Spec [§6.3 Movement](../docs/WoC-Bots_Implementation_Spec.md#63-movement),
  mentions to have a pluggable movement interface with a function `move()`. It
  also provides a reference algorithm:

  Move one step uniformly at random in one of the 4 cardinal direction while
  staying in the arena. An interaction is triggered when moving into an already
  occupied cell with one agent. It is forbidden to move into a cell containing
  already two agents.

  Anti-clique rules: Two agents are not allowed to interact twice in a row but
  at maximum twice in. a 5-iteration window. When there is no legal move for an
  agent, he is teleported into a random empty cell.

  Stirring: teleport an agent at random even when it could move legally, as
  reference 5% of the time, this is a parameter that can be tuned.

  The movement is synchronous-in-rounds: agents movements, then agent
  interactions, then a new round starts with movements, interactions, etc.
  Agents must be iterated in a random order with each new round.



- Spec [§6.4 Interaction period
  length](../docs/WoC-Bots_Implementation_Spec.md#64-interaction-period-length)
  defines the size of the interaction period as:

  $$interaction_{iters} = \max(10,\ round(0.10 \times N))$$

- Spec [§10.3 Interaction ordering
  artifacts](../docs/WoC-Bots_Implementation_Spec.md#10-pitfalls-read-before-debugging)
  warns that if the agent iteration order is fixed in each round, this will lead
  to a bias on who flips first. Therefore iteration order must be shuffled
  between rounds.

---

## 5. Execution-path maps

per-sample experiment loop (owned later, W4-01)
```text
  -> Initialized Arena, fully populated
  -> Initialized RoundEngine with Arena, MovementPolicy, a list of Agents and
  the random number generator
  -> As long as the episode is not finished:
    -> call `round()`, the engine moves each agent in the arena at
    random, or teleports it depending on the situation
  -> The final encounter log is passed to W3-03
```

---

## 6. STEP 0 — pre-code gate (fill the RESULT block at the bottom of this file BEFORE coding)

1. Confirm the ticket W3-01 is OK in `tickets/00_INDEX.md` and W3-02 is blocked by
   no-one with independent review sign-off.
1. Confirm folder `src/wocbots/` exists.
1. Re-read this ticket, this plan, spec [§6.3
   Movement](../docs/WoC-Bots_Implementation_Spec.md#63-movement), [§6.4
   Interaction period
   length](../docs/WoC-Bots_Implementation_Spec.md#64-interaction-period-length),
   [§10.3 Interaction ordering
   artifacts](../docs/WoC-Bots_Implementation_Spec.md#10-pitfalls-read-before-debugging)
   
---

## 7. Specification

### S1 

#### `src/wocbots/arena/arena.py`

```python
from collections import defaultdict

class _GridCell:
    # ...
    def remove(self, agent: Agent) -> None:
        self._agents.remove(agent)

    @property
    def agents(self) -> list[Agent]:
        return self._agents

class Arena:
    def __init__(self, n_participants: int) -> None:
        if n_participants < 1:
            raise ValueError(f"arena requires at least 1 participants, got {n_participants}")
        self._rows: int = floor(sqrt(2 * n_participants))
        self._cols: int = ceil(2 * n_participants / self._rows)
        self._grid: list[_GridCell] = [_GridCell() for _ in range(self._rows * self._cols)]
        self._agents_cell: dict[Agent, Cell] = {}
    # ...

    def place(self, agent: Agent, cell: Cell) -> None:
        self._grid[self._index(cell)].place(agent)
        self._agents_cell[agent] = cell

    def move_to(self, agent: Agent, cell: Cell) -> None:
        if self.is_full(cell):
            raise ValueError(f"arena at cell {cell} already has two agents")
        cur_cell = self._agents_cell[agent]
        self._grid[self._index(cur_cell)].remove(agent)
        self._grid[self._index(cell)].place(agent)
        self._agents_cell[agent] = cell

    def cell(self, agent: Agent) -> Cell:
        return self._agents_cell[agent]

    def agents_at(self, cell: Cell) -> list[Agent]:
        return self._grid[self._index(cell)].agents
```

#### `src/wocbots/arena/movement_policy.py`

```python
from __future__ import annotations
from collections import deque, defaultdict
from typing import Tuple
import numpy as np

class RandomMovementPolicy:
    def __init__(self, teleport_rate: float = 0.05) -> None:
        self._moves: list[Tuple] = [(1, 0),(-1, 0),(0, 1),(0, -1)]
        self._teleport_rate: float = teleport_rate
        self._cur_round = 0
        self._moved_this_round: set[Agent] = set()
        self._current_encounter: tuple[Agent, Agent] | None = None
        self._pair_history: dict[frozenset[Agent], deque[int]] = defaultdict(deque)

    def move(self, agent: Agent, arena: Arena, rng: np.random.Generator) -> Cell:
        if agent in self._moved_this_round:
            self._cur_round += 1
            self._moved_this_round = set()
        self._moved_this_round.add(agent)

        cur_cell = arena.cell(agent)
        if rng.random() < self._teleport_rate:
            while True:
                col = rng.integers(0, arena.cols)
                row = rng.integers(0, arena.rows)
                cell: Cell = (row, col)
                if cur_cell != cell and self._can_move_to(agent, arena, cell):
                    break
            agents = arena.agents_at(cell)
            if agents:
                other_agent = arena.agents_at(cell)[0]
                self._encounter(agent, other_agent)
                self._current_encounter = (agent, other_agent)
            else:
                self._current_encounter = None
            arena.move_to(agent, cell)
            return cell

        if not self._has_moves(agent, arena):
            while True:
                col = rng.integers(0, arena.cols)
                row = rng.integers(0, arena.rows)
                cell: Cell = (row, col)
                if arena.is_empty(cell):
                    break
            self._current_encounter = None
            arena.move_to(agent, cell)
            return cell
            
        while True:
            i = rng.integers(0, len(self._moves))
            dir = self._moves[i]
            next_cell = (cur_cell[0] + dir[0], cur_cell[1] + dir[1])
            if self._can_move_to(agent, arena, next_cell):
                break

        agents = arena.agents_at(next_cell)
        if agents:
            other_agent = agents[0]
            self._encounter(agent, other_agent)
        else:
            self._current_encounter = None
        arena.move_to(agent, next_cell)
        return next_cell

    def current_encounter(self) -> tuple[Agent, Agent] | None:
        return self._current_encounter
        

    def _can_move_to(self, agent: Agent, arena: Arena, cell: Cell) -> bool:
        row, col = cell
        if row < 0 or row >= arena.rows or col < 0 or col >= arena.cols:
            return False
        if arena.is_empty(cell):
            return True
        if not arena.is_full(cell):
            other_agent = arena.agents_at(cell)[0]
            if self._can_encounter(agent, other_agent):
                return True
        return False
        

    def _has_moves(self, agent: Agent, arena: Arena) -> bool:
        cur_cell = arena.cell(agent)
        for dir in self._moves:
            next_cell = (cur_cell[0] + dir[0], cur_cell[1] + dir[1])
            if self._can_move_to(agent, arena, next_cell):
                return True
        return False

    def _can_encounter(self, a: Agent, b: Agent) -> bool:
        key = frozenset((a,b))
        if len(self._pair_history[key]) > 0 and self._pair_history[key][-1] == self._cur_round - 1:
            return False
        count = 0
        for round in self._pair_history[key]:
            if round > self._cur_round - 5:
                count +=1
        if count >= 2:
            return False
        return True

    def _encounter(self, a: Agent, b: Agent) -> None:
        key = frozenset((a,b))
        self._pair_history[key].append(self._cur_round)

        if len(self._pair_history[key]) >= 2:
            if self._pair_history[key][-1] - self._pair_history[key][0] >= 5:
                self._pair_history[key].popleft()

```

### S2 - `src/wocbots/arena/round_engine.py`

```python
from collections import defaultdict
from typing import Tuple

class RoundEngine:
    def __init__(self,
    agents: list[Agent],
    arena: Arena,
    movement_policy: MovementPolicy,
    rng: np.random.Generator,
    ) -> None:
        n: int = len(agents)
        self._agents: list[Agent] = agents
        self._agent_indices: list[int] = list(range(n))
        self._cur_round: int = 0
        self._max_rounds: int = max(10, round(0.1 * n))
        self._arena: Arena = arena
        self._movement_policy: MovementPolicy = movement_policy
        self._rng: np.random.Generator = rng
        self._encounter_log: dict[int, tuple[tuple[Agent, Agent] | None, Cell]] = defaultdict()

    def round(self) -> None:
        if self._cur_round >= self._max_rounds:
            raise RuntimeError(
                f"max number of rounds reached: {self._max_rounds}"
                )
        self._rng.shuffle(self._agent_indices)
        for i in self._agent_indices:
            cell = self._movement_policy.move(self._agents[i], self._arena, self._rng)
            encounter = self._movement_policy.current_encounter()
            self._encounter_log[self._cur_round].append((encounter, cell))
        self._cur_round += 1

    def finished(self) -> bool:
        return self._cur_round >= self._max_rounds

    @property
    def encounter_log(self) -> dict[int, tuple[tuple[Agent, Agent] | None, Cell]]:
        return self._encounter_log

```

---

## 8. Observability

- tests prove interaction constraints are followed according to [§6.3
  Movement](../docs/WoC-Bots_Implementation_Spec.md#63-movement)

- tests prove that the number of rounds are capped according [§6.4 Interaction
  period length](../docs/WoC-Bots_Implementation_Spec.md#64-interaction-period-length)

- tests prove that agents are moved in a different order each round under a
  given seed preventing [§10.3 Interaction ordering
  artifacts](../docs/WoC-Bots_Implementation_Spec.md#10-pitfalls-read-before-debugging)


---

## 9. Sequenced implementation steps

1. Run pre-code gates in §6.
1. Add `src/wocbots/arena/round_engine.py`
1. Add `src/wocbots/arena/movement_policy.py`
1. Update `src/wocbots/arena/arena.py`
1. Update `src/wocbots/arena/__init__.py`
1. Add `test/unit/test_round_engine.py`
1. Add `test/unit/test_movement_policy.py`

---

## 10. Test plan (exact pins)

Arena movement tests live in `tests/unit/test_movement_policy.py`, round engine
tests live in `tests/unit/test_round_engine.py`.

1. Over an entire run, no more than two agents can be on the same cell after one
   move with the `RandomMovementPolicy`.
1. Over an entire run, Agents cannot interact more than twice in a row and max 2
   times in a 5-iteration window
1. Agents moved with the `RandomMovementPolicy` are moved within the bounds of
   the arena
1. Agents moved with the `RandomMovementPolicy` are always teleported randomly,
   when 100% is specified in the RandomMovementPolicy's constructor
1. Agents moved with the RandomMovementPolicy are never teleported randomly,
   when 0% is specified in the `RandomMovementPolicy`'s constructor
1. Number of rounds is pinned, 5 agents -> 10 rounds; 105 agents -> 10 rounds;
   120 agents -> 12 rounds
1. Agent processing order is different accross rounds given a fixed seed
1. Agent processing order over a run is the same given a fixed seed
1. Over an entire run, every 2-agent encounter is recorded in a log and appear
   exactly once per round.
1. Round engine eventually finishes
1. The `RoundEngine` returns the an encounter log refelecting the true
   encounters from the beginning up to the current processed round.

---

## 11. Blast radius (forward commitments)

- W3-03 needs the `RandomMovementPolicy`
- W4-01 needs the `RandomMovementPolicy`

---

## 12. Risks, alternatives, open questions FOR THE STAKEHOLDER

- R1 - The agents are processed in the same order in each round.

---

## 13. Definition of Done (preamble §6, instantiated)

1. [ ] W3-01 is OK before implementation starts.
1. [ ] `RandomMovementPolicy` class exists exactly as specified.
1. [ ] `RoundEngine` class exists exactly as specified.
1. [ ] Tests in §10 land in the same change set.
1. [ ] `ruff check .` passes.
1. [ ] `ruff format --check .` passes.
1. [ ] `mypy src tests` passes.
1. [ ] `pytest` passes.
1. [ ] Encounter statistics (encounters/agent/round) recorded in the test
   manifest for tuning reference.
1. [ ] Touched paths are listed in close report.
1. [ ] Independent review signs off and `tickets/00_INDEX.md` is flipped with
    `OK (reviewed: <who/what>, <date>)`.
1. [ ] `AGENT_HANDOFF.md` is updated with the new CURRENT STATE.
