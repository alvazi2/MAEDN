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


def plot_seat_advantage(df: pd.DataFrame, ax: Optional[plt.Axes] = None):
    """Win rate by seat (turn order) to expose first-player advantage."""
    ax = _ax(ax)
    seat_win_rates(df).plot(kind="bar", ax=ax, color="goldenrod", edgecolor="white")
    ax.axhline(1 / C.N_PLAYERS, color="grey", linestyle="--", label="fair share (25%)")
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
