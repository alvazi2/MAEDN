"""Board geometry and game constants for *Mensch ärgere Dich nicht* (base rules).

The board is a shared circular track of ``TRACK_LEN`` fields. Each of the
``N_PLAYERS`` players enters the track at their own A field, walks the full loop,
then turns into a private lane of ``GOAL_LEN`` goal fields.

Positions are expressed as a player-relative ``progress`` value (see
:mod:`maedn.state`):

* ``HOME``           -- figure waits on a B field, not yet in play
* ``0 .. TRACK_LEN-1`` -- figure is on the shared track
* ``TRACK_LEN .. LAST_PROGRESS`` -- figure is on its goal fields a, b, c, d
"""

#: Number of fields on the shared circular track (classic board: 40).
TRACK_LEN = 40

#: Number of goal fields per colour (a, b, c, d).
GOAL_LEN = 4

#: Number of players / colours.
N_PLAYERS = 4

#: Figures per player.
N_FIGURES = 4

#: Sentinel ``progress`` value for a figure still waiting on its B fields.
HOME = -1

#: First ``progress`` value that lies inside the goal lane.
FIRST_GOAL_PROGRESS = TRACK_LEN

#: Highest legal ``progress`` value (the last goal field, ``d``).
LAST_PROGRESS = TRACK_LEN + GOAL_LEN - 1

#: ``progress`` of a freshly-entered figure sitting on its A field.
START_PROGRESS = 0

#: Die face that lets a figure enter play and grants an extra roll.
ENTRY_ROLL = 6


def entry_offset(player: int) -> int:
    """Absolute track index of ``player``'s A (start) field.

    Players are spaced evenly around the track, e.g. 0, 10, 20, 30 on the
    classic board.
    """
    return player * (TRACK_LEN // N_PLAYERS)
