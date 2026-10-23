"""Maze data structure used by the game (independent of any generator)."""

from collections import deque
from collections.abc import Iterator, Sequence
from enum import Enum

Coordinate = tuple[int, int]


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
        return _OPPOSITES[self]


_OPPOSITES = {
    Direction.NORTH: Direction.SOUTH,
    Direction.EAST: Direction.WEST,
    Direction.SOUTH: Direction.NORTH,
    Direction.WEST: Direction.EAST,
}

WallGrid = Sequence[Sequence[set[Direction]]]


class Maze:
    """A rectangular maze; each cell holds the set of blocked sides."""

    def __init__(self, width: int, height: int, walls: WallGrid) -> None:
        """Validate sizes and wall consistency, then store a copy."""
        if width <= 0 or height <= 0:
            raise MazeError("maze dimensions must be positive")
        if len(walls) != height:
            raise MazeError("wall grid has the wrong height")
        if any(len(row) != width for row in walls):
            raise MazeError("wall grid has the wrong width")
        self.width = width
        self.height = height
        self.walls = [[set(cell) for cell in row] for row in walls]
        self.validate()

    def validate(self) -> None:
        """Raise MazeError if two neighbouring cells disagree on a wall."""
        for x, y in self.all_cells():
            for d in Direction:
                nx, ny = x + d.dx, y + d.dy
                if not self.in_bounds(nx, ny):
                    continue
                here = d in self.walls[y][x]
                there = d.opposite in self.walls[ny][nx]
                if here != there:
                    raise MazeError(
                        f"inconsistent wall between {(x, y)} and {(nx, ny)}")

    def in_bounds(self, x: int, y: int) -> bool:
        """Return whether a coordinate is inside the maze."""
        return 0 <= x < self.width and 0 <= y < self.height

    def has_wall(self, x: int, y: int, direction: Direction) -> bool:
        """Return whether a cell blocks movement in a direction."""
        if not self.in_bounds(x, y):
            raise MazeError("coordinate is outside the maze")
        return direction in self.walls[y][x]

    def can_move(self, x: int, y: int, direction: Direction) -> bool:
        """Return whether one step from (x, y) is possible."""
        if not self.in_bounds(x, y) or self.has_wall(x, y, direction):
            return False
        return self.in_bounds(x + direction.dx, y + direction.dy)

    def neighbors(self, x: int, y: int) -> list[Coordinate]:
        """Return all cells reachable in one move."""
        return [(x + d.dx, y + d.dy)
                for d in Direction if self.can_move(x, y, d)]

    def all_cells(self) -> Iterator[Coordinate]:
        """Iterate over every cell as (x, y)."""
        for y in range(self.height):
            for x in range(self.width):
                yield x, y

    def is_blocked(self, x: int, y: int) -> bool:
        """Return True for a fully walled cell (a '42' block)."""
        return len(self.walls[y][x]) == len(Direction)

    def open_cells(self) -> list[Coordinate]:
        """Return every cell that is not fully walled."""
        return [c for c in self.all_cells() if not self.is_blocked(*c)]

    def nearest_open_cell(self, target: Coordinate) -> Coordinate:
        """Return the closest non-blocked cell, searching over the grid."""
        if not self.in_bounds(*target):
            raise MazeError("coordinate is outside the maze")
        seen = {target}
        pending = deque([target])
        while pending:
            cell = pending.popleft()
            if not self.is_blocked(*cell):
                return cell
            for d in Direction:
                nxt = (cell[0] + d.dx, cell[1] + d.dy)
                if self.in_bounds(*nxt) and nxt not in seen:
                    seen.add(nxt)
                    pending.append(nxt)
        raise MazeError("maze has no open cell")

    def center(self) -> Coordinate:
        """Return the geometric centre cell (may be a '42' block)."""
        return self.width // 2, self.height // 2

    def corners(self) -> tuple[Coordinate, Coordinate, Coordinate,
                               Coordinate]:
        """Return the four corner cells."""
        return ((0, 0), (self.width - 1, 0),
                (0, self.height - 1), (self.width - 1, self.height - 1))

    def player_start(self) -> Coordinate:
        """Return the open cell closest to the centre."""
        return self.nearest_open_cell(self.center())

    def ghost_starts(self) -> list[Coordinate]:
        """Return the open cell closest to each corner."""
        return [self.nearest_open_cell(c) for c in self.corners()]

    def is_connected(self) -> bool:
        """Return True if every open cell is reachable from the start."""
        start = self.player_start()
        visited = {start}
        pending = deque([start])
        while pending:
            cell = pending.popleft()
            for nxt in self.neighbors(*cell):
                if nxt not in visited:
                    visited.add(nxt)
                    pending.append(nxt)
        return len(visited) == len(self.open_cells())
