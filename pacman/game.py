"""Game state and rules (no graphics)."""

import math
import random
from enum import Enum, auto

from pacman.entities import Player
from pacman.ghost import TIME_EPSILON, Ghost
from pacman.maze import Coordinate, Direction, Maze

MAX_FRAME_TIME = 0.25
SUBSTEP = 0.05                    # longest slice simulated at once
PLAYER_MOVE_INTERVAL = 0.20       # seconds per cell
GHOST_MOVE_INTERVAL = 0.27        # ghosts are a bit slower than the player
GHOST_RESPAWN_DELAY = 7.0         # after being eaten (subject: 5 to 10 s)
GHOST_RELEASE_STAGGER = 2.0       # ghost i leaves after i * 2 seconds


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
        move_interval: float = PLAYER_MOVE_INTERVAL,
        ghost_move_interval: float = GHOST_MOVE_INTERVAL,
        ghost_move_intervals: list[float] | None = None,
        points_per_pacgum: int = 10,
        points_per_super_pacgum: int = 50,
        points_per_ghost: int = 200,
        power_duration: float = 8.0,
        lives: int = 3,
        rng: random.Random | None = None,
    ) -> None:
        """Create a game on a maze, with everyone on their start cell."""
        self.maze = maze
        self.rng = rng or random.Random()   # never the global random module

        # Player
        self.player = Player(maze.player_start())
        self.move_interval = move_interval
        self._accumulator = 0.0

        # Game state, score and lives
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = lives

        # Collectibles
        self.super_pacgums = set(maze.ghost_starts())
        self.pacgums = (
            set(maze.open_cells())
            - self.super_pacgums
            - {self.player.start}
        )
        self.points_per_pacgum = points_per_pacgum
        self.points_per_super_pacgum = points_per_super_pacgum
        self.points_per_ghost = points_per_ghost

        # Power-up
        self.power_duration = power_duration
        self.power_time_left = 0.0

        # Ghosts: one per corner, each with its own personality and speed.
        ghost_starts = list(maze.ghost_starts())
        if ghost_move_intervals is None:
            ghost_move_intervals = [ghost_move_interval for _ in ghost_starts]
        if len(ghost_move_intervals) != len(ghost_starts):
            raise ValueError(
                "Provide exactly one movement interval for each ghost.")

        self.ghosts = [
            Ghost(
                start=start,
                personality=Ghost.PERSONALITIES[
                    i % len(Ghost.PERSONALITIES)],
                move_interval=ghost_move_intervals[i],
                respawn_delay=GHOST_RESPAWN_DELAY,
                start_delay=i * GHOST_RELEASE_STAGGER,
                rng=self.rng,
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

    def _eat(self, cell: Coordinate) -> None:
        """Collect a pacgum or super pacgum."""
        if cell in self.pacgums:
            self.pacgums.remove(cell)
            self.score += self.points_per_pacgum

        elif cell in self.super_pacgums:
            self.super_pacgums.remove(cell)
            self.score += self.points_per_super_pacgum

            # Refresh the power-up timer; ghosts that are out turn edible.
            self.power_time_left = self.power_duration
            for ghost in self.ghosts:
                if not ghost.is_respawning:
                    ghost.frightened = True

        # Check for level completion.
        if not self.pacgums and not self.super_pacgums:
            self.state = GameState.LEVEL_WON

    def _lose_life(self) -> None:
        """Take a life: game over at zero, otherwise restart positions."""
        self.lives -= 1
        if self.lives <= 0:
            self.state = GameState.GAME_OVER
        else:
            self.reset()

    def _check_collisions(self) -> None:
        """Handle collisions between the player and ghosts."""
        for ghost in self.ghosts:
            if ghost.is_respawning:
                continue
            if ghost.position != self.player.position:
                continue

            if ghost.frightened:
                ghost.eat()
                self.score += self.points_per_ghost
            else:
                self._lose_life()
                return

    def reset(self) -> None:
        """Put the player and ghosts back on their start cells."""
        self.player.reset()
        for ghost in self.ghosts:
            ghost.reset()
        self.state = GameState.PLAYING
        self._accumulator = 0.0
        self.power_time_left = 0.0

    def _substep(self) -> float:
        """Slice length: short enough that nobody moves twice per slice."""
        return min(
            SUBSTEP,
            self.move_interval / 2,
            *(g.move_interval / 2 for g in self.ghosts),
        )

    def _advance(self, dt: float) -> None:
        """Simulate one short slice of time."""
        # Power-up timer; when it ends, ghosts are normal again.
        was_edible = self.ghosts_edible
        self.power_time_left = max(0.0, self.power_time_left - dt)
        if was_edible and not self.ghosts_edible:
            for ghost in self.ghosts:
                ghost.frightened = False

        # Move the player at regular intervals.
        self._accumulator += dt
        while (
            self._accumulator >= self.move_interval - TIME_EPSILON
            and self.state is GameState.PLAYING
        ):
            self._accumulator -= self.move_interval
            if self.player.step(self.maze):
                self._eat(self.player.position)
            if self.state is GameState.PLAYING:
                self._check_collisions()

        # Move the ghosts, checking for a collision after each one.
        for ghost in self.ghosts:
            if self.state is not GameState.PLAYING:
                break
            ghost.update(dt, self.maze, self.player)
            self._check_collisions()

    def update(self, dt: float) -> None:
        """Advance the game by dt seconds."""
        if self.state is not GameState.PLAYING:
            return

        # Limit unusually large frame times.
        remaining = max(0.0, min(dt, MAX_FRAME_TIME))

        # Simulate in equal, short slices so that nobody can move twice
        # inside one slice and a collision can never be skipped.
        slices = max(1, math.ceil(remaining / self._substep() - TIME_EPSILON))
        step = remaining / slices
        for _ in range(slices):
            if self.state is not GameState.PLAYING:
                break
            self._advance(step)
