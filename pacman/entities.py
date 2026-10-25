"""Moving entities of the game."""

from pacman.maze import Coordinate, Direction, Maze


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
        # 1. Try to take the buffered turn.
        if (self.desired is not None
                and maze.can_move(self.x, self.y, self.desired)):
            self.direction = self.desired
            self.desired = None

        # 2. Keep going in the current direction.
        if (self.direction is not None
                and maze.can_move(self.x, self.y, self.direction)):
            self.x += self.direction.dx
            self.y += self.direction.dy
            return True

        # 3. Blocked: stand still.
        self.direction = None
        return False
