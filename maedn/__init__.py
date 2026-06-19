"""maedn -- a simulator for *Mensch ärgere Dich nicht* (base rules).

Public entry points:

* :func:`maedn.simulation.run_tournament` -- run many games -> pandas DataFrame
* :mod:`maedn.analysis` -- aggregation and plotting helpers
* :class:`maedn.game.Game` / :class:`maedn.game.GameResult` -- single game
* :data:`maedn.strategies.STRATEGIES` -- available player strategies
"""

from .game import Game, GameResult
from .simulation import run_tournament
from .strategies import STRATEGIES, make_strategy

__all__ = [
    "Game",
    "GameResult",
    "run_tournament",
    "STRATEGIES",
    "make_strategy",
]
