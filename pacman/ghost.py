"""Ghost movement and AI behaviors."""

import random
from collections import deque
from collections.abc import Iterator

from pacman.entities import Player
from pacman.maze import Coordinate, Direction, Maze

TIME_EPSILON = 1e-9               # absorbs float rounding in timers
FRIGHTENED_SLOWDOWN = 1.35        # edible ghosts move 35% slower
AMBUSH_LOOK_AHEAD = 4             # cells ahead of the player
UNPREDICTABLE_RANDOM_CHANCE = 0.30
WANDERER_RANDOM_CHANCE = 0.75


class Ghost:
    """A ghost with configurable speed and movement personality."""

    PERSONALITIES = ("chaser", "ambusher", "unpredictable", "wanderer")

    def __init__(
        self,
        start: Coordinate,
        personality: str = "chaser",
        move_interval: float = 0.27,
        respawn_delay: float = 7.0,
        start_delay: float = 0.0,
        rng: random.Random | None = None,
    ) -> None:
        """Create a ghost.

        Args:
            start: Corner cell where the ghost lives.
            personality: One of PERSONALITIES.
            move_interval: Seconds per cell.
            respawn_delay: Seconds spent at home after being eaten.
            start_delay: Seconds to wait before leaving at level start.
            rng: Random generator (never the global random module).
        """
        if personality not in self.PERSONALITIES:
            raise ValueError(
                f"Unknown personality: {personality}. "
                f"Choose from {self.PERSONALITIES}."
            )
        if move_interval <= 0:
            raise ValueError("move_interval must be greater than zero.")

        self.start = start
        self.x, self.y = start
        self.personality = personality
        self.move_interval = move_interval
        self.respawn_delay = respawn_delay
        self.start_delay = start_delay
        self.rng = rng or random.Random()

        self.direction: Direction | None = None
        self.frightened = False
        self.is_respawning = False
        self._accumulator = 0.0
        self._respawn_timer = 0.0
        self.reset()

    @property
    def position(self) -> Coordinate:
        """Return the ghost's current position."""
        return (self.x, self.y)

    def reset(self) -> None:
        """Return to the start cell (used at level start / after a life)."""
        self.x, self.y = self.start
        self.direction = None
        self.frightened = False
        self._accumulator = 0.0
        self.is_respawning = self.start_delay > 0
        self._respawn_timer = self.start_delay

    def eat(self) -> None:
        """Send the ghost home at once and start its respawn countdown."""
        if not self.is_respawning:
            self.x, self.y = self.start
            self.direction = None
            self.frightened = False
            self._accumulator = 0.0
            self.is_respawning = True
            self._respawn_timer = self.respawn_delay

    def _neighbors(
        self, maze: Maze, cell: Coordinate
    ) -> Iterator[tuple[Coordinate, Direction]]:
        """Yield legal neighboring cells and their directions."""
        x, y = cell
        for direction in Direction:
            if maze.can_move(x, y, direction):
                yield (x + direction.dx, y + direction.dy), direction

    def _distances(self, maze: Maze,
                   start: Coordinate) -> dict[Coordinate, int]:
        """Calculate shortest-path distances using BFS."""
        distances = {start: 0}
        queue = deque([start])
        while queue:
            cell = queue.popleft()
            for neighbor, _ in self._neighbors(maze, cell):
                if neighbor not in distances:
                    distances[neighbor] = distances[cell] + 1
                    queue.append(neighbor)
        return distances

    def _bfs_direction(self, maze: Maze,
                       target: Coordinate) -> Direction | None:
        """Find the first step on a shortest path to the target."""
        start = self.position
        if start == target:
            return None

        queue = deque([start])
        seen = {start}
        first_direction: dict[Coordinate, Direction] = {}
        while queue:
            cell = queue.popleft()
            if cell == target:
                return first_direction[cell]
            for neighbor, direction in self._neighbors(maze, cell):
                if neighbor in seen:
                    continue
                seen.add(neighbor)
                first_direction[neighbor] = (
                    direction if cell == start else first_direction[cell])
                queue.append(neighbor)
        return None  # no path to the target

    def _ambush_target(self, maze: Maze, player: Player) -> Coordinate:
        """Cell up to AMBUSH_LOOK_AHEAD steps ahead along the corridor."""
        heading = player.direction or player.desired
        x, y = player.position
        if heading is None:
            return x, y
        for _ in range(AMBUSH_LOOK_AHEAD):
            if not maze.can_move(x, y, heading):
                break
            x, y = x + heading.dx, y + heading.dy
        return x, y

    def _random_direction(self, maze: Maze) -> Direction | None:
        """Choose a random legal direction, avoiding a U-turn if possible."""
        options = list(self._neighbors(maze, self.position))
        if not options:
            return None
        if self.direction is not None and len(options) > 1:
            ahead = [o for o in options
                     if o[1] is not self.direction.opposite]
            options = ahead or options
        return self.rng.choice(options)[1]

    def _flee_direction(self, maze: Maze,
                        player: Player) -> Direction | None:
        """Choose a move that increases distance from the player."""
        distances = self._distances(maze, player.position)
        options = list(self._neighbors(maze, self.position))
        if not options:
            return None
        self.rng.shuffle(options)       # random tie-break
        return max(options, key=lambda o: distances.get(o[0], -1))[1]

    def _choose_direction(self, maze: Maze,
                          player: Player) -> Direction | None:
        """Choose a direction according to the ghost's current behavior."""
        if self.frightened:
            return self._flee_direction(maze, player)

        if self.personality == "wanderer":
            if self.rng.random() < WANDERER_RANDOM_CHANCE:
                return self._random_direction(maze)
            return self._bfs_direction(maze, player.position)

        if self.personality == "unpredictable":
            if self.rng.random() < UNPREDICTABLE_RANDOM_CHANCE:
                return self._random_direction(maze)
            return self._bfs_direction(maze, player.position)

        if self.personality == "ambusher":
            direction = self._bfs_direction(
                maze, self._ambush_target(maze, player))
            if direction is None:       # already there: chase directly
                direction = self._bfs_direction(maze, player.position)
            return direction

        return self._bfs_direction(maze, player.position)   # chaser

    def step(self, maze: Maze, player: Player) -> bool:
        """Move one tile. Returns True if the ghost moved."""
        if self.is_respawning:
            return False
        direction = self._choose_direction(maze, player)
        if direction is None or not maze.can_move(
                self.x, self.y, direction):
            self.direction = None
            return False
        self.direction = direction
        self.x += direction.dx
        self.y += direction.dy
        return True

    def update(self, dt: float, maze: Maze, player: Player) -> bool:
        """Advance the ghost by dt seconds. True if it moved."""
        if self.is_respawning:
            self._respawn_timer -= dt
            if self._respawn_timer <= 0:
                self.is_respawning = False
                self._respawn_timer = 0.0
                self._accumulator = 0.0
            return False

        interval = self.move_interval
        if self.frightened:
            interval *= FRIGHTENED_SLOWDOWN
        self._accumulator += dt
        moved = False
        while self._accumulator >= interval - TIME_EPSILON:
            self._accumulator -= interval
            if self.step(maze, player):
                moved = True
        return moved
