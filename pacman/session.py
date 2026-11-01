"""Manage a complete Pac-Man run across multiple levels."""

import logging
import random
from pacman.cheats import Cheat
from typing import Callable, Protocol, Sequence

from pacman.cheats import Cheats
from pacman.game import Game, GameState
from pacman.maze import Direction, Maze
from pacman.maze_loader import MazeGeneration, MazeGenerationError


logger = logging.getLogger(__name__)

LEVEL_TRANSITION_DELAY = 2.0
LOW_TIME_SECONDS = 10.0


class LevelConfig(Protocol):
    """Configuration for one level."""

    width: int
    height: int


class SessionConfig(Protocol):
    """Configuration shared by the entire game session."""

    levels: Sequence[LevelConfig]
    seed: int | None
    lives: int
    points_per_pacgum: int
    points_per_super_pacgum: int
    points_per_ghost: int
    level_max_time: float


MazeFactory = Callable[
    [int, int, int | None, random.Random],
    Maze,
]


def default_maze_factory(
    width: int,
    height: int,
    seed: int | None,
    rng: random.Random,
) -> Maze:
    """Generate a maze using the external maze generator."""

    return MazeGeneration().generate_maze(
        width=width,
        height=height,
        seed=seed,
        rng=rng,
    )


class GameSession:
    """Manage the player's complete run across multiple levels."""

    def __init__(
        self,
        config: SessionConfig,
        maze_factory: MazeFactory = default_maze_factory,
        rng: random.Random | None = None,
    ) -> None:
        """Create a session and generate its first level."""

        if not config.levels:
            raise ValueError("A game session must contain at least one level.")

        self.config = config
        self.rng = rng if rng is not None else random.Random()
        self._maze_factory = maze_factory

        # One shared cheats object for the entire run.
        self.cheats = Cheats()

        # Level tracking.
        self.level_index = 0

        # Session status.
        self.error: str | None = None
        self.transition_left = 0.0
        self._transitioning = False
        self._ended: GameState | None = None

        # Generate the first level.
        # If this fails, MazeGenerationError is allowed to propagate.
        self.game = self._build_game(
            index=0,
            lives=config.lives,
            score=0,
        )

    @property
    def state(self) -> GameState:
        """Return the overall session state."""

        if self._ended is not None:
            return self._ended

        return self.game.state

    @property
    def level_number(self) -> int:
        """Return the current level number, starting at 1."""

        return self.level_index + 1

    @property
    def total_levels(self) -> int:
        """Return the total number of configured levels."""

        return len(self.config.levels)

    @property
    def score(self) -> int:
        """Return the current score."""

        return self.game.score

    @property
    def lives(self) -> int:
        """Return the remaining lives."""

        return self.game.lives

    @property
    def time_left(self) -> float:
        """Return the remaining time in the current level."""

        return self.game.time_left

    def set_direction(self, direction: Direction) -> None:
        """Set the player's desired movement direction."""

        if not self._is_over() and not self._transitioning:
            self.game.set_direction(direction)

    def toggle_pause(self) -> None:
        """Toggle pause, unless the session has ended or is transitioning."""

        if self._is_over() or self._transitioning:
            return

        self.game.toggle_pause()

    def toggle_cheat_mode(self) -> bool:
        """Toggle the master cheat switch and return its new value."""

        if self._is_over():
            return self.cheats.enabled

        self.cheats.enabled = not self.cheats.enabled
        return self.cheats.enabled

    def apply_cheat(self, cheat: Cheat) -> str:
        """Apply a cheat and return a message for the UI."""

        if not self.cheats.enabled:
            return "Cheat mode is off"

        if self._is_over():
            return "The game is over"

        self.cheats.used = True

        if cheat is Cheat.INVINCIBLE:
            self.cheats.invincible = not self.cheats.invincible

            status = "ON" if self.cheats.invincible else "OFF"
            return f"Invincibility {status}"

        elif cheat is Cheat.FREEZE_GHOSTS:
            self.cheats.freeze_ghosts = not self.cheats.freeze_ghosts

            status = "ON" if self.cheats.freeze_ghosts else "OFF"
            return f"Ghost freeze {status}"

        elif cheat is Cheat.SPEED_BOOST:
            self.cheats.speed_boost = not self.cheats.speed_boost

            status = "ON" if self.cheats.speed_boost else "OFF"
            return f"Speed boost {status}"

        elif cheat is Cheat.EXTRA_LIFE:
            self.game.lives += 1
            return f"Lives: {self.game.lives}"

        elif cheat is Cheat.SKIP_LEVEL:
            self.game.force_win()
            self._check_level_end()
            return "Level skipped"

        elif cheat is Cheat.POWER_UP:
            self.game.activate_power()
            return "Power-up active"

        elif cheat is Cheat.LOW_TIME:
            self.game.time_left = min(
                self.game.time_left,
                LOW_TIME_SECONDS,
            )
            return f"Only {self.game.time_left:.0f} s left"

        return "Unknown cheat"

    def _build_game(
        self,
        index: int,
        lives: int,
        score: int,
    ) -> Game:
        """Generate a maze and create a Game for the requested level."""

        level = self.config.levels[index]

        # The first level uses the configured seed.
        # Later levels use randomly generated seeds.
        seed = self.config.seed if index == 0 else None

        maze = self._maze_factory(
            level.width,
            level.height,
            seed,
            self.rng,
        )

        return Game(
            maze,
            points_per_pacgum=self.config.points_per_pacgum,
            points_per_super_pacgum=self.config.points_per_super_pacgum,
            points_per_ghost=self.config.points_per_ghost,
            lives=lives,
            score=score,
            level_max_time=self.config.level_max_time,
            cheats=self.cheats,
            rng=self.rng,
        )

    def _next_level(self) -> None:
        """Generate the next level while preserving score and lives."""

        next_index = self.level_index + 1

        try:
            new_game = self._build_game(
                index=next_index,
                lives=self.game.lives,
                score=self.game.score,
            )

        except MazeGenerationError as error:
            logger.exception("Could not generate level %d", next_index + 1)

            self.error = str(error)
            self._ended = GameState.GAME_OVER
            return

        # Only change the current level after successful generation.
        self.game = new_game
        self.level_index = next_index

        self.transition_left = 0.0
        self._transitioning = False

    def _level_state(self) -> GameState:
        """Return the current Game state.

        Kept as a separate method so static type checkers do not
        incorrectly assume that the state cannot change.
        """

        return self.game.state

    def _is_over(self) -> bool:
        """Check whether the entire session has ended."""

        return self._ended is not None

    def _check_level_end(self) -> None:
        """Detect level completion, game over and final victory."""

        if self._is_over():
            return

        state = self._level_state()

        if state is GameState.GAME_OVER:
            self._ended = GameState.GAME_OVER

        elif state is GameState.LEVEL_WON and not self._transitioning:

            # The final level has been completed.
            if self.level_index + 1 >= self.total_levels:
                self._ended = GameState.VICTORY

            else:
                # Start the transition to the next level.
                self._transitioning = True
                self.transition_left = LEVEL_TRANSITION_DELAY

    def update(self, dt: float) -> None:
        """Advance the session by dt seconds."""

        self._check_level_end()

        if self._is_over():
            return

        # Handle the delay between levels.
        if self._transitioning:
            self.transition_left -= max(0.0, dt)

            if self.transition_left <= 0:
                self._next_level()

            return
        self.game.update(dt)

        self._check_level_end()
