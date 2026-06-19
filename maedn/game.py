"""Single-game engine: runs one game to completion and reports the outcome."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import constants as C
from .moves import Move, legal_moves
from .state import GameState
from .strategies import Strategy

#: Safety cap on a player's consecutive rolls within one turn (repeated 6s).
_MAX_ROLLS_PER_TURN = 100


@dataclass
class GameResult:
    """Outcome and statistics of one finished game."""

    winner: int
    winner_strategy: str
    seat_strategies: list[str]
    turns: int
    rolls: int
    captures_made: list[int]
    captures_suffered: list[int]
    #: Seats in the order they finished all four figures (winner first).
    ranking: list[int] = field(default_factory=list)
    #: True if the game stopped on the turn cap instead of a real finish.
    hit_turn_cap: bool = False


class Game:
    """Drive one game with a per-seat list of strategies.

    Each of the four seats has its own (independently chosen) strategy. The same
    strategy instance may be reused across seats. ``rng`` makes the whole game
    deterministic for a given seed.
    """

    def __init__(
        self,
        strategies: list[Strategy],
        rng: random.Random,
        continue_to_full_ranking: bool = False,
        max_turns: int = 2000,
    ) -> None:
        if len(strategies) != C.N_PLAYERS:
            raise ValueError(f"need {C.N_PLAYERS} strategies, got {len(strategies)}")
        self.strategies = strategies
        self.rng = rng
        self.continue_to_full_ranking = continue_to_full_ranking
        self.max_turns = max_turns

        self.state = GameState()
        self.captures_made = [0] * C.N_PLAYERS
        self.captures_suffered = [0] * C.N_PLAYERS
        self.ranking: list[int] = []

    # -- mechanics ----------------------------------------------------------

    def _apply(self, player: int, move: Move) -> None:
        if move.captured is not None:
            opp, opp_fig = move.captured
            self.state.figures[opp][opp_fig] = C.HOME
            self.captures_made[player] += 1
            self.captures_suffered[opp] += 1
        self.state.figures[player][move.figure] = move.to_progress

    def _take_turn(self, player: int) -> int:
        """Play one player's full turn; return the number of dice rolls made.

        A turn may include several rolls because every 6 grants another roll.
        """
        strategy = self.strategies[player]
        for roll_count in range(1, _MAX_ROLLS_PER_TURN + 1):
            roll = self.rng.randint(1, 6)
            moves = legal_moves(self.state, player, roll)
            if moves:
                move = strategy.choose(self.state, player, moves, self.rng)
                self._apply(player, move)
            if self.state.is_finished(player) and player not in self.ranking:
                self.ranking.append(player)
            # A 6 grants another roll, unless this player is already done.
            if roll == C.ENTRY_ROLL and not self.state.is_finished(player):
                continue
            return roll_count
        return _MAX_ROLLS_PER_TURN

    # -- driver -------------------------------------------------------------

    def _game_over(self) -> bool:
        if not self.ranking:
            return False
        if not self.continue_to_full_ranking:
            return True
        # Continue until only one seat is left unfinished.
        return len(self.ranking) >= C.N_PLAYERS - 1

    def play(self) -> GameResult:
        """Run the game to completion and return its :class:`GameResult`."""
        player = 0
        turns = 0
        rolls = 0
        hit_cap = False

        while True:
            if self._game_over():
                break
            if turns >= self.max_turns:
                hit_cap = True
                break
            # Skip seats that have already finished (relevant only when playing
            # on for a full ranking).
            if not self.state.is_finished(player):
                rolls += self._take_turn(player)
                turns += 1
            player = (player + 1) % C.N_PLAYERS

        winner = self.ranking[0] if self.ranking else -1
        return GameResult(
            winner=winner,
            winner_strategy=self.strategies[winner].name if winner >= 0 else "none",
            seat_strategies=[s.name for s in self.strategies],
            turns=turns,
            rolls=rolls,
            captures_made=self.captures_made[:],
            captures_suffered=self.captures_suffered[:],
            ranking=self.ranking[:],
            hit_turn_cap=hit_cap,
        )
