# UI Integration Guide: Pac-Man engine -> your graphics


## 0. The idea in five lines

1. The engine (`GameSession`) holds the whole game: rules, mazes, ghosts, score, timer, cheats.
2. Your UI **reads** the session and **draws** it. It also **forwards key presses** to it.
3. Every frame you call `session.update(dt)` once, with the real elapsed time.
4. The UI never moves anything, scores anything or checks a collision.
5. Screens (menu, highscores, name entry) are yours. The engine only tells you which *game* state it is in.

```
 key events ──► YOUR UI ──► session.set_direction / toggle_pause / apply_cheat
                  │
 each frame ──────┼──► session.update(dt)
                  │
                  └──► read session.* ──► draw with your graphics library
```

---

## 1. Files you can rely on

| File | What it gives you |
|---|---|
| `pacman/session.py` | `GameSession`: **the only object you really talk to** |
| `pacman/game.py` | `GameState` (the enum you switch on) and the per-level `Game` you read |
| `pacman/maze.py` | `Maze` (walls) and `Direction` (NORTH, EAST, SOUTH, WEST) |
| `pacman/cheats.py` | `Cheat` (the enum of cheats) |
| `pacman/highscore.py` | `HighscoreTable` (load, qualifies, add, save) |
| `pacman/config.py` | `Config`, already validated; passed to your `run()` |
| `pacman/maze_loader.py` | `MazeGenerationError` (the only error you must catch) |
| `scripts/ui_demo.py` | A complete example UI drawing six frames to a PNG. **Read it.** |
| `scripts/demo_terminal.py` | The game playable in a terminal (to learn the rules by playing) |

Run `python3 scripts/demo_terminal.py --config config.json` for 5 minutes before you write any code. You will understand the game much faster by playing it.

---

## 2. Entry point

`app.py` calls your function. Create `pacman/ui/__init__.py` containing:

```python
def run(config: Config) -> int:
    """Open the window, run the game, return 0 on a normal exit."""
```

Rules:
- Signature exactly `run(config) -> int`, with `Config` from `pacman.config`.
- Return 0 on a normal exit. Return 1 after showing a fatal message.
- Do not wrap everything in `try/except Exception`. `app.py` already converts unexpected errors into a clean one-line message (no traceback).
- During development set `PACMAN_DEBUG=1` to see tracebacks.

---

## 3. API reference

### 3.1 Creating and ending a game

| Call | Result |
|---|---|
| `GameSession(config)` | Builds the whole run and generates **level 1**. Can raise `MazeGenerationError` (catch it, show the message, go back to the menu). Takes a fraction of a second, so draw a "Generating..." frame first if you like. |
| New game | Create a **new** `GameSession(config)`. Never reuse a finished one. |
| Quit mid-game | Just drop the session. Nothing to save or clean up. |

### 3.2 Calls you make (the only ways to change the game)

| Call | When | Returns |
|---|---|---|
| `session.update(dt)` | **Every frame**, with `dt` in seconds (float) | nothing |
| `session.set_direction(Direction.X)` | On an arrow/WASD key press | nothing |
| `session.toggle_pause()` | On the pause key | nothing |
| `session.toggle_cheat_mode()` | On the cheat-mode key | `bool`: the new on/off value |
| `session.apply_cheat(Cheat.X)` | On a cheat key | `str`: a message to show for about 2 s |

Details that matter:
- **Call `update` in every screen state of a running session**, including `LEVEL_WON`, because the 2-second pause between levels is counted down inside `update`. When paused or finished, it is harmless and does nothing.
- `dt` must be the **real** time since the last frame. Do not pass a constant. The engine caps very large values, so a window drag or a breakpoint can't teleport anyone.
- `set_direction` remembers the **latest** direction as a request. If a turn isn't possible yet, the player keeps going and turns as soon as it is possible. So call it on key *press*, not every frame, and don't try to be clever.
- At the start of every level the player stands still until the first direction key.
- `set_direction` and `toggle_pause` are silently ignored during the level-change pause and after the game ended. You don't need to check.
- `apply_cheat` works only while cheat mode is on, and returns "Cheat mode is off" otherwise. Show whatever string it returns.

Imports: `from pacman.maze import Direction`, `from pacman.cheats import Cheat`.

### 3.3 What you read (never write)

`session` is a `GameSession`. `game = session.game` is the **current level**.

> **Read `session.game` again every frame.** A brand-new `Game` object replaces it at each level change. If you store it in a variable, you will draw the old level.

**On the session**

| Read | Type | Use |
|---|---|---|
| `session.state` | `GameState` | which screen/overlay (section 5) |
| `session.score` | int | HUD |
| `session.lives` | int | HUD |
| `session.level_number` | int, starts at 1 | HUD "LEVEL 3/10" |
| `session.total_levels` | int | HUD |
| `session.time_left` | float, seconds | HUD timer |
| `session.cheats.enabled` | bool | "CHEAT MODE" badge |
| `session.cheats.invincible`, `.freeze_ghosts`, `.speed_boost` | bool | show which cheats are active |
| `session.cheats.used` | bool | True once any cheat was applied (decides if the score is saved) |
| `session.error` | `str` or `None` | set if a later maze could not be built; show on the end screen |
| `session.game` | `Game` | the level |

