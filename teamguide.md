# Pac-Man: Guide for the UI and Graphics Developer

This guide is for the teammate who builds the **graphics library, the window, the menus and the screens**. The game engine (rules, mazes, ghosts, score, timer, cheats, highscores, config, error handling) is already written and tested. You never touch game rules. You draw the game and forward the player's keys.

---

## 1. The 60-second picture

```
 config.json ──► pac-man.py ──► pacman/app.py ──► pacman/ui  (YOU)
                                                    │
                                   ┌────────────────┴───────────────┐
                                   ▼                                ▼
                             GameSession  (engine)           HighscoreTable
                       level, score, lives, timer,        load / qualifies / add / save
                       maze, player, ghosts, cheats
```

Every frame, your code does three things:

```
1. keys  ->  session.set_direction(d) / toggle_pause() / apply_cheat(c)
2. time  ->  session.update(dt)        # dt = seconds since the previous frame
3. draw  ->  read the session, draw it with your graphics library
```

The engine never draws. Your code never moves anyone, adds score or checks a collision.

---

## 2. Where to start (in this order)

1. **Run the engine without graphics** and get a feel for the game:
   ```
   python3 scripts/demo_terminal.py --config config.json   # playable in the terminal
   python3 scripts/autoplay.py                              # self-check, all PASS
   ```
2. **Read `scripts/ui_demo.py`** (about 200 lines). It is a complete example of a "UI" that uses only the public API. Run it: `python3 scripts/ui_demo.py out.png` (needs `pip install pillow`) and open the image. Your job is the same thing with your graphics library.
3. **Implement the 5 drawing calls** the demo needs on top of your library: `clear`, `line`, `rect`, `circle`, `text`. This is the `Backend` class in the demo.
4. **Copy `GameView.draw`** from the demo. It already draws the HUD, maze, pacgums, ghosts and player correctly.
5. **Create `pacman/ui/__init__.py` with `run(config) -> int`** (skeleton in section 5). `app.py` finds and calls it. Until it exists, the game prints "graphical interface is not available".
6. Add menus and screens (section 6), then smooth movement (section 8).

---

## 3. What you read (never write)

`session` is a `GameSession`. `game = session.game` is the **current level**.

> Read `session.game` again **every frame**. A new `Game` object replaces it when a level changes, so never keep a reference to it.

| To draw | Read |
|---|---|
| Score, lives, level, timer | `session.score`, `.lives`, `.level_number`, `.total_levels`, `.time_left` (seconds, float) |
| Maze size | `game.maze.width`, `game.maze.height` |
| Walls | `maze.has_wall(x, y, Direction.NORTH)` (also `EAST`, `SOUTH`, `WEST`) |
| The "42" | `maze.is_blocked(x, y)`: draw those cells as solid blocks |
| Pacgums | `game.pacgums` (a set of `(x, y)`) |
| Super pacgums | `game.super_pacgums` (a set of `(x, y)`) |
| Player | `game.player.position` as `(x, y)`, and `game.player.direction` (a `Direction` or `None`) |
| Ghosts | `game.ghosts`: a list. For each: `ghost.position`, `ghost.personality`, `ghost.frightened`, `ghost.is_respawning` |
| Power-up | `game.ghosts_edible` (bool) and `game.power_time_left` (seconds) |
| Cheat badge | `session.cheats.enabled` |
| Which screen | `session.state` |
| Fatal later-level error | `session.error` (a string or `None`) |

**Coordinates:** `(x, y)`, with `x` growing to the right and `y` growing **downward**, starting at `(0, 0)` in the top-left cell. Positions are whole cells.

**Ghost looks** (suggested, all yours to change):
- Normal: one colour per `personality` (`"chaser"`, `"ambusher"`, `"unpredictable"`, `"wanderer"`).
- `ghost.frightened` is True: draw it blue (edible). Flash it when `game.power_time_left` is below about 2 s.
- `ghost.is_respawning` is True: it is waiting at home after being eaten (or not yet released). Draw it grey, or hide it.

---

## 4. What you call

| Player action | Call |
|---|---|
| Arrow keys / WASD | `session.set_direction(Direction.NORTH)` (`EAST`, `SOUTH`, `WEST`) |
| Pause key | `session.toggle_pause()` |
| Cheat-mode key | `on = session.toggle_cheat_mode()` returns the new on/off value |
| Cheat keys | `msg = session.apply_cheat(Cheat.X)` returns a text to show on screen |
| Every frame | `session.update(dt)` |

