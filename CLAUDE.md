# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Python simulator for the board game *Mensch ärgere Dich nicht* (base rules only). It runs many
automated **4-player** games to produce statistical research data — average game length, win rates
per strategy (the headline question is *mean vs. nice*), capture counts, and turn-order advantage.
There is **no interactive/graphical game** and no human player; this is a batch simulation for
analysis. Reference material: `49324_Mensch_aergere_Dich_nicht_REISE_DE.pdf` (rules) and
`Mensch_ärgere_dich_nicht_4.svg.png` (board image).

## Commands

```bash
python3 -m pip install -r requirements.txt   # numpy, pandas, matplotlib, jupyter, pytest

pytest -q                                     # run all tests
pytest tests/test_moves.py -q                 # one test file
pytest tests/test_moves.py::test_capture_marks_opponent -q   # one test

# Execute the research notebook headless (writes outputs back in place):
cd notebooks && python3 -m jupyter nbconvert --to notebook --execute --inplace research.ipynb
```

Quick smoke run of the engine:

```python
from maedn import run_tournament
from maedn import analysis
df = run_tournament(["mean", "nice", "random", "defensive"], n_games=3000, seed=42)
print(analysis.win_rates(df), analysis.game_length_stats(df), sep="\n")
```

## Architecture

The package is named **`maedn`** (the repo directory name has an umlaut/hyphens and isn't a valid
Python identifier). The engine is pure, deterministic, and I/O-free; pandas/matplotlib live only in
the analysis layer and notebook. A root `conftest.py` puts the repo on `sys.path` so `import maedn`
works from tests and the notebook.

Data-flow / dependency order (each module imports only from those above it):

```
constants.py  → board geometry: TRACK_LEN=40, GOAL_LEN=4, N_PLAYERS=4, entry_offset()
state.py      → GameState: figures[player][figure] = progress; position helpers
moves.py      → Move dataclass + legal_moves(): base rules AND forced-move filtering
strategies.py → Strategy ABC + 5 strategies + STRATEGIES registry / make_strategy()
game.py       → Game (one game loop) → GameResult
simulation.py → run_tournament() → tidy per-game pandas DataFrame
analysis.py   → aggregations + matplotlib plot helpers (used by the notebook)
```

Key concepts that span multiple files:

