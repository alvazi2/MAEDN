"""Tests for the analysis helpers, focused on seat-advantage statistics."""

import maedn.constants as C
from maedn import analysis
from maedn.simulation import run_tournament


def test_seat_advantage_shape_and_bounds():
    df = run_tournament(["mean", "nice", "random", "defensive"], n_games=200, seed=0)
    adv = analysis.seat_advantage(df)
    assert list(adv.index) == list(range(C.N_PLAYERS))
    # Win rates sum to 1 (exactly one winner per game) and CIs bracket them.
    assert abs(adv["win_rate"].sum() - 1.0) < 1e-9
    assert (adv["ci_low"] <= adv["win_rate"]).all()
    assert (adv["win_rate"] <= adv["ci_high"]).all()


def test_uniformity_test_keys():
    df = run_tournament(["random"] * 4, n_games=300, seed=0)
    test = analysis.seat_uniformity_test(df)
    assert set(test) == {"chi2", "dof", "critical_0.05", "significant"}
    assert test["dof"] == C.N_PLAYERS - 1
    assert isinstance(test["significant"], bool)


def test_random_play_has_no_significant_seat_advantage():
    # Pure-luck play should not show a statistically significant turn-order edge.
    df = analysis.first_player_experiment(strategy="random", n_games=5000, seed=1)
    assert not analysis.seat_uniformity_test(df)["significant"]
