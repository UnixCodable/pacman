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
| `src/session.py` | `GameSession`: **the only object you really talk to** |
| `src/game.py` | `GameState` (the enum you switch on) and the per-level `Game` you read |
| `src/maze.py` | `Maze` (walls) and `Direction` (NORTH, EAST, SOUTH, WEST) |
| `src/cheats.py` | `Cheat` (the enum of cheats) |
| `src/highscores.py` | `HighscoreTable` (load, qualifies, add, save) |
| `src/config.py` | `Config`, already validated; passed to your `run()` |
| `src/maze_loader.py` | `MazeGenerationError` (the maze-generation error to handle) |
| `scripts/demo_terminal.py` | The game playable in a terminal (to learn the rules by playing) |

Run `python3 scripts/demo_terminal.py --config config.json` for 5 minutes before you write any code. You will understand the game much faster by playing it.

---

## 2. Entry point

`src/app.py` loads your function. Create `src/ui/__init__.py` containing:

```python
def run(config: Config) -> int:
    """Open the window, run the game, return 0 on a normal exit."""
```

Rules:
- Signature exactly `run(config) -> int`, with `Config` from `src.config`.
- Return 0 on a normal exit. Return 1 after showing a fatal message.
- Do not wrap everything in `try/except Exception`. `src/app.py` already converts unexpected errors into a clean one-line message (no traceback).
- During development set `PACMAN_DEBUG=1` to see tracebacks.

---

## 3. API reference

### 3.1 Creating and ending a game

| Call | Result |
|---|---|
| `GameSession(config)` | Builds the whole run and generates **level 1**. Can raise `MazeGenerationError` (catch it, show the message, go back to the menu). It may also raise `ValueError` for invalid configuration or level settings; configuration normally prevents this. |
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

Imports: `from src.maze import Direction`, `from src.cheats import Cheat`.

### 3.2.1 How to use `update()` correctly

The UI must call **`session.update(dt)` once per rendered frame** while a
session exists. `dt` is the elapsed time in seconds since the previous frame:

```python
now = time.monotonic()
dt = now - last_frame_time
last_frame_time = now
session.update(dt)
```

Use `time.monotonic()`, not wall-clock time, because the clock must not jump
when the system time changes. Reset `last_frame_time` when creating a new
session or returning from a non-game screen so the first frame does not
include time spent in a menu.

`GameSession.update(dt)` performs this sequence:

1. Detects that the current level was won or lost.
2. During the two-second level transition, counts down
   `session.transition_left` and creates the next `Game` when it reaches zero.
3. Otherwise delegates `dt` to `session.game.update(dt)`.
4. Detects a level win, final victory, or game over after the game advances.

Always call the session method rather than calling `session.game.update(dt)`
from the UI. Calling the inner method bypasses level transitions and can leave
the UI displaying a completed level indefinitely. Read `session.game` again
after every update because a new `Game` object replaces it when the next level
starts.

The engine clamps negative values to zero and limits a single update to
`0.25` seconds, so a paused debugger or a delayed frame cannot move the game
an excessive distance. Still pass the measured `dt`; do not pass a fixed
value such as `1 / 60`. The update method does not return a value. Inspect
`session.state`, `session.score`, `session.lives`, and the other read-only
properties after the call.

Do not call `update()` more than once for the same frame. A typical loop is:

```python
while window_is_open:
    handle_events()                 # may call set_direction/toggle_pause
    if session is not None:
        session.update(dt)          # exactly once
    draw(session)                   # read state after updating
    present_frame()
```

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
| `ghost.move_interval` | normal seconds per cell (the engine applies `FRIGHTENED_SLOWDOWN` from `src.ghost` while frightened) |

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

from src.config import Config
from src.game import GameState
from src.maze_loader import MazeGenerationError
from src.session import GameSession


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

`session.state` is a `GameState` (`from src.game import GameState`):

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

## 6. Rendering example: how the UI uses the engine

The renderer should be a one-way adapter:

1. Read the current `session` and `session.game`.
2. Convert maze coordinates into pixels.
3. Draw the maze, collectibles, player, ghosts, and HUD.
4. Never change positions, score, lives, or collectibles itself.

The following example is deliberately graphics-library neutral. Replace
`draw_rectangle`, `draw_circle`, `draw_text`, `poll_events`, and
`present_frame` with calls from the chosen UI toolkit.

