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

Each of the four seats is configured independently, so any mix is allowed
(`["mean", "mean", "nice", "nice"]` for a 2-vs-2 study, etc.).

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
