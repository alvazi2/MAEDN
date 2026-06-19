# Mensch ärgere Dich nicht — strategy simulation

A Python simulator for the board game *Mensch ärgere Dich nicht* (base rules
only). It runs many automated 4-player games to study questions like **how long
a game lasts** and **whether playing mean beats playing nice**.

## Setup

```bash
python3 -m pip install -r requirements.txt
```

(`numpy`, `pandas`, `matplotlib` are likely already present; this also adds
`jupyter` and `pytest`.)

## Quick start

```python
from maedn import run_tournament
from maedn import analysis

df = run_tournament(
    ["mean", "nice", "random", "defensive"],  # one strategy per seat
    n_games=2000,
    seed=42,
)

print(analysis.win_rates(df))          # win rate per strategy
print(analysis.game_length_stats(df))  # avg / median game length
```

## Strategies

| name        | behaviour                                                        |
|-------------|------------------------------------------------------------------|
| `mean`      | capture whenever possible (most-advanced opponent first)         |
| `nice`      | avoid capturing; only capture when no other move is legal         |
| `random`    | uniform choice among legal moves (baseline)                       |
| `runahead`  | always advance the figure that is furthest along                  |
| `defensive` | get figures out of home, rescue threatened figures, stay compact  |
| `optimal`   | composite from strategy guides: capture, deploy, rescue, spread    |

Each of the four seats is configured independently, so any mix is allowed
(`["mean", "mean", "nice", "nice"]` for a 2-vs-2 study, etc.).

## Findings

Headline results from `notebooks/research.ipynb`. Exact numbers depend on the
strategies, seeds and game counts used, so treat these as indicative — re-run the
notebook to reproduce them.

- **Aggression pays off.** In a four-way game of `mean`, `nice`, `random` and
  `defensive`, the capturing `mean` strategy wins roughly **half** the games
  (~48%), while the pacifist `nice` lands near its fair 25% share and the weaker
  strategies trail. Captures correlate with winning.
- **Games are long.** A four-player game runs on the order of **~300 turns** on
  average (a turn = one player's full go), with a long right tail driven by
  figures being sent home.
- **First-player advantage is small but real, and strategy-dependent.** With all
  four seats playing the *same* strategy (to isolate turn order), seat 0 always
  does best, but the edge over the fair 25% is only ~**+0.1 to +1.8 pp**. It is
  statistically significant (chi-square) for decisive strategies like `runahead`
  and `nice`, and negligible for pure-luck `random` play.
- **"Spread out and play safe" does not pay off here.** The `optimal` strategy
  implements the composite advice from popular strategy guides (capture, deploy,
  rescue threatened figures, develop all figures evenly). It does *not* beat pure
  `mean` — in a 4-way mix it lands around or just below its fair share, and
  head-to-head against `mean` it loses clearly. The simulation's verdict is that
  the guides' aggression advice holds, but **racing the leading figure beats
  spreading evenly**, consistent with `runahead` outperforming `defensive`.

## Layout

```
maedn/            engine + analysis package
  constants.py    board geometry
  state.py        GameState + position helpers
  moves.py        legal-move generation incl. forced-move rules
  strategies.py   the five player strategies
  game.py         single-game loop + GameResult
  simulation.py   run_tournament -> pandas DataFrame
  analysis.py     aggregation + matplotlib plot helpers
notebooks/
  research.ipynb  high-level orchestration + visualisations
tests/            pytest rule + determinism tests
```

The authoritative game rules are documented in `CLAUDE.md`.

## Running tests

```bash
pytest -q
```

## Research notebook

```bash
jupyter notebook notebooks/research.ipynb
```