**On the level (`game`)**

| Read | Type | Use |
|---|---|---|
| `game.maze` | `Maze` | walls (below) |
| `game.pacgums` | `set[(x, y)]` | small dots |
| `game.super_pacgums` | `set[(x, y)]` | big dots (the four corners) |
| `game.player.position` | `(x, y)` | player cell |
| `game.player.direction` | `Direction` or `None` | which way to point the mouth. `None` means standing still |
| `game.ghosts` | list of `Ghost` | four ghosts (below) |
| `game.ghosts_edible` | bool | a power-up is active |
| `game.power_time_left` | float, seconds | power-up bar, flashing |
| `game.player_interval` | float, seconds per cell | for smooth movement (section 8) |

**On the maze (`game.maze`)**

| Read | Meaning |
|---|---|
| `maze.width`, `maze.height` | size in cells |
| `maze.has_wall(x, y, Direction.NORTH)` | is there a wall on that side of the cell (also `EAST`, `SOUTH`, `WEST`) |
| `maze.is_blocked(x, y)` | the cell belongs to the **"42"**: fully walled, draw it as a solid block |
| `maze.all_cells()` | iterate every `(x, y)` |

**On each ghost**

| Read | Meaning |
|---|---|
| `ghost.position` | `(x, y)` cell |
| `ghost.personality` | `"chaser"`, `"ambusher"`, `"unpredictable"`, `"wanderer"`: choose the colour from it |
| `ghost.frightened` | edible: draw blue |
| `ghost.is_respawning` | waiting at home (not yet released, or recently eaten): draw grey/dim; it is harmless |
| `ghost.direction` | last move direction (or `None`), for eye direction |
| `ghost.move_interval` | seconds per cell (multiply by `FRIGHTENED_SLOWDOWN` from `pacman.ghost` while frightened) |

**Coordinates:** `(x, y)`, `x` to the right, `y` **downward**, `(0, 0)` is the top-left cell. A cell is one maze square, and walls live on the **edges** of cells.

### 3.4 Highscores

```python
table = HighscoreTable(config.highscore_filename)
table.entries                 # list[HighscoreEntry]; .name, .score; best first, max 10
table.qualifies(score) -> bool
table.add(name, score) -> int # rank (0-based), or -1 if it did not qualify
table.save() -> bool          # False if the disk write failed (tell the player)
```

`HighscoreTable(...)` never raises: a missing or corrupt file just gives an empty table. `add` cleans the name for you (ASCII letters, digits and spaces, max 10 characters, empty becomes "Player"), so limit your text box to 10 characters and don't worry about the rest.

---

## 4. The main loop

```python
import time

from pacman.config import Config
from pacman.game import GameState
from pacman.maze_loader import MazeGenerationError
from pacman.session import GameSession


def run(config: Config) -> int:
    """Open the window and run the application."""
    # window = create_window(...)           # your graphics library
    screen = "menu"                         # menu | playing | end | highscores
    session: GameSession | None = None
    last = time.monotonic()

    while True:                             # your window's main loop
        now = time.monotonic()
        dt, last = now - last, now

        # 1. EVENTS: translate your library's events (section 7)
        # 2. UPDATE
        if session is not None:
            session.update(dt)
            if session.state in (GameState.GAME_OVER, GameState.VICTORY):
                screen = "end"
        # 3. DRAW (section 6): choose what to draw from `screen` and state
        # 4. present the frame; sleep or vsync to about 60 fps
    return 0
```

Starting a game from the menu:

```python
try:
    session = GameSession(config)
except MazeGenerationError as error:
    message = f"Could not build the maze: {error}"   # show in the menu
else:
    screen = "playing"
```

---

## 5. States and screens

`session.state` is a `GameState` (`from pacman.game import GameState`):

| State | When | Draw | Player can |
|---|---|---|---|
| `PLAYING` | normal play | the game | move, pause, cheats |
| `PAUSED` | after pause key | the game **plus** a "PAUSED" overlay | press pause again |
| `LEVEL_WON` | the last pacgum was eaten, for about 2 s | the game plus "LEVEL n COMPLETE" | nothing (don't need to do anything: the next level starts by itself and the state returns to `PLAYING`) |
| `GAME_OVER` | no lives left, or a later maze failed to build | end screen | enter name, go to menu |
| `VICTORY` | the last level was completed | end screen with a win message | same |

Your own screens:

```
MENU ──Start──► PLAYING ──(GAME_OVER/VICTORY)──► END
  │                                               │
  ├──Highscores──► HIGHSCORES                     ├─ qualifies? ─► NAME ENTRY ─► HIGHSCORES
  └──Quit                                         └─ otherwise ──────────────► MENU
```

**End screen logic** (run it once, when the state first becomes `GAME_OVER` or `VICTORY`):

```python
table = HighscoreTable(config.highscore_filename)
can_save = (not session.cheats.used) and table.qualifies(session.score)
# can_save True  -> ask for a name, then table.add(name, score); table.save()
# cheats used    -> show "Cheats were used: score not saved"
# no qualify     -> show the score and "not in the top 10"
# session.error  -> also show the error text
```

---

