"""Run many games and collect the results into a tidy pandas DataFrame."""

from __future__ import annotations

import random

import pandas as pd

from . import constants as C
from .game import Game
from .strategies import make_strategy


def _rotate(seq: list, by: int) -> list:
    by %= len(seq)
    return seq[by:] + seq[:by]


def run_tournament(
    strategy_assignment: list[str],
    n_games: int,
    seed: int = 0,
    rotate_seats: bool = True,
    continue_to_full_ranking: bool = False,
    max_turns: int = 2000,
) -> pd.DataFrame:
    """Play ``n_games`` games and return one row per game.

    ``strategy_assignment`` is the per-seat list of strategy names (length 4),
    e.g. ``["mean", "nice", "random", "defensive"]``. When ``rotate_seats`` is
    true the assignment is rotated by one seat each game so that, over the run,
    every strategy spends an equal share of games in each seat -- this cancels
    the starting-position / turn-order advantage. The actual seating used is
    recorded per game so the seat effect can still be studied.

    Returns columns: ``game``, ``turns``, ``rolls``, ``hit_turn_cap``,
    ``winner_seat``, ``winner_strategy``, ``seat_0..seat_3`` (strategy names),
    ``made_0..made_3`` and ``suffered_0..suffered_3`` (captures per seat).
    """
    if len(strategy_assignment) != C.N_PLAYERS:
        raise ValueError(
            f"strategy_assignment needs {C.N_PLAYERS} entries, "
            f"got {len(strategy_assignment)}"
        )

    master = random.Random(seed)
    rows = []
    for g in range(n_games):
        seating = _rotate(strategy_assignment, g) if rotate_seats else list(
            strategy_assignment
        )
        strategies = [make_strategy(name) for name in seating]
        game_rng = random.Random(master.random())
        result = Game(
            strategies,
            game_rng,
            continue_to_full_ranking=continue_to_full_ranking,
            max_turns=max_turns,
        ).play()

        row = {
            "game": g,
            "turns": result.turns,
            "rolls": result.rolls,
            "hit_turn_cap": result.hit_turn_cap,
            "winner_seat": result.winner,
            "winner_strategy": result.winner_strategy,
        }
        for seat in range(C.N_PLAYERS):
            row[f"seat_{seat}"] = seating[seat]
            row[f"made_{seat}"] = result.captures_made[seat]
            row[f"suffered_{seat}"] = result.captures_suffered[seat]
        rows.append(row)

    return pd.DataFrame(rows)
