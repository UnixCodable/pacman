"""Text-mode version of the whole game, to try the engine without graphics.

Run from the project root:
    python3 scripts/demo_terminal.py
Options:
    --config FILE     play with a real config file (overrides the options
                      below it, except --highscores)
    --levels N        number of levels (default 3)
    --size WxH        maze size of every level (default 16x16)
    --time SECONDS    time limit per level (default 90)
    --lives N         starting lives (default 3)
    --highscores FILE where scores are saved (default demo_highscores.json)
    --snapshot        print one frame and exit
Keys: w a s d / arrows = move   p = pause   q = quit
      c = cheat mode on/off, then:
      1 invincible  2 freeze ghosts  3 speed  4 +life
      5 skip level  6 power-up       7 only 5 s left
Legend: @ you, . pacgum, O super-pacgum, blocks = the 42.
Ghosts: C chaser, A ambusher, U unpredictable, W wanderer
(lowercase when edible, ~ while waiting at home).
"""
from sys import argv
import os
import random
import select
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.cheats import Cheat  # noqa: E402
from src.config import (  # noqa: E402
 ConfigError, ConfigParser)
from src.game import GameState  # noqa: E402
from src.highscores import HighscoreTable, sanitize_name  # noqa: E402
from src.maze import Direction  # noqa: E402
from src.maze_loader import MazeGenerationError  # noqa: E402
from src.session import GameSession  # noqa: E402

MOVES = {
    b"w": Direction.NORTH, b"a": Direction.WEST,
    b"s": Direction.SOUTH, b"d": Direction.EAST,
    b"\x1b[A": Direction.NORTH, b"\x1b[D": Direction.WEST,
    b"\x1b[B": Direction.SOUTH, b"\x1b[C": Direction.EAST,
}
CHEATS = {
    b"1": Cheat.INVINCIBLE, b"2": Cheat.FREEZE_GHOSTS,
    b"3": Cheat.SPEED_BOOST, b"4": Cheat.EXTRA_LIFE,
    b"5": Cheat.SKIP_LEVEL, b"6": Cheat.POWER_UP, b"7": Cheat.LOW_TIME,
}


def render(session: GameSession, message: str = "") -> str:
    """Draw the current level and the HUD as text."""
    game = session.game
    maze = game.maze
    w, h = maze.width, maze.height
    canvas = [[" "] * (2 * w + 1) for _ in range(2 * h + 1)]
    for x, y in maze.all_cells():
        cx, cy = 2 * x + 1, 2 * y + 1
        if maze.is_blocked(x, y):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    canvas[cy + dy][cx + dx] = "█"
            continue
        for d in Direction:
            if maze.has_wall(x, y, d):
                canvas[cy + d.dy][cx + d.dx] = "#"
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            canvas[cy + dy][cx + dx] = "+"
    for x, y in game.pacgums:
        canvas[2 * y + 1][2 * x + 1] = "."
    for x, y in game.super_pacgums:
        canvas[2 * y + 1][2 * x + 1] = "O"
    for ghost in game.ghosts:
        letter = ghost.personality[0].upper()
        if ghost.is_respawning:
            letter = "~"
        elif ghost.frightened:
            letter = letter.lower()
        gx, gy = ghost.position
        canvas[2 * gy + 1][2 * gx + 1] = letter
    px, py = game.player.position
    canvas[2 * py + 1][2 * px + 1] = "@"
    lines = ["".join(row) for row in canvas]
    cheats = session.cheats
    flags = "".join([
        "I" if cheats.invincible else "", "F" if cheats.freeze_ghosts else "",
        "S" if cheats.speed_boost else ""])
    lines.append(
        f"SCORE {session.score}  LIVES {session.lives}  "
        f"LEVEL {session.level_number}/{session.total_levels}  "
        f"TIME {session.time_left:5.1f}  [{session.state.name}]")
    extra = f"CHEAT MODE [{flags}]" if cheats.enabled else ""
    power = ""
    if game.ghosts_edible:
        power = f"  POWER {game.power_time_left:3.1f}s"
    lines.append(f"{extra}{power}  {message}".rstrip())
    return "\n".join(lines)


def read_key() -> bytes:
    """Return pending key bytes without blocking (empty if none)."""
    ready, _, _ = select.select([sys.stdin], [], [], 0.02)
    return os.read(sys.stdin.fileno(), 8) if ready else b""


def play(session: GameSession) -> None:
    """Real-time loop until the run ends or the user quits."""
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    message, message_until, last = "", 0.0, time.monotonic()
    try:
        tty.setcbreak(fd)
        while True:
            now = time.monotonic()
            dt, last = now - last, now
            key = read_key()
            if key in (b"q", b"\x03"):
                return
            if key == b"p":
                session.toggle_pause()
            elif key == b"c":
                on = session.toggle_cheat_mode()
                message, message_until = f"cheat mode {on}", now + 2
            elif key in CHEATS:
                message = session.apply_cheat(CHEATS[key])
                message_until = now + 2
            elif key in MOVES:
                session.set_direction(MOVES[key])
            session.update(dt)
            if now > message_until:
                message = ""
            sys.stdout.write("\x1b[H\x1b[2J" + render(session, message) + "\n")
            sys.stdout.flush()
            if session.state in (GameState.GAME_OVER, GameState.VICTORY):
                return
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def finish(session: GameSession, path: str) -> None:
    """Show the result and save the score (like the game-over screen)."""
    if session.state not in (GameState.GAME_OVER, GameState.VICTORY):
        return
    title = "VICTORY!" if session.state is GameState.VICTORY else "GAME OVER"
    print(f"\n{title}  final score: {session.score}")
    if session.error:
        print(f"(stopped early: {session.error})")
    table = HighscoreTable(path)
    if session.cheats.used:
        print("Cheats were used: score not saved.")
    elif table.qualifies(session.score):
        name = sanitize_name(input("Your name (max 10 characters): "))
        table.add(name, session.score)
        if not table.save():
            print("Could not save the highscores file.")
    print("\nHIGHSCORES")
    for i, entry in enumerate(table.entries, 1):
        print(f"{i:2}. {entry.name:<10} {entry.score:>6} pts")


def main() -> int:
    """Parse options, build a session and run it."""

    try:
        config = ConfigParser().load_config(argv[1])
    except ConfigError as error:
        print(f"Error: {error}")
        return 1
    try:
        session = GameSession(config, rng=random.Random())
    except MazeGenerationError as error:
        print(f"Error: {error}")
        return 1
    # if args.snapshot:
    #     print(render(session))
    #     return 0
    if not sys.stdin.isatty():
        print("Error: this demo needs a terminal")
        return 1
    play(session)
    # finish(session, args.highscores)
    return 0


if __name__ == "__main__":
    sys.exit(main())
