"""Legal-move generation, including the forced-move rules.

The base rules of *Mensch ärgere Dich nicht* force certain moves (you *must*
bring a figure in on a 6, you *must* vacate your A field while figures wait).
Encoding that here means :mod:`maedn.strategies` only ever decides between moves
that are genuinely the player's free choice.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import constants as C
from .state import GameState


@dataclass(frozen=True)
class Move:
    """A single candidate move for one figure.

    ``captured`` is ``(player, figure)`` of an opponent figure sent home by this
    move, or ``None``. ``is_entry`` marks a figure coming from a B field onto its
    A field.
    """

    figure: int
    from_progress: int
    to_progress: int
    is_entry: bool = False
    captured: Optional[tuple[int, int]] = None

    @property
    def is_capture(self) -> bool:
        return self.captured is not None


def _landing(state: GameState, player: int, to_progress: int) -> Optional[Move]:
    """Resolve a target ``to_progress`` for ``player`` into the captured info.

    Returns a partially-built sentinel via ``Move`` only to carry the
    ``captured`` field, or ``None`` if the landing is illegal (own figure
    already there). The caller fills in the remaining fields.
    """
    if to_progress >= C.FIRST_GOAL_PROGRESS:
        # Goal field: must be unoccupied by an own figure (exact entry; no
        # opponent can ever be in our goal lane).
        if state.own_goal_occupied(player, to_progress):
            return None
        return Move(figure=-1, from_progress=-1, to_progress=to_progress)

    abs_index = GameState.absolute_index(player, to_progress)
    occupant = state.occupant_at(abs_index)
    if occupant is None:
        return Move(figure=-1, from_progress=-1, to_progress=to_progress)
    occ_player, _ = occupant
    if occ_player == player:
        return None  # one figure per field; cannot land on own figure
    return Move(
        figure=-1, from_progress=-1, to_progress=to_progress, captured=occupant
    )


def _move_for_figure(
    state: GameState, player: int, figure: int, roll: int
) -> Optional[Move]:
    """Build the (single) legal move for ``figure`` under ``roll``, or ``None``."""
    progress = state.figures[player][figure]

    if progress == C.HOME:
        if roll != C.ENTRY_ROLL:
            return None
        landing = _landing(state, player, C.START_PROGRESS)
        if landing is None:
            return None  # A field blocked by an own figure
        return Move(
            figure=figure,
            from_progress=C.HOME,
            to_progress=C.START_PROGRESS,
            is_entry=True,
            captured=landing.captured,
        )

    to_progress = progress + roll
    if to_progress > C.LAST_PROGRESS:
        return None  # overshoot: exact roll required to finish
    landing = _landing(state, player, to_progress)
    if landing is None:
        return None
    return Move(
        figure=figure,
        from_progress=progress,
        to_progress=to_progress,
        captured=landing.captured,
    )


def _all_moves(state: GameState, player: int, roll: int) -> list[Move]:
    moves = []
    for figure in range(C.N_FIGURES):
        move = _move_for_figure(state, player, figure, roll)
        if move is not None:
            moves.append(move)
    return moves


def _figure_on_a_field(state: GameState, player: int) -> Optional[int]:
    """Index of ``player``'s own figure sitting on its A field, or ``None``."""
    for figure, progress in enumerate(state.figures[player]):
        if progress == C.START_PROGRESS:
            return figure
    return None


def legal_moves(state: GameState, player: int, roll: int) -> list[Move]:
    """Return the moves ``player`` may choose from for ``roll``.

    Applies the base forced-move rules so that the returned list contains only
    genuinely free choices:

    * On a 6 with figures still on a B field, the player **must** bring a figure
      in -- or, if the A field is blocked by an own figure, **must** move that
      figure onward first.
    * On any roll, while figures still wait on B fields, the figure on the A
      field **must** be moved off when it can.

    If a forced rule cannot be satisfied (e.g. the A figure is itself blocked),
    we fall back to all otherwise-legal moves rather than deadlock the turn.
    """
    home = state.home_figures(player)
    a_figure = _figure_on_a_field(state, player)

    if roll == C.ENTRY_ROLL and home:
        if a_figure is not None:
            # Must clear the A field with the 6 before a new figure can enter.
            forced = [
                m for m in _all_moves(state, player, roll) if m.figure == a_figure
            ]
            if forced:
                return forced
        else:
            entry = _move_for_figure(state, player, home[0], roll)
            if entry is not None:
                return [entry]
        # Forced entry impossible -> fall back to any legal move.

    elif home and a_figure is not None:
        # Non-6 roll: the A field must be vacated while figures wait on B.
        forced = [m for m in _all_moves(state, player, roll) if m.figure == a_figure]
        if forced:
            return forced

    return _all_moves(state, player, roll)
