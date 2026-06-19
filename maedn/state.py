"""Mutable game state and position helpers.

A figure's location is stored as a player-relative ``progress`` value (see
:mod:`maedn.constants`). Translating a track ``progress`` to an absolute board
index lets us detect collisions and captures between different colours, which is
the only place colours interact.
"""

from __future__ import annotations

from typing import Optional

from . import constants as C


class GameState:
    """The full, mutable state of a single game.

    ``figures[player][figure]`` holds the ``progress`` of each figure. A value
    of :data:`maedn.constants.HOME` means the figure waits on a B field;
    ``0..TRACK_LEN-1`` is on the shared track; ``TRACK_LEN..LAST_PROGRESS`` is
    inside that player's goal lane.
    """

    def __init__(self) -> None:
        # All figures start on their B (home) fields.
        self.figures: list[list[int]] = [
            [C.HOME] * C.N_FIGURES for _ in range(C.N_PLAYERS)
        ]
        self.current_player: int = 0

    # -- position helpers ---------------------------------------------------

    @staticmethod
    def absolute_index(player: int, progress: int) -> Optional[int]:
        """Absolute track index for a figure of ``player`` at ``progress``.

        Returns ``None`` for figures that are at HOME or in the goal lane (those
        occupy private fields and cannot collide with other colours).
        """
        if progress < 0 or progress >= C.TRACK_LEN:
            return None
        return (C.entry_offset(player) + progress) % C.TRACK_LEN

    def occupant_at(self, abs_index: int) -> Optional[tuple[int, int]]:
        """Return ``(player, figure)`` occupying the given absolute track field, or ``None``."""
        for player in range(C.N_PLAYERS):
            for figure, progress in enumerate(self.figures[player]):
                if self.absolute_index(player, progress) == abs_index:
                    return player, figure
        return None

    def own_goal_occupied(self, player: int, progress: int) -> bool:
        """True if ``player`` already has a figure on the given goal ``progress``."""
        return any(p == progress for p in self.figures[player])

    # -- queries ------------------------------------------------------------

    def home_figures(self, player: int) -> list[int]:
        """Indices of ``player``'s figures still waiting on B fields."""
        return [f for f, p in enumerate(self.figures[player]) if p == C.HOME]

    def is_finished(self, player: int) -> bool:
        """True when all of ``player``'s figures occupy goal fields."""
        return all(p >= C.FIRST_GOAL_PROGRESS for p in self.figures[player])

    def copy(self) -> "GameState":
        """Return a deep copy of the state (figures + current player)."""
        clone = GameState.__new__(GameState)
        clone.figures = [row[:] for row in self.figures]
        clone.current_player = self.current_player
        return clone