`Direction` comes from `pacman.maze`, `Cheat` from `pacman.cheats`.

**Cheats** (only work while cheat mode is on; show `msg` for about 2 seconds):

| `Cheat.` | Effect |
|---|---|
| `INVINCIBLE` | toggle: ghosts cannot hurt you |
| `FREEZE_GHOSTS` | toggle: ghosts stop moving |
| `SPEED_BOOST` | toggle: player is faster |
| `EXTRA_LIFE` | +1 life |
| `SKIP_LEVEL` | win the current level at once |
| `POWER_UP` | ghosts become edible |
| `LOW_TIME` | at most 10 s left (to test the timeout) |

Calls are safe at any time. During a level change, or after the game ends, direction and pause are simply ignored.

---

## 5. Skeleton of `pacman/ui/__init__.py`

This runs today with the engine (it was checked with flake8 and mypy `--strict`). Replace the marked lines with your window code.

```python
"""Graphical interface of the Pac-Man game."""

import time

from pacman.config import Config
from pacman.game import GameState
from pacman.highscore import HighscoreTable
from pacman.maze import Direction
from pacman.maze_loader import MazeGenerationError
from pacman.session import GameSession


def run(config: Config) -> int:
    """Open the window, play until the player quits, return an exit code."""
    try:
        session = GameSession(config)       # level 1 is generated here
    except MazeGenerationError as error:
        print(f"Error: {error}")            # or show it in your menu
        return 1

    last = time.monotonic()
    running = True
    while running:                          # <- your window's main loop
        now = time.monotonic()
        dt, last = now - last, now          # real elapsed time

        # 1. keys: translate your library's key events, for example:
        #    session.set_direction(Direction.EAST)
        #    session.toggle_pause()

        # 2. time
        session.update(dt)

        # 3. drawing: HUD, maze, pacgums, ghosts, player, overlays

        if session.state in (GameState.GAME_OVER, GameState.VICTORY):
            table = HighscoreTable(config.highscore_filename)
            if not session.cheats.used and table.qualifies(session.score):
                table.add("Name", session.score)   # name typed by the player
                table.save()
            running = False                 # or show the highscore screen
    return 0
```

Rules for `run`:
- Signature is exactly `run(config) -> int`. Return `0` on a normal exit.
- Do not catch every exception. `app.py` already turns unexpected errors into a clean message with exit code 1 (no traceback).
- Set the environment variable `PACMAN_DEBUG=1` to see the full traceback while developing.

---

## 6. Screens and what the state means

`session.state` is a `GameState` (import from `pacman.game`):

| State | What to show |
|---|---|
| `PLAYING` | The game |
| `PAUSED` | The game frozen, with a "PAUSED" overlay |
| `LEVEL_WON` | "Level complete" for about 2 s. The next level then starts **by itself** (the state returns to `PLAYING`). Do nothing |
| `GAME_OVER` | Final score, name entry if it qualifies, highscores |
| `VICTORY` | Same as `GAME_OVER`, with a win message (all levels done) |

Also handle:
- **Main menu** (yours): Start, Highscores, Quit. Starting creates a new `GameSession(config)`. Create a new session for every new game.
- **Highscore screen:** `HighscoreTable(config.highscore_filename).entries` is a list of `HighscoreEntry(name, score)`, already sorted best first and limited to 10.
- **Name entry:** call `table.qualifies(score)` first. Then `table.add(name, score)` and `table.save()`. `add` cleans the name (letters, digits and spaces, max 10 characters, empty becomes "Player"). `save()` returns `False` if the disk write failed, so tell the player.
- **Cheated runs:** `session.cheats.used` is True once any cheat was applied. We do **not** save those scores (show "cheats used, score not saved").
- **`session.error`:** if it is not `None`, the run ended early because a later maze could not be generated. Show it on the game-over screen.

---

## 7. Game rules you may want to display

