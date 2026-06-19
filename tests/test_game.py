"""Game-loop and determinism tests."""

import random

import maedn.constants as C
from maedn.game import Game
from maedn.simulation import run_tournament
from maedn.strategies import make_strategy


def _strategies(names):
    return [make_strategy(n) for n in names]


def test_game_produces_a_winner():
    rng = random.Random(0)
    result = Game(_strategies(["mean", "nice", "random", "defensive"]), rng).play()
    assert 0 <= result.winner < C.N_PLAYERS
    assert not result.hit_turn_cap
    assert result.turns > 0


def test_winner_has_all_figures_home():
    rng = random.Random(1)
    game = Game(_strategies(["runahead"] * 4), rng)
    result = game.play()
    # The recorded winner must actually have every figure in its goal lane.
    assert game.state.is_finished(result.winner)


def test_determinism_same_seed():
    def run():
        rng = random.Random(123)
        return Game(_strategies(["mean", "nice", "random", "runahead"]), rng).play()

    a, b = run(), run()
    assert a.winner == b.winner
    assert a.turns == b.turns
    assert a.captures_made == b.captures_made


def test_tournament_reproducible_and_shaped():
    kw = dict(strategy_assignment=["mean", "nice", "random", "defensive"],
              n_games=50, seed=7)
    df1 = run_tournament(**kw)
    df2 = run_tournament(**kw)
    assert df1.equals(df2)
    assert len(df1) == 50
    assert df1["winner_strategy"].isin(
        ["mean", "nice", "random", "defensive"]
    ).all()


def test_identical_strategies_are_seat_fair():
    # With four identical strategies and seat rotation, no seat should be wildly
    # advantaged beyond the known first-player edge.
    df = run_tournament(["random"] * 4, n_games=400, seed=3)
    seat_rates = df["winner_seat"].value_counts(normalize=True)
    assert abs(seat_rates.mean() - 0.25) < 1e-9
    assert seat_rates.max() < 0.40  # first-player edge exists but is modest
