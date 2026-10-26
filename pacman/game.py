"""Game state and rules (no graphics)."""

from enum import Enum, auto

from pacman.entities import Player
from pacman.ghost import Ghost
from pacman.maze import Direction, Maze


MAX_FRAME_TIME = 0.25


class GameState(Enum):
    """High-level state of the game."""

    PLAYING = auto()
    PAUSED = auto()
    LEVEL_WON = auto()
    GAME_OVER = auto()
    VICTORY = auto()


class Game:
    """Owns the maze, player, ghosts, score, and game rules."""

    def __init__(
        self,
        maze: Maze,
        move_interval: float = 0.15,
        ghost_move_interval: float | None = None,
        ghost_move_intervals: list[float] | None = None,
        points_per_pacgum: int = 10,
        points_per_super_pacgum: int = 50,
        points_per_ghost: int = 200,
        power_duration: float = 8.0,
    ) -> None:
        self.maze = maze

        # Player
        self.player = Player(maze.player_start())
        self.move_interval = move_interval
        self._accumulator = 0.0

        # Game state and score
        self.state = GameState.PLAYING
        self.score = 0

        # Collectibles
        self.super_pacgums = set(maze.ghost_starts())
        self.pacgums = (
            set(maze.open_cells())
            - self.super_pacgums
            - {self.player.start}
        )

        self.points_per_pacgum = points_per_pacgum
        self.points_per_super_pacgum = points_per_super_pacgum

        # Power-up
        self.power_duration = power_duration
        self.power_time_left = 0.0

        # Ghost configuration
        ghost_starts = list(maze.ghost_starts())

        personalities = [
            "chaser",
            "ambusher",
            "unpredictable",
            "wanderer",
        ]

        # By default, ghosts move at the same interval as the player.
        if ghost_move_interval is None:
            ghost_move_interval = move_interval

        # Optionally configure each ghost's interval individually.
        if ghost_move_intervals is None:
            ghost_move_intervals = [
                ghost_move_interval
                for _ in ghost_starts
            ]

        if len(ghost_move_intervals) != len(ghost_starts):
            raise ValueError(
                "Provide exactly one movement interval "
                "for each ghost."
            )

        self.points_per_ghost = points_per_ghost

        self.ghosts = [
            Ghost(
                start=start,
                personality=personalities[i % len(personalities)],
                move_interval=ghost_move_intervals[i],
            )
            for i, start in enumerate(ghost_starts)
        ]

    @property
    def ghosts_edible(self) -> bool:
        """Whether the power-up effect is currently active."""
        return self.power_time_left > 0

    def set_direction(self, direction: Direction) -> None:
        """Set the player's desired direction."""
        self.player.desired = direction

    def toggle_pause(self) -> None:
        """Toggle between PLAYING and PAUSED."""
        if self.state is GameState.PLAYING:
            self.state = GameState.PAUSED
        elif self.state is GameState.PAUSED:
            self.state = GameState.PLAYING

    def _eat(self, cell) -> None:
        """Collect a pacgum or super pacgum."""

        if cell in self.pacgums:
            self.pacgums.remove(cell)
            self.score += self.points_per_pacgum

        elif cell in self.super_pacgums:
            self.super_pacgums.remove(cell)
            self.score += self.points_per_super_pacgum

            # Refresh the power-up timer.
            self.power_time_left = self.power_duration

        # Check for level completion.
        if not self.pacgums and not self.super_pacgums:
            self.state = GameState.LEVEL_WON

    def _check_collisions(self) -> None:
        """Handle collisions between the player and ghosts."""

        for ghost in self.ghosts:
            if ghost.is_respawning:
                continue

            if ghost.position != self.player.position:
                continue

            if self.ghosts_edible:
                # Eat the ghost and award points.
                ghost.eat()
                self.score += self.points_per_ghost
            else:
                # A non-edible ghost catches the player.
                self.state = GameState.GAME_OVER
                return

    def reset(self) -> None:
        """Reset the player and ghosts to their starting positions."""

        self.player.reset()

        for ghost in self.ghosts:
            ghost.reset()

        self.state = GameState.PLAYING
        self._accumulator = 0.0
        self.power_time_left = 0.0

    def update(self, dt: float) -> None:
        """Advance the game by dt seconds."""

        if self.state is not GameState.PLAYING:
            return

        # Limit unusually large frame times.
        dt = max(0.0, min(dt, MAX_FRAME_TIME))

        # Update the power-up timer.
        self.power_time_left = max(
            0.0,
            self.power_time_left - dt,
        )

        # Accumulate time for player movement.
        self._accumulator += dt

        while (
            self._accumulator >= self.move_interval
            and self.state is GameState.PLAYING
        ):
            self._accumulator -= self.move_interval

            # Move the player.
            if self.player.step(self.maze):
                self._eat(self.player.position)

                if self.state is not GameState.PLAYING:
                    break

            # Check for collisions after player movement.
            self._check_collisions()

            if self.state is not GameState.PLAYING:
                break

        # Update ghosts independently of player movement.
        if self.state is not GameState.PLAYING:
            return

        for ghost in self.ghosts:
            ghost.update(
                dt=dt,
                maze=self.maze,
                player=self.player,
                edible=self.ghosts_edible,
            )

            # Check collisions after ghost movement.
            self._check_collisions()

            if self.state is not GameState.PLAYING:
                break
