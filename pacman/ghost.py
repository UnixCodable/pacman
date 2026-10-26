"""Ghost movement and AI behaviors."""

from collections import deque
import random

from pacman.maze import Direction, Maze


class Ghost:
    """A ghost with configurable speed and movement personality."""

    PERSONALITIES = ("chaser", "ambusher", "unpredictable", "wanderer")

    def __init__(
        self,
        start,
        personality: str = "chaser",
        move_interval: float = 0.15,
        respawn_delay: float = 1.0,
    ) -> None:
        self.start = start
        self.x, self.y = start

        self.personality = personality
        self.move_interval = move_interval
        self.respawn_delay = respawn_delay

        self.direction = None
        self._accumulator = 0.0
        self._respawn_timer = 0.0
        self.is_respawning = False

        if personality not in self.PERSONALITIES:
            raise ValueError(
                f"Unknown personality: {personality}. "
                f"Choose from {self.PERSONALITIES}."
            )

        if move_interval <= 0:
            raise ValueError("move_interval must be greater than zero.")

    @property
    def position(self) -> tuple[int, int]:
        """Return the ghost's current position."""
        return (self.x, self.y)

    def reset(self) -> None:
        """Return the ghost to its starting position."""
        self.x, self.y = self.start
        self.direction = None
        self._accumulator = 0.0
        self._respawn_timer = 0.0
        self.is_respawning = False

    def eat(self) -> None:
        """Start the respawn countdown after the ghost is eaten."""
        if not self.is_respawning:
            self.is_respawning = True
            self._respawn_timer = self.respawn_delay
            self.direction = None

    def _neighbors(self, maze: Maze, cell):
        """Yield legal neighboring cells and their directions."""
        x, y = cell

        for direction in Direction:
            if maze.can_move(x, y, direction):
                neighbor = (
                    x + direction.dx,
                    y + direction.dy,
                )
                yield neighbor, direction

    def _distances(self, maze: Maze, start):
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

    def _bfs_direction(self, maze: Maze, target):
        """Find the first step on a shortest path to the target."""
        start = self.position

        if start == target:
            return None

        queue = deque([start])
        previous = {start: None}
        first_direction = {}

        while queue:
            cell = queue.popleft()

            if cell == target:
                return first_direction[cell]

            for neighbor, direction in self._neighbors(maze, cell):
                if neighbor in previous:
                    continue

                previous[neighbor] = cell

                if cell == start:
                    first_direction[neighbor] = direction
                else:
                    first_direction[neighbor] = first_direction[cell]

                queue.append(neighbor)

        # No path to the target.
        return None

    def _player_target(self, player):
        """Choose the tile the ghost wants to chase."""
        player_position = player.position

        if self.personality == "ambusher":
            # Target four tiles ahead of the player.
            direction = player.direction

            if direction is not None:
                return (
                    player.x + direction.dx * 4,
                    player.y + direction.dy * 4,
                )

        return player_position

    def _random_direction(self, maze: Maze):
        """Choose a random legal direction."""
        options = list(self._neighbors(maze, self.position))

        if not options:
            return None

        # Avoid immediately reversing direction when possible.
        if self.direction is not None and len(options) > 1:
            reverse = (
                -self.direction.dx,
                -self.direction.dy,
            )

            without_reverse = [
                option
                for option in options
                if (option[1].dx, option[1].dy) != reverse
            ]

            if without_reverse:
                options = without_reverse

        return random.choice(options)[1]

    def _flee_direction(self, maze: Maze, player):
        """Choose a move that increases distance from the player."""
        distances = self._distances(maze, player.position)
        options = list(self._neighbors(maze, self.position))

        if not options:
            return None

        # Prefer the neighboring cell with the greatest BFS distance.
        # Randomize ties to make movement less predictable.
        random.shuffle(options)

        best_cell, best_direction = max(
            options,
            key=lambda option: distances.get(option[0], -1),
        )

        return best_direction

    def _choose_direction(self, maze: Maze, player, edible: bool):
        """Choose a direction according to the ghost's current behavior."""

        if edible:
            return self._flee_direction(maze, player)

        if self.personality == "wanderer":
            # Wander randomly most of the time.
            if random.random() < 0.75:
                return self._random_direction(maze)

            return self._bfs_direction(maze, player.position)

        if self.personality == "unpredictable":
            # Occasionally abandon the chase and move randomly.
            if random.random() < 0.30:
                return self._random_direction(maze)

            return self._bfs_direction(maze, player.position)

        if self.personality == "ambusher":
            target = self._player_target(player)
            direction = self._bfs_direction(maze, target)

            # If the target is unreachable, chase the player instead.
            if direction is None:
                direction = self._bfs_direction(
                    maze, player.position
                )

            return direction

        # Default personality: direct BFS chaser.
        return self._bfs_direction(maze, player.position)

    def step(self, maze: Maze, player, edible: bool = False) -> bool:
        """Move one tile toward the current target.

        Returns True if the ghost moved, otherwise False.
        """
        if self.is_respawning:
            return False

        direction = self._choose_direction(maze, player, edible)

        if direction is None:
            self.direction = None
            return False

        if not maze.can_move(self.x, self.y, direction):
            self.direction = None
            return False

        self.direction = direction
        self.x += direction.dx
        self.y += direction.dy

        return True

    def update(
        self,
        dt: float,
        maze: Maze,
        player,
        edible: bool = False,
    ) -> bool:
        """Advance the ghost according to elapsed time.

        Returns True if the ghost moved at least one tile.
        """
        if self.is_respawning:
            self._respawn_timer -= dt

            if self._respawn_timer <= 0:
                self.reset()

            return False

        self._accumulator += dt
        moved = False

        while self._accumulator >= self.move_interval:
            self._accumulator -= self.move_interval

            if self.step(maze, player, edible):
                moved = True

        return moved
