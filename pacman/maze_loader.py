
from __future__ import annotations

import io
import logging
from typing import Any
from contextlib import redirect_stdout
from random import Random
from pacman.maze import Direction, Maze

logger = logging.getLogger(__name__)

WALL_BITS: dict[Direction, int] = {
    Direction.NORTH: 1,
    Direction.EAST: 2,
    Direction.SOUTH: 4,
    Direction.WEST: 8,
}


class MazeGenerationError(Exception):
    """Raised when a generated maze cannot be used by the game."""


class MazeGeneration:
    """Decode and validate output from the external maze generator."""

    @staticmethod
    def decode_cells(raw: Any, width: int,
                     height: int) -> list[list[set[Direction]]]:
        """Convert the generator's integer cells into blocked directions."""
        if not isinstance(raw, list) or len(raw) != height:
            raise MazeGenerationError("generated maze has the wrong height")
        if width <= 0 or height <= 0:
            raise MazeGenerationError("maze dimensions must be positive")
        if len(raw) != height:
            raise MazeGenerationError("generated maze has the wrong height")

        decoded: list[list[set[Direction]]] = []
        for row in raw:
            if not isinstance(raw, list) or len(raw) != height:
                raise MazeGenerationError("generated maze has "
                                          "the wrong height")

            if len(row) != width:
                raise MazeGenerationError("generated maze has the wrong width")
            decoded_row: list[set[Direction]] = []
            for value in row:
                if type(value) is not int or not 0 <= value <= 15:
                    raise MazeGenerationError(
                        "maze cells must be integers between 0 and 15")
                decoded_row.append({
                    direction
                    for direction, bit in WALL_BITS.items()
                    if value & bit
                })
            decoded.append(decoded_row)
        return decoded

    def build_once(self, width: int, height: int, seed: int) -> Maze:
        """Generate one maze and reject malformed or disconnected output."""
        try:
            from mazegenerator import MazeGenerator
        except ImportError:
            raise MazeGenerationError("package 'mazegenerator' "
                                      "is not installed")
        try:
            with redirect_stdout(io.StringIO()):
                generator = MazeGenerator(
                    size=(width, height),
                    perfect=False,
                    seed=seed,
                )
            walls = self.decode_cells(generator.maze, width, height)
            maze = Maze(width, height, walls)
            if not maze.is_connected():
                raise MazeGenerationError(
                    "generated maze has unreachable areas")
            return maze
        except MazeGenerationError:
            raise
        except Exception as error:
            raise MazeGenerationError(
                f"maze generator failed: {error}") from error

    def generate_maze(self, width: int, height: int, seed: int | None,
                      rng: Random) -> Maze:
        """Generate a maze, retrying random seeds when no seed was supplied."""
        seeds = [seed] if seed is not None else [
            rng.randint(1, 2**31 - 1) for _ in range(3)
        ]
        last_error = "unknown generation error"

        for attempt_seed in seeds:
            logger.info("generating maze with seed %d", attempt_seed)
            try:
                return self.build_once(width, height, attempt_seed)
            except MazeGenerationError as error:
                last_error = str(error)
                logger.warning("maze generation failed with seed %d: %s",
                               attempt_seed, error)

        raise MazeGenerationError(last_error)