```python
import time

from src.cheats import Cheat
from src.game import GameState
from src.maze import Direction
from src.maze_loader import MazeGenerationError
from src.session import GameSession


CELL = 32
WALL_COLOR = (30, 70, 220)
DOT_COLOR = (255, 220, 150)
PLAYER_COLOR = (255, 220, 0)
FRIGHTENED_COLOR = (40, 100, 255)


def cell_center(cell: tuple[int, int]) -> tuple[int, int]:
    """Convert a maze cell to the centre pixel used by the renderer."""
    x, y = cell
    return (x * CELL + CELL // 2, y * CELL + CELL // 2)


def draw_level(session: GameSession) -> None:
    """Draw one frame from current engine state."""
    game = session.game
    maze = game.maze

    clear_screen((0, 0, 0))

    # Draw every cell and its walls. A wall is on a cell edge.
    for x, y in maze.all_cells():
        left, top = x * CELL, y * CELL
        if maze.is_blocked(x, y):
            draw_rectangle((left, top, CELL, CELL), (60, 60, 60))
            continue

        for direction in Direction:
            if not maze.has_wall(x, y, direction):
                continue
            if direction is Direction.NORTH:
                draw_line((left, top), (left + CELL, top), WALL_COLOR)
            elif direction is Direction.EAST:
                draw_line(
                    (left + CELL, top),
                    (left + CELL, top + CELL),
                    WALL_COLOR,
                )
            elif direction is Direction.SOUTH:
                draw_line(
                    (left, top + CELL),
                    (left + CELL, top + CELL),
                    WALL_COLOR,
                )
            else:
                draw_line((left, top), (left, top + CELL), WALL_COLOR)

    for cell in game.pacgums:
        draw_circle(cell_center(cell), radius=3, color=DOT_COLOR)

    for cell in game.super_pacgums:
        draw_circle(cell_center(cell), radius=7, color=DOT_COLOR)

    for ghost in game.ghosts:
        color = FRIGHTENED_COLOR if ghost.frightened else ghost_color(
            ghost.personality
        )
        if ghost.is_respawning:
            color = dim(color)
        draw_ghost(cell_center(ghost.position), color, ghost.direction)

    draw_player(
        cell_center(game.player.position),
        PLAYER_COLOR,
        game.player.direction,
    )

    draw_text(
        f"SCORE {session.score}   LIVES {session.lives}   "
        f"LEVEL {session.level_number}/{session.total_levels}   "
        f"TIME {session.time_left:05.1f}",
        position=(8, maze.height * CELL + 8),
    )

    if session.cheats.enabled:
        draw_text("CHEAT MODE", position=(8, maze.height * CELL + 32))


def draw_frame(session: GameSession | None, screen: str) -> None:
    """Choose the application screen and draw it."""
    if screen == "menu":
        draw_menu()
    elif screen == "highscores":
        draw_highscores()
    elif screen == "playing" and session is not None:
        draw_level(session)
        if session.state is GameState.PAUSED:
            draw_overlay("PAUSED")
        elif session.state is GameState.LEVEL_WON:
            draw_overlay(f"LEVEL {session.level_number} COMPLETE")
    elif screen == "end" and session is not None:
        draw_level(session)
        title = (
            "VICTORY!" if session.state is GameState.VICTORY
            else "GAME OVER"
        )
        draw_overlay(f"{title}  SCORE {session.score}")
        if session.error:
            draw_text(session.error, position=(8, 8))
```

### Event-to-engine mapping

The UI translates toolkit events into engine calls. It does not implement
movement or collision rules:

```python
def handle_game_event(event, session: GameSession) -> str | None:
    """Forward one input event and return an optional user message."""
    if event.is_key_pressed("up"):
        session.set_direction(Direction.NORTH)
    elif event.is_key_pressed("right"):
        session.set_direction(Direction.EAST)
    elif event.is_key_pressed("down"):
        session.set_direction(Direction.SOUTH)
    elif event.is_key_pressed("left"):
        session.set_direction(Direction.WEST)
    elif event.is_key_pressed("pause"):
        session.toggle_pause()
    elif event.is_key_pressed("cheat-mode"):
        return f"Cheat mode: {session.toggle_cheat_mode()}"
    elif event.is_key_pressed("skip-level"):
        return session.apply_cheat(Cheat.SKIP_LEVEL)
    return None
```

Use the same event handler for keyboard, controller, or touch input. The
important rule is that a direction is sent once when the input changes; the
engine buffers the requested turn until it is possible.

### Complete frame order

Use this order so input is responsive and the frame displays the newest state:

```python
last = time.monotonic()

while window_is_open:
    now = time.monotonic()
    dt = now - last
    last = now

    for event in poll_events():
        if event.is_quit():
            return 0
        if screen == "playing" and session is not None:
            handle_game_event(event, session)
        else:
            handle_menu_or_highscore_event(event)

    if session is not None and screen == "playing":
        session.update(dt)
        if session.state in (GameState.GAME_OVER, GameState.VICTORY):
            screen = "end"

    draw_frame(session, screen)
    present_frame()
```

