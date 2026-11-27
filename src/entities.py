"""Moving entities of the game."""

from src.maze import Coordinate, Direction, Maze


class Player:
    """Pac-Man: moves cell by cell and keeps going until blocked."""

    def __init__(self, start: Coordinate) -> None:
        """Place the player on a start cell, standing still."""
        self.start = start
        self.x, self.y = start
        self.direction: Direction | None = None
        self.desired: Direction | None = None

    @property
    def position(self) -> Coordinate:
        """Return the current cell as (x, y)."""
        return self.x, self.y

    def reset(self) -> None:
        """Return to the start cell and forget all movement."""
        self.x, self.y = self.start
        self.direction = None
        self.desired = None

    def step(self, maze: Maze) -> bool:
        """Advance one cell.

        Args:
            maze: The maze the player moves in.

        Returns:
            True if the player moved, False otherwise.
        """

        moved = False

        # 1. Reach the target cell.
        if (self.direction is not None
                and maze.can_move(self.x, self.y, self.direction)):
            self.x += self.direction.dx
            self.y += self.direction.dy
            moved = True

        # 2. Choose the next direction from the new cell.
        if (self.desired is not None
                and maze.can_move(self.x, self.y, self.desired)):
            self.direction = self.desired
            self.desired = None

        direction = self.direction
        if (direction is not None
                and not maze.can_move(self.x, self.y, direction)):
            # 3. Blocked: stand still.
            self.direction = None

        return moved
