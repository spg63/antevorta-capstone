from __future__ import annotations

import pytest

from wocbots.agents import HOLLYWOOD_WEIGHTS, Agent
from wocbots.arena import Arena, CellFullError


def make_agent() -> Agent:
    return Agent(
        features=("f0",),
        eval_accuracy=0.5,
        eval_precision=0.5,
        eval_recall=0.5,
        confidence_weights=HOLLYWOOD_WEIGHTS,
    )


def test_seam_import_path_unchanged() -> None:
    """The W0-02 TYPE_CHECKING import path still resolves to this Arena."""
    from wocbots.arena import Arena as SeamArena

    assert SeamArena is Arena
    arena = SeamArena(5)
    assert (arena.rows, arena.cols) == (3, 4)


def test_arena_accepts_valid_size() -> None:
    # arrange
    n = 42
    # act
    arena = Arena(n)
    # assert
    assert arena.rows == 9
    assert arena.cols == 10


def test_arena_rejects_invalid_size() -> None:
    with pytest.raises(ValueError):
        _ = Arena(-1)


def test_arena_n5_is_right_size() -> None:
    # arrange
    n = 5
    # act
    arena = Arena(n)
    # assert
    assert arena.rows == 3
    assert arena.cols == 4


def test_arena_n10_is_right_size() -> None:
    # arrange
    n = 10
    # act
    arena = Arena(n)
    # assert
    assert arena.rows == 4
    assert arena.cols == 5


def test_arena_n26_is_right_size() -> None:
    # arrange
    n = 26
    # act
    arena = Arena(n)
    # assert
    assert arena.rows == 7
    assert arena.cols == 8


def test_arena_n3_to_200_has_right_density() -> None:
    for n in range(3, 201):
        arena = Arena(n)
        density = n / (arena.rows * arena.cols)
        assert density >= 0.4
        assert density <= 0.5


def test_grid_cell_with_more_than_2_agents_fails() -> None:
    # arrange
    arena = Arena(4)
    agents = [make_agent() for _ in range(3)]
    cell = (0, 0)
    # act
    # assert
    with pytest.raises(CellFullError):
        arena.place(agents[0], cell)
        arena.place(agents[1], cell)
        arena.place(agents[2], cell)


def test_two_constructions_different_N_provide_different_grids() -> None:
    # arrange
    arena1 = Arena(5)

    # act
    # assert
    assert (arena1.rows, arena1.cols) == (3, 4)
    arena2 = Arena(10)
    assert (arena1.rows, arena1.cols) == (3, 4)
    assert (arena2.rows, arena2.cols) == (4, 5)
