
from collections import deque
from collections.abc import Iterator, Sequence
from enum import Enum

Coordinate = tuple[int, int]
WallGrid = Sequence[Sequence[set["Direction"]]]


class MazeError(ValueError):
    """Raised when a maze has invalid dimensions or wall data."""


class Direction(Enum):
    """A movement direction and its coordinate delta."""

    NORTH = (0, -1)
    EAST = (1, 0)
    SOUTH = (0, 1)
    WEST = (-1, 0)

    @property
    def dx(self) -> int:
        """Return the horizontal coordinate change."""
        return self.value[0]

    @property
    def dy(self) -> int:
        """Return the vertical coordinate change."""
        return self.value[1]

    @property
    def opposite(self) -> "Direction":
        """Return the direction pointing back to the current cell."""
        opposites = {
            Direction.NORTH: Direction.SOUTH,
            Direction.EAST: Direction.WEST,
            Direction.SOUTH: Direction.NORTH,
            Direction.WEST: Direction.EAST,
        }
        return opposites[self]


class Maze:
    """A rectangular maze whose cells contain blocked directions."""

    def __init__(self, width: int, height: int, walls: WallGrid) -> None:
        if width <= 0 or height <= 0:
            raise MazeError("maze dimensions must be positive")
        if len(walls) != height:
            raise MazeError("wall grid has the wrong height")
        if any(len(row) != width for row in walls):
            raise MazeError("wall grid has the wrong width")

        self.width = width
        self.height = height
        self.walls = [
            [set(cell_walls) for cell_walls in row]
            for row in walls
        ]
        self.entry: Coordinate = (0, 0)
        self.exit: Coordinate = (width - 1, height - 1)
        self.shortest_path = ""

    def in_bounds(self, x: int, y: int) -> bool:
        """Return whether a coordinate is inside the maze."""
        return 0 <= x < self.width and 0 <= y < self.height

    def has_wall(self, x: int, y: int, direction: Direction) -> bool:
        """Return whether a cell blocks movement in a direction."""
        if not self.in_bounds(x, y):
            raise MazeError("coordinate is outside the maze")
        return direction in self.walls[y][x]

    def can_move(self, x: int, y: int, direction: Direction) -> bool:
        """Return whether movement from a cell is possible."""
        if not self.in_bounds(x, y) or self.has_wall(x, y, direction):
            return False
        return self.in_bounds(x + direction.dx, y + direction.dy)

    def neighbors(self, x: int, y: int) -> list[Coordinate]:
        """Return all cells reachable in one move from a coordinate."""
        if not self.in_bounds(x, y):
            raise MazeError("coordinate is outside the maze")
        return [
            (x + direction.dx, y + direction.dy)
            for direction in Direction
            if self.can_move(x, y, direction)
        ]

    def all_cells(self) -> Iterator[Coordinate]:
        """Iterate over every cell as an ``(x, y)`` coordinate."""
        for y in range(self.height):
            for x in range(self.width):
                yield x, y

    def center(self) -> Coordinate:
        """Return the center cell."""
        return self.width // 2, self.height // 2

    def corners(self) -> tuple[Coordinate, Coordinate, Coordinate, Coordinate]:
        """Return the maze's four corner cells."""
        return (
            (0, 0),
            (self.width - 1, 0),
            (0, self.height - 1),
            (self.width - 1, self.height - 1),
        )

    def is_connected(self) -> bool:
        """Return whether every cell can be reached from the center."""
        start = self.center()
        visited = {start}
        pending = deque([start])
        while pending:
            cell = pending.popleft()
            for neighbor in self.neighbors(*cell):
                if neighbor not in visited:
                    visited.add(neighbor)
                    pending.append(neighbor)
        return len(visited) == self.width * self.height