- **Position encoding (`state.py`).** A figure's location is a *player-relative* `progress`:
  `HOME` (sentinel `-1`) on a B field; `0..39` on the shared track; `40..43` in the private goal
  lane. The shared track is the only place colors interact, so collisions/captures are detected by
  converting a track `progress` to an **absolute index** via `(entry_offset(player) + progress) % 40`.
  `absolute_index()` returns `None` for HOME and goal positions (they can't collide across colors).

- **Forced moves live in `moves.py`, not in strategies.** `legal_moves()` already applies the
  mandatory base rules — must enter on a 6 while figures wait on B, must first vacate an own-occupied
  A field, no overshooting the goal, one figure per field. Strategies therefore only ever choose among
  *genuinely free* options. If a forced rule can't be satisfied (e.g. the A figure is itself blocked),
  it falls back to all legal moves rather than deadlocking. **When adding/altering rules, do it here**,
  and keep `strategies.py` free of legality logic.

- **Strategies (`strategies.py`)** implement `choose(state, player, candidates, rng) -> Move`. They are
  stateless; ties are broken with the game's seeded `rng` so runs stay reproducible. The five:
  `mean` (capture-first), `nice` (capture-avoiding), `random`, `runahead` (advance furthest figure),
  `defensive` (enter figures, rescue threatened ones, stay compact). Register new ones in `STRATEGIES`.

- **Determinism.** Everything flows from a single seed. `run_tournament(seed=...)` spawns one
  independent `random.Random` per game from a master RNG, so results are fully reproducible — there is
  a determinism test asserting this; don't introduce unseeded randomness or wall-clock dependence.

- **Seat rotation (`simulation.py`).** Seat 0 plays first and has a real advantage. `run_tournament`
  rotates the strategy→seat assignment by one seat each game (`rotate_seats=True`) so every strategy
  spends an equal share of games in each seat, canceling that bias; the actual seating is recorded per
  game so the seat effect can still be measured. **Win rate is computed per seat-game** in
  `analysis.win_rates` (not per game), which stays correct when one strategy occupies several seats.

- **Game termination (`game.py`).** A game stops at the first player to get all four figures home
  (`continue_to_full_ranking=True` plays on for placings). A `max_turns` cap plus a per-turn roll cap
  guard against pathological loops from repeated 6s; `GameResult.hit_turn_cap` flags it (expected to be
  0 in normal runs — investigate if it isn't).

Only the **base rules** (documented below) are implemented — the *Spielvarianten* are intentionally
out of scope.

## Game rules (domain model)

These are the authoritative game rules, extracted from the rules PDF. They define the domain any
implementation must enforce. (The optional *Spielvarianten* / house rules are intentionally **not**
included here — implement only the base rules below unless asked otherwise.)

### Setup

- 2–4 players, each owning **4 figures** of one color (typically red, yellow, green, black).
- Board has three kinds of fields per color:
  - **A field** — the color's *start* field, where figures enter the track.
  - **B fields** — the *yard/home base* where figures wait out of play.
  - **a, b, c, d fields** — the color's 4 *goal* fields (the finish lane).
- White fields form the shared **track** (`Laufbahn`) that all figures traverse.
- At setup, each player places **1 figure on their A field** and the **other 3 on their B fields**.
- Youngest player starts; turns proceed **clockwise**.

### Movement

- On a turn the player rolls one die and moves a figure forward by that many fields, in arrow
  direction along the track.
- Own and opponent figures may be **jumped over**, but occupied fields are still **counted** when
  measuring the move.
- A field holds **at most one figure** at a time.
- With multiple figures on the track, the player chooses which one to move.
- A move must be legal (lands on a non-own-occupied field, respects the constraints below). If the
  chosen die value yields no legal move, the player must move a different figure; if no figure can
  move, the turn passes.

### Capturing (schlagen)

- If a figure ends its move exactly on a field occupied by an **opponent** figure, that opponent is
  **captured**: it returns to its color's B fields, and the moving figure takes the field.
- There is **no obligation to capture** (kein Schlagzwang) in the base rules.
- You can **never** capture your own figure — and since two figures cannot share a field, if your
  only landing spot is occupied by your own figure, you must move a different figure instead.

### Entering figures from B (the "6" rule)

- A figure on a B field can **only enter play with a rolled 6**, moving onto the A field.
- While any of your figures still wait on B fields, **your A field may not stay occupied** by your
  own figure — it must be vacated as soon as possible (move that figure onward).
- Rolling a **6**:
  - Grants an **extra roll** after the move. Another 6 grants another roll, and so on.
  - If figures remain on your B fields, the 6 **must** be used to bring a new figure onto A.
    - If A is occupied by your own figure, that figure must first be moved onward (with the 6).
    - If A is occupied by an **opponent** figure, it is captured and your new figure takes A.
  - If **no** figures remain on B, the 6 is used to move a figure 6 fields along the track, then roll
    again.
  - Exception: if a 6 brings your **last** figure into the goal, you do **not** roll again.

### Goal fields (a, b, c, d)

- After a figure has completed one full loop of the track, it advances into its color's goal fields.
- Goal fields are **counted individually** when moving in. From directly before the goal lane: a roll
  of 1 reaches field `a`, a 2 reaches `b`, etc.
- Figures already in the goal **may be jumped over** (base rule).
- You may **not** enter another color's goal fields.
- A figure can only move into a goal field with an **exactly fitting roll** (no overshooting).

### Winning

- The first player to bring **all 4 figures into their goal fields** wins. Remaining players may keep
  playing for subsequent placings.
