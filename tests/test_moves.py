"""Rule tests for legal-move generation."""

import maedn.constants as C
from maedn.moves import legal_moves
from maedn.state import GameState


def _state(figures):
    """Build a GameState from a 4x4 nested list of progress values."""
    s = GameState()
    s.figures = [row[:] for row in figures]
    return s


def test_home_figure_only_enters_on_six():
    s = GameState()  # everyone at HOME
    for roll in range(1, 6):
        assert legal_moves(s, 0, roll) == []
    moves = legal_moves(s, 0, 6)
    assert len(moves) == 1
    assert moves[0].is_entry and moves[0].to_progress == C.START_PROGRESS


def test_cannot_land_on_own_figure():
    # Player 0 has figures at progress 0 and 5; rolling 5 would collide.
    s = _state([[0, 5, C.HOME, C.HOME], [C.HOME] * 4, [C.HOME] * 4, [C.HOME] * 4])
    # No home figures? there are two home figures, so the A-vacate rule forces
    # moving the A figure (progress 0). With roll 5 it would land on its own
    # figure at 5 -> illegal -> forced set empty -> fall back to all moves.
    moves = legal_moves(s, 0, 5)
    targets = {(m.figure, m.to_progress) for m in moves}
    # Figure at 0 cannot move to 5 (own figure there); figure at 5 -> 10 is fine.
    assert (0, 5) not in targets
    assert (1, 10) in targets


def test_capture_marks_opponent():
    # Player 0 figure at progress 3; player 1 figure sits on board index 5.
    # Player 1 entry offset is 10, so progress -5 ... instead place opponent so
    # that its absolute index equals player 0's target.
    s = GameState()
    s.figures[0] = [3, C.HOME, C.HOME, C.HOME]  # abs index 3
    # Want opponent on abs index 5 (player 0 progress 5). Player 1 offset 10,
    # progress p -> (10+p)%40 = 5 -> p = 35.
    s.figures[1] = [35, C.HOME, C.HOME, C.HOME]
    # Player 0 still has home figures, but A field (progress 0) is empty, so on a
    # non-6 the figure at 3 is free to move.
    moves = legal_moves(s, 0, 2)  # 3 -> 5
    move = next(m for m in moves if m.figure == 0)
    assert move.captured == (1, 0)


def test_no_overshoot_into_goal():
    # Figure one short of the final goal field; only an exact roll is legal.
    s = _state([[C.LAST_PROGRESS - 1, C.HOME, C.HOME, C.HOME]] + [[C.HOME] * 4] * 3)
    # roll 1 lands exactly on LAST_PROGRESS; roll 2 overshoots.
    assert any(m.to_progress == C.LAST_PROGRESS for m in legal_moves(s, 0, 1))
    # Player 0 has home figures and A empty -> figure may move; roll 2 illegal,
    # and entry needs a 6, so no legal move at all.
    assert legal_moves(s, 0, 2) == []


def test_forced_entry_on_six():
    # Home figures waiting, A field free -> a 6 must be used to enter.
    s = _state([[10, C.HOME, C.HOME, C.HOME]] + [[C.HOME] * 4] * 3)
    moves = legal_moves(s, 0, 6)
    assert all(m.is_entry for m in moves)


def test_six_must_clear_blocked_a_field_first():
    # A figure on the A field (progress 0) with figures still on B: a 6 must move
    # that A figure onward, not the one further along.
    s = _state([[0, 12, C.HOME, C.HOME]] + [[C.HOME] * 4] * 3)
    moves = legal_moves(s, 0, 6)
    assert {m.figure for m in moves} == {0}


def test_vacate_a_field_on_non_six():
    # Figures waiting on B and a figure on A: any roll must move the A figure.
    s = _state([[0, 12, C.HOME, C.HOME]] + [[C.HOME] * 4] * 3)
    moves = legal_moves(s, 0, 3)
    assert {m.figure for m in moves} == {0}
