"""Aggregation and plotting helpers for tournament result DataFrames.

These keep the research notebook high-level: it calls these functions rather than
doing pandas/matplotlib work inline. Every function takes the wide per-game
DataFrame produced by :func:`maedn.simulation.run_tournament`.
"""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd

from . import constants as C


def seat_long(df: pd.DataFrame) -> pd.DataFrame:
    """Reshape the wide per-game frame to one row per (game, seat).

    Columns: ``game``, ``seat``, ``strategy``, ``made``, ``suffered``,
    ``is_winner`` (this seat won), ``turns``.
    """
    parts = []
    for seat in range(C.N_PLAYERS):
        parts.append(
            pd.DataFrame(
                {
                    "game": df["game"],
                    "seat": seat,
                    "strategy": df[f"seat_{seat}"],
                    "made": df[f"made_{seat}"],
                    "suffered": df[f"suffered_{seat}"],
                    "is_winner": df["winner_seat"] == seat,
                    "turns": df["turns"],
                }
            )
        )
    return pd.concat(parts, ignore_index=True)


def win_rates(df: pd.DataFrame) -> pd.Series:
    """Win probability per strategy.

    Computed per seat-game: the fraction of games-as-a-seat that a strategy won.
    This is robust to a strategy occupying several seats and is ~0.25 for every
    strategy when all four are identical.
    """
    long = seat_long(df)
    return long.groupby("strategy")["is_winner"].mean().sort_values(ascending=False)


def game_length_stats(df: pd.DataFrame) -> pd.Series:
    """Summary statistics of game length (turns until the first finisher)."""
    return df["turns"].describe()


def captures_by_strategy(df: pd.DataFrame) -> pd.DataFrame:
    """Mean captures made and suffered per strategy."""
    long = seat_long(df)
    return long.groupby("strategy")[["made", "suffered"]].mean()


def seat_win_rates(df: pd.DataFrame) -> pd.Series:
    """Win probability per seat index (turn order: seat 0 plays first)."""
    return df["winner_seat"].value_counts(normalize=True).sort_index()


# -- seat / turn-order advantage --------------------------------------------

#: z-values for the normal-approximation confidence interval.
_Z = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}


def seat_advantage(df: pd.DataFrame, confidence: float = 0.95) -> pd.DataFrame:
    """Per-seat win rate with a binomial confidence interval.

    Seat 0 plays first. The interval is the normal (Wald) approximation
    ``p ± z*sqrt(p(1-p)/n)``; with thousands of games it is tight enough to read
    a first-player advantage straight off the table. Columns: ``games``,
    ``wins``, ``win_rate``, ``ci_low``, ``ci_high``.

    To isolate the *pure positional* effect, run this on games where every seat
    uses the same strategy (see :func:`first_player_experiment`); otherwise the
    spread also reflects which strategies happened to sit where.
    """
    z = _Z.get(confidence, 1.960)
    n = len(df)
    rows = []
    for seat in range(C.N_PLAYERS):
        wins = int((df["winner_seat"] == seat).sum())
        p = wins / n if n else 0.0
        half = z * (p * (1 - p) / n) ** 0.5 if n else 0.0
        rows.append(
            {
                "games": n,
                "wins": wins,
                "win_rate": p,
                "ci_low": max(0.0, p - half),
                "ci_high": min(1.0, p + half),
            }
        )
    out = pd.DataFrame(rows)
    out.index.name = "seat"
    return out


def seat_uniformity_test(df: pd.DataFrame) -> dict:
    """Chi-square goodness-of-fit test of wins-per-seat against a uniform 25%.

    Returns the ``chi2`` statistic, degrees of freedom, the 0.05 critical value
    (7.815 for 3 dof), and a ``significant`` flag. ``significant=True`` means the
    seat differences are unlikely to be chance, i.e. turn order matters.
    """
    counts = (
        df["winner_seat"].value_counts().reindex(range(C.N_PLAYERS), fill_value=0)
    )
    n = len(df)
    expected = n / C.N_PLAYERS
    chi2 = float(((counts - expected) ** 2 / expected).sum()) if expected else 0.0
    crit = 7.815  # chi-square 0.05 critical value, dof = N_PLAYERS - 1 = 3
    return {
        "chi2": chi2,
        "dof": C.N_PLAYERS - 1,
        "critical_0.05": crit,
        "significant": chi2 > crit,
    }


