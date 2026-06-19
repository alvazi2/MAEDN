"""Player strategies: how to choose among the legal moves on a turn.

Each strategy receives only genuinely free choices (the forced-move rules are
already applied in :mod:`maedn.moves`). Strategies are stateless and pick a move
given the current state; ties are broken with the game's seeded RNG so that runs
stay reproducible.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Callable

from . import constants as C
from .moves import Move
from .state import GameState


def _threatened(state: GameState, player: int, progress: int) -> bool:
    """True if an own figure at track ``progress`` is within an opponent's reach.

    Heuristic: any opponent figure on the shared track sitting 1..6 fields behind
    (same travel direction) could capture it on a suitable roll. Goal-lane
    turn-offs are ignored, which slightly over-counts danger -- fine for a
    defensive heuristic.
    """
    abs_i = GameState.absolute_index(player, progress)
    if abs_i is None:
        return False  # HOME or in the goal lane: unreachable by opponents
    for opp in range(C.N_PLAYERS):
        if opp == player:
            continue
        for opp_progress in state.figures[opp]:
            abs_j = GameState.absolute_index(opp, opp_progress)
            if abs_j is None:
                continue
            gap = (abs_i - abs_j) % C.TRACK_LEN
            if 1 <= gap <= 6:
                return True
    return False


def _pick(moves: list[Move], key: Callable[[Move], float], rng: random.Random) -> Move:
    """Return the move maximising ``key``, breaking ties with ``rng``."""
    best = max(key(m) for m in moves)
    tied = [m for m in moves if key(m) == best]
    return rng.choice(tied)


class Strategy(ABC):
    """Abstract policy for selecting one move from the legal candidates."""

    #: Human-readable name used in result tables and the registry.
    name: str = "base"

    @abstractmethod
    def choose(
        self,
        state: GameState,
        player: int,
        candidates: list[Move],
        rng: random.Random,
    ) -> Move:
        ...

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"{type(self).__name__}()"


class MeanStrategy(Strategy):
    """Aggressive: capture whenever possible, hitting the most-advanced opponent."""

    name = "mean"

    def choose(self, state, player, candidates, rng):
        captures = [m for m in candidates if m.is_capture]
        if captures:
            # Captured opponent's progress (higher = more painful to lose).
            return _pick(
                captures, lambda m: state.figures[m.captured[0]][m.captured[1]], rng
            )
        return _pick(candidates, lambda m: m.to_progress, rng)


class NiceStrategy(Strategy):
    """Friendly: avoid capturing; only capture when no other move is legal."""

    name = "nice"

    def choose(self, state, player, candidates, rng):
        peaceful = [m for m in candidates if not m.is_capture]
        pool = peaceful if peaceful else candidates
        return _pick(pool, lambda m: m.to_progress, rng)


class RandomStrategy(Strategy):
    """Baseline: pick uniformly among the legal moves."""

    name = "random"

    def choose(self, state, player, candidates, rng):
        return rng.choice(candidates)


class RunAheadStrategy(Strategy):
    """Greedy front-runner: always advance the figure that is furthest along."""

    name = "runahead"

    def choose(self, state, player, candidates, rng):
        # Prefer moving the most-advanced figure; tie-break on landing square.
        return _pick(candidates, lambda m: (m.from_progress, m.to_progress), rng)


class DefensiveStrategy(Strategy):
    """Cautious: get figures out of home, rescue threatened figures, stay compact."""

    name = "defensive"

    def choose(self, state, player, candidates, rng):
        entries = [m for m in candidates if m.is_entry]
        if entries:
            return rng.choice(entries)

        # Move a currently-threatened figure, preferring a move to a safe square.
        rescues = [
            m
            for m in candidates
            if m.from_progress != C.HOME
            and _threatened(state, player, m.from_progress)
        ]
        if rescues:
            return _pick(
                rescues,
                lambda m: 0 if _threatened(state, player, m.to_progress) else 1,
                rng,
            )

        # Otherwise advance the rearmost figure to keep a compact formation.
        return _pick(candidates, lambda m: -m.from_progress, rng)


class OptimalStrategy(Strategy):
    """Composite play following a published strategy guide (bayern3.de).

    The guide's actionable rules, mapped to a 4-player game (its social /
    colour-choice / psychological tips don't translate to engine moves):

    * **Capture whenever you can** (rule 3).
    * **Keep your figures out of reach** -- aim for a >6-field lead so a pursuer
      can't hit you (rule 5); rescue a figure that has fallen into danger.
    * **Race the leading figure** -- push the most-advanced figure fastest
      (rule 7) rather than bunching figures up where one roll threatens several
      (rule 6).

    Priority order (the forced enter-on-6 / vacate-A rules are already applied
    upstream, so this only orders the genuinely free choices):

    1. **Capture** the most-advanced opponent when possible.
    2. **Rescue** a currently-threatened figure to a safe square; among those,
       move the most-advanced one.
    3. **Race**: advance a figure, preferring a safe landing square and, among
       equally safe moves, the most-advanced (front-running) figure.

    It is "optimal" only in the sense of following the guide's recommended
    tactics; it is a heuristic, not a game-theoretic optimum.
    """

    name = "optimal"

    def choose(self, state, player, candidates, rng):
        # 1. Capture the most-advanced opponent (rule 3).
        captures = [m for m in candidates if m.is_capture]
        if captures:
            return _pick(
                captures, lambda m: state.figures[m.captured[0]][m.captured[1]], rng
            )

        # 2. Rescue a figure that is within an opponent's reach (rule 5),
        #    preferring a destination that is itself safe.
        rescues = [
            m
            for m in candidates
            if m.from_progress != C.HOME
            and _threatened(state, player, m.from_progress)
        ]
        if rescues:
            safe = [m for m in rescues if not _threatened(state, player, m.to_progress)]
            return _pick(safe or rescues, lambda m: m.from_progress, rng)

        # 3. Otherwise race the leading figure (rule 7) to a safe square (rule 5).
        return _pick(
            candidates,
            lambda m: (
                0 if _threatened(state, player, m.to_progress) else 1,
                m.from_progress,
            ),
            rng,
        )


#: Registry mapping strategy name -> class, for selection by string.
STRATEGIES: dict[str, type[Strategy]] = {
    cls.name: cls
    for cls in (
        MeanStrategy,
        NiceStrategy,
        RandomStrategy,
        RunAheadStrategy,
        DefensiveStrategy,
        OptimalStrategy,
    )
}


def make_strategy(name: str) -> Strategy:
    """Instantiate a strategy by its registry ``name``."""
    try:
        return STRATEGIES[name]()
    except KeyError:
        raise ValueError(
            f"unknown strategy {name!r}; choose from {sorted(STRATEGIES)}"
        ) from None