- Pacgums on every open cell. Four **super pacgums** in the corners start the power-up (8 s, ghosts edible).
- A level is won when every pacgum and super pacgum is eaten.
- Eating a ghost gives points. The eaten ghost goes home and waits about 7 s.
- Ghosts are released one by one, 2 s apart.
- Each level has a time limit (`config.level_max_time`). When it runs out the player **loses a life**, everyone goes back to the start, the clock refills and eaten pacgums stay eaten.
- Score and lives carry over to the next level. The maze, pacgums and timer start fresh.
- Level 1 uses the fixed `seed` from the config (the same maze every time). Later levels are random.
- The player stands still at the start until the first direction key.

---

## 8. Making it look smooth

The engine moves in whole cells: the player every 0.20 s and ghosts every 0.27 s. If you draw exactly the cell, movement looks jumpy. A purely visual fix, which needs **no engine change**:

- Remember each entity's previous cell.
- When its `position` changes, slide the drawn position from the old cell to the new one over the move interval.
- You can draw the player's mouth pointing along `player.direction`.

Pass the **real** elapsed time as `dt`. Very large values (window drag, breakpoint) are capped inside the engine, so nothing teleports.

**Window size:** read `maze.width` and `maze.height`, and compute the cell size from them so any maze fits the window. Do not hard-code it. Maze sizes come from the config (`MIN_SIZE` and `MAX_SIZE` in `pacman/config.py`, currently 5 and 50). **Please tell us the largest maze your window can show, and we will set `MAX_SIZE` to match.**

---

## 9. The config file (what `config.json` contains)

JSON with whole-line comments (`#` or `//`). Bad values fall back to defaults with a warning, so the game still starts.

| Key | Meaning | Default |
|---|---|---|
| `highscore_filename` | where scores are stored | `highscores.json` |
| `levels` | list of `{"width": N, "height": N}`, padded to 10 levels | 10 levels of 15x15 |
| `lives` | starting lives, 1 to 99 | 3 |
| `points_per_pacgum` | points per pacgum | 10 |
| `points_per_super_pacgum` | points per super pacgum | 50 |
| `points_per_ghost` | points per ghost eaten | 200 |
| `seed` | maze seed of level 1, at least 1 | 42 |
| `level_max_time` | seconds per level, 5 to 3600 | 90 |

`pacgum` is accepted but ignored. Your code receives the already-checked `Config` object, so there is nothing to validate on your side.

---

## 10. Rules of the road

**Do**
- Treat the session as read-only for drawing.
- Re-read `session.game` each frame.
- Keep the UI free of game rules. If a rule needs to change, ask the engine owner.
- Follow the subject's constraints: type hints, PEP 257 docstrings, flake8, mypy with the subject's flags. Run `make lint` before every commit.

**Don't**
- Don't write to `game.pacgums`, `game.player.position`, `session.score` and so on.
- Don't call `game.update` directly. Always go through `session.update`.
- Don't keep your own copy of lives, score or timer. Read them each frame.
- Don't let an exception reach the terminal as a traceback.

---

## 11. Checklist for the UI side

- [ ] `pacman/ui/__init__.py` exposes `run(config) -> int`
- [ ] The five drawing calls work (clear, line, rect, circle, text)
- [ ] Maze with walls, the filled "42" blocks, pacgums and super pacgums
- [ ] HUD: score, lives, level n/N, time left, cheat badge, power-up bar
- [ ] Player and four ghost colours, blue when edible, grey while waiting
- [ ] Keys: arrows/WASD, pause, cheat mode on/off, cheat keys, quit
- [ ] Overlays: PAUSED, LEVEL COMPLETE, GAME OVER, VICTORY
- [ ] Menu, highscore screen, name entry
- [ ] Message from `apply_cheat` shown for about 2 s
- [ ] Window closing at any moment exits cleanly
- [ ] `make lint` passes

---

## 12. Who owns what

| Area | Owner |
|---|---|
| Config, error handling, maze loading, player, ghosts, scoring, levels, timer, cheats, highscore logic, game state | Engine developer |
| Graphics library, window, menus, screens, key handling, animation | UI developer (you) |
| Packaging (PyInstaller, itch.io), README, project-management notes | to be agreed |

**To agree together:**
1. The largest maze the window can show (sets `MAX_SIZE`).
2. Which keys are used for cheats.
3. Where the highscore file lives in a packaged build.
4. Who writes which README sections.

If something you need is missing from the API (for example a new thing to display), ask the engine developer. It is usually one extra line to expose.