When a game starts, set `last = time.monotonic()` immediately after creating
the session. This prevents menu time from being applied to the first game
frame. Keep calling `session.update(dt)` while `LEVEL_WON` is displayed; that
is how the automatic two-second transition reaches the next level.

## 7. Step-by-step order for creating the complete UI

Implement the UI in this order:

1. **Create the package.** Add `src/ui/__init__.py` with `run(config) -> int`.
2. **Create a window.** Choose the resolution, frame rate, fonts, and colours.
3. **Create application screens.** Start with `menu`, `playing`, `end`, and
   `highscores`. These are UI states, separate from `GameState`.
4. **Start a session.** On Start, call `GameSession(config)`. Catch
   `MazeGenerationError`, display the error, and remain on the menu.
5. **Add the clock.** Store `time.monotonic()` and calculate `dt` once per
   frame. Reset it whenever a new session starts.
6. **Forward input.** Map directions to `set_direction`, pause to
   `toggle_pause`, and cheat controls to the cheat methods.
7. **Update once.** Call `session.update(dt)` once per frame while playing.
8. **Render the level.** Read `session.game` after updating, then draw walls,
   dots, super dots, ghosts, player, and HUD from the read-only properties.
9. **Render overlays.** Use `session.state` for `PAUSED` and `LEVEL_WON`.
   Switch to the end screen for `GAME_OVER` or `VICTORY`.
10. **Handle end results.** Run the high-score qualification flow in section
    8 exactly once when the session first reaches an end state.
11. **Add navigation.** Let the player return to the menu, start a new
    session, view highscores, or quit. A finished session must not be reused.
12. **Test each feature.** Test movement, buffered turns, pause, level
    transitions, losing lives, victory, maze-generation failure, cheats,
    high-score saving, and a failed high-score write.

Do not add game rules to the UI. If the UI needs a new rule or value, add it
to the engine API first, then expose it as a read-only value for rendering.

## 8. High-score file: complete UI workflow

The configured path is `config.highscore_filename`. The UI owns the
high-score screen, but `HighscoreTable` owns loading, sorting, validation, and
saving.

### 8.1 Display existing scores

Load the table when entering the high-score screen or when opening the menu:

```python
from src.highscores import HighscoreTable

table = HighscoreTable(config.highscore_filename)

for rank, entry in enumerate(table.entries, start=1):
    draw_text(f"{rank:2}. {entry.name:<10} {entry.score:>6}")
```

The constructor loads the JSON file. A missing, malformed, or invalid file is
reported through logging and produces an empty table, so the screen can still
be displayed. Do not read or write the JSON file directly.

### 8.2 Decide whether a score qualifies

When the session reaches `GAME_OVER` or `VICTORY`, do this once:

```python
table = HighscoreTable(config.highscore_filename)

if session.cheats.used:
    end_message = "Cheats were used: score not saved"
elif table.qualifies(session.score):
    screen = "name_entry"
else:
    end_message = "Score did not reach the top 10"
```

Cheat use disqualifies the score even if it would otherwise qualify. Keep the
table object alive while the name-entry screen is open so the UI can add to
the same loaded table.

### 8.3 Collect and add the player name

Limit the text input to ten characters in the UI, then add the score:

```python
from src.highscores import sanitize_name

clean_name = sanitize_name(name_input)
rank = table.add(clean_name, session.score)

if rank == -1:
    end_message = "This score is no longer in the top 10"
else:
    end_message = f"New high score: rank {rank + 1}"
```

`sanitize_name()` keeps only ASCII letters, digits, and spaces, trims the
result to ten characters, and uses `"Player"` when the result is empty.
`add()` sorts the entries and keeps at most ten scores.

### 8.4 Save and report failures

After a successful `add()`, save explicitly and check the return value:

```python
if not table.save():
    end_message = "Could not save the highscores file"
```

Saving is atomic and creates the parent directory when possible. A `False`
return means the UI must tell the player that the score was not persisted; do
not show a success message. The in-memory table can still be displayed during
the current run.

### 8.5 Recommended high-score screen state machine

```text
MENU ──Highscores──► HIGHSCORES ──Back──► MENU
  │
  └─Start──► PLAYING ──end──► RESULT
                         │
                         ├─cheats used──► RESULT ──Continue──► MENU
                         ├─not qualified► RESULT ──Continue──► MENU
                         └─qualified────► NAME_ENTRY
                                            │
                                            ├─Confirm──► add + save
                                            └─Cancel───► do not save
```

Do not call `table.add()` repeatedly while the player types. Call it once
when the name is confirmed, then call `save()` once. If the player cancels,
discard the table or reload it before the next high-score screen.

---