def first_player_experiment(
    strategy: str = "random", n_games: int = 20000, seed: int = 0
) -> pd.DataFrame:
    """Run a controlled tournament where all four seats use ``strategy``.

    With identical strategies, seat rotation is moot and any win-rate difference
    between seats is purely the turn-order (first-player) effect. Returns the raw
    per-game DataFrame; pass it to :func:`seat_advantage` /
    :func:`seat_uniformity_test`.
    """
    from .simulation import run_tournament  # local import avoids an import cycle

    return run_tournament(
        [strategy] * C.N_PLAYERS, n_games=n_games, seed=seed, rotate_seats=False
    )


# -- plot helpers -----------------------------------------------------------


def _ax(ax: Optional[plt.Axes]) -> plt.Axes:
    return ax if ax is not None else plt.subplots()[1]


def plot_length_hist(df: pd.DataFrame, ax: Optional[plt.Axes] = None, bins: int = 40):
    """Histogram of game length (turns)."""
    ax = _ax(ax)
    ax.hist(df["turns"], bins=bins, color="steelblue", edgecolor="white")
    mean = df["turns"].mean()
    ax.axvline(mean, color="crimson", linestyle="--", label=f"mean = {mean:.1f}")
    ax.set_xlabel("game length (turns)")
    ax.set_ylabel("number of games")
    ax.set_title("Distribution of game length")
    ax.legend()
    return ax


def plot_win_rates(df: pd.DataFrame, ax: Optional[plt.Axes] = None):
    """Bar chart of win rate per strategy, with the 25% fair baseline."""
    ax = _ax(ax)
    rates = win_rates(df)
    rates.plot(kind="bar", ax=ax, color="mediumseagreen", edgecolor="white")
    ax.axhline(1 / C.N_PLAYERS, color="grey", linestyle="--", label="fair share (25%)")
    ax.set_ylabel("win rate")
    ax.set_title("Win rate per strategy")
    ax.legend()
    return ax


def plot_mean_vs_nice(df: pd.DataFrame, ax: Optional[plt.Axes] = None):
    """Direct win-rate comparison of the 'mean' and 'nice' strategies."""
    ax = _ax(ax)
    rates = win_rates(df)
    pair = rates.reindex(["mean", "nice"]).dropna()
    pair.plot(kind="bar", ax=ax, color=["firebrick", "royalblue"], edgecolor="white")
    ax.axhline(1 / C.N_PLAYERS, color="grey", linestyle="--", label="fair share (25%)")
    ax.set_ylabel("win rate")
    ax.set_title("Mean vs. Nice")
    ax.legend()
    return ax


def plot_seat_advantage(
    df: pd.DataFrame, ax: Optional[plt.Axes] = None, confidence: float = 0.95
):
    """Win rate by seat (turn order) with confidence-interval error bars.

    Bars whose interval clears the 25% line are a statistically real advantage.
    """
    ax = _ax(ax)
    adv = seat_advantage(df, confidence=confidence)
    yerr = [adv["win_rate"] - adv["ci_low"], adv["ci_high"] - adv["win_rate"]]
    ax.bar(
        adv.index,
        adv["win_rate"],
        yerr=yerr,
        capsize=5,
        color="goldenrod",
        edgecolor="white",
    )
    ax.axhline(1 / C.N_PLAYERS, color="grey", linestyle="--", label="fair share (25%)")
    ax.set_xticks(range(C.N_PLAYERS))
    ax.set_xlabel("seat (0 = plays first)")
    ax.set_ylabel("win rate")
    ax.set_title("Turn-order advantage")
    ax.legend()
    return ax


def plot_captures_vs_winrate(df: pd.DataFrame, ax: Optional[plt.Axes] = None):
    """Scatter of mean captures made per strategy against its win rate."""
    ax = _ax(ax)
    rates = win_rates(df)
    caps = captures_by_strategy(df)["made"]
    joined = pd.concat([caps, rates.rename("win_rate")], axis=1).dropna()
    ax.scatter(joined["made"], joined["win_rate"], color="purple")
    for name, row in joined.iterrows():
        ax.annotate(name, (row["made"], row["win_rate"]),
                    textcoords="offset points", xytext=(5, 5))
    ax.set_xlabel("mean captures made per game")
    ax.set_ylabel("win rate")
    ax.set_title("Aggression vs. success")
    return ax
