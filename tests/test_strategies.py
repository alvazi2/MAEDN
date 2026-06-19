"""Behavioural tests for the individual strategies."""

import random

import maedn.constants as C
from maedn.moves import Move
from maedn.state import GameState
from maedn.strategies import make_strategy


def test_registry_has_all_strategies():
    from maedn.strategies import STRATEGIES

    assert set(STRATEGIES) == {
        "mean",
        "nice",
        "random",
        "runahead",
        "defensive",
        "optimal",
    }


def test_mean_prefers_capture():
    s = GameState()
    rng = random.Random(0)
    plain = Move(figure=0, from_progress=3, to_progress=5)
    capture = Move(figure=1, from_progress=8, to_progress=10, captured=(1, 0))
    s.figures[1][0] = 30  # the captured opponent's progress (used for ranking)
    chosen = make_strategy("mean").choose(s, 0, [plain, capture], rng)
    assert chosen is capture


def test_nice_avoids_capture_when_possible():
    s = GameState()
    rng = random.Random(0)
    plain = Move(figure=0, from_progress=3, to_progress=5)
    capture = Move(figure=1, from_progress=8, to_progress=10, captured=(1, 0))
    chosen = make_strategy("nice").choose(s, 0, [plain, capture], rng)
    assert chosen is plain


def test_nice_captures_when_forced():
    s = GameState()
    rng = random.Random(0)
    only = Move(figure=1, from_progress=8, to_progress=10, captured=(1, 0))
    chosen = make_strategy("nice").choose(s, 0, [only], rng)
    assert chosen is only


def test_runahead_moves_furthest_figure():
    s = GameState()
    rng = random.Random(0)
    rear = Move(figure=0, from_progress=2, to_progress=4)
    front = Move(figure=1, from_progress=20, to_progress=22)
    chosen = make_strategy("runahead").choose(s, 0, [rear, front], rng)
    assert chosen is front


def test_defensive_prioritises_entry():
    s = GameState()
    rng = random.Random(0)
    entry = Move(figure=2, from_progress=C.HOME, to_progress=0, is_entry=True)
    other = Move(figure=0, from_progress=5, to_progress=11)
    chosen = make_strategy("defensive").choose(s, 0, [entry, other], rng)
    assert chosen is entry


def test_optimal_capture_is_top_priority():
    # The composite strategy's top priority is capturing.
    s = GameState()
    rng = random.Random(0)
    s.figures[1][0] = 25  # captured opponent's progress
    capture = Move(figure=0, from_progress=8, to_progress=10, captured=(1, 0))
    advance = Move(figure=1, from_progress=3, to_progress=5)
    chosen = make_strategy("optimal").choose(s, 0, [capture, advance], rng)
    assert chosen is capture


def test_optimal_races_leading_figure_when_safe():
    # With no captures and no threats on the board, race the most-advanced figure.
    s = GameState()  # all opponents at HOME -> nothing is threatened
    rng = random.Random(0)
    rear = Move(figure=0, from_progress=4, to_progress=6)
    front = Move(figure=1, from_progress=20, to_progress=22)
    chosen = make_strategy("optimal").choose(s, 0, [rear, front], rng)
    assert chosen is front
