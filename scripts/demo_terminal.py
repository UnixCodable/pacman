"""Terminal demo: watch or steer Pac-Man on a real generated maze.

Usage (from the project root):
    python3 scripts/demo_terminal.py                # play with WASD / arrows
    python3 scripts/demo_terminal.py --auto         # watch a random walk
    python3 scripts/demo_terminal.py --snapshot     # print one frame and exit
Options: --size WxH (default 16x16)  --seed N (default 42)
Keys: w a s d or arrows = move, p = pause, q = quit.
"""

import argparse
import os
import random
import select
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pacman.game import Game, GameState  # noqa: E402
from pacman.maze import Direction, Maze  # noqa: E402
from pacman.maze_loader import (  # noqa: E402
    MazeGeneration, MazeGenerationError)

KEYS = {
    b"w": Direction.NORTH, b"a": Direction.WEST,
    b"s": Direction.SOUTH, b"d": Direction.EAST,
    b"\x1b[A": Direction.NORTH, b"\x1b[D": Direction.WEST,
    b"\x1b[B": Direction.SOUTH, b"\x1b[C": Direction.EAST,
}


def render(game: Game) -> str:
    """Draw the maze as text: '#' walls, '@' player, '█' the 42 blocks."""
    maze: Maze = game.maze
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
    px, py = game.player.position
    canvas[2 * py + 1][2 * px + 1] = "@"
    lines = ["".join(row) for row in canvas]
    arrow = game.player.direction.name if game.player.direction else "-"
    status = "PAUSED" if game.state is GameState.PAUSED else "PLAYING"
    lines.append(f"pos={game.player.position} moving={arrow} [{status}]")
    return "\n".join(lines)


def read_key() -> bytes:
    """Return pending key bytes without blocking (empty if none)."""
    ready, _, _ = select.select([sys.stdin], [], [], 0.02)
    return os.read(sys.stdin.fileno(), 8) if ready else b""


def play(game: Game, auto: bool) -> None:
    """Run the real-time loop until the user quits."""
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd) if not auto else None
    rng = random.Random(1)
    last = time.monotonic()
    ticks = 0
    try:
        if not auto:
            tty.setcbreak(fd)
        while True:
            now = time.monotonic()
            dt, last = now - last, now
            if auto:
                ticks += 1
                if ticks % 6 == 0:
                    game.set_direction(rng.choice(list(Direction)))
                time.sleep(0.03)
            else:
                key = read_key()
                if key in (b"q", b"\x03"):
                    return
                if key == b"p":
                    game.toggle_pause()
                elif key in KEYS:
                    game.set_direction(KEYS[key])
            game.update(dt)
            sys.stdout.write("\x1b[H\x1b[2J" + render(game) + "\n")
            sys.stdout.flush()
    except KeyboardInterrupt:
        return
    finally:
        if old is not None:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def main() -> int:
    """Parse options, build a real maze and run the demo."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", default="16x16")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--snapshot", action="store_true")
    args = parser.parse_args()
    try:
        width, height = (int(v) for v in args.size.lower().split("x"))
        maze = MazeGeneration().generate_maze(width, height, args.seed,
                                              random.Random())
    except ValueError:
        print("Error: --size must look like 16x16")
        return 1
    except MazeGenerationError as error:
        print(f"Error: {error}")
        return 1
    game = Game(maze)
    if args.snapshot:
        print(render(game))
        return 0
    if not sys.stdin.isatty() and not args.auto:
        print("Error: interactive mode needs a terminal (use --auto)")
        return 1
    play(game, args.auto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
