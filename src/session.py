"""Manage a complete Pac-Man run across multiple levels."""

import logging
import random
from typing import Callable

from src.cheats import Cheats, Cheat
from src.config import Config, MAX_LEVELS
from src.game import Game, GameState
from src.maze import Direction, Maze
from src.maze_loader import MazeGeneration, MazeGenerationError

logger = logging.getLogger(__name__)

LEVEL_TRANSITION_DELAY = 2.0
LOW_TIME_SECONDS = 10.0


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
        config: Config,
        maze_factory: MazeFactory = default_maze_factory,
        rng: random.Random | None = None,
    ) -> None:
        if not config.levels:
            raise ValueError(
                "A game session must contain at least one level."
            )

        if len(config.levels) > MAX_LEVELS:
            raise ValueError(
                f"A game session cannot have more than "
                f"{MAX_LEVELS} levels."
            )

        self.config = config
        self.rng = rng if rng is not None else random.Random()
        self._maze_factory = maze_factory

        # One shared cheat object for the entire run.
        self.cheats = Cheats()

        self.level_index = 0
        self.error: str | None = None

        self.transition_left = 0.0
        self._transitioning = False
        self._ended: GameState | None = None

        # Create the first level.
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
        """Return the current total score."""

        return self.game.score

    @property
    def lives(self) -> int:
        """Return the number of remaining lives."""

        return self.game.lives

    @property
    def time_left(self) -> float:
        """Return the time remaining in the current level."""

        return self.game.time_left

    def set_direction(self, direction: Direction) -> None:
        """Send a movement request to the current game."""

        if not self._is_over() and not self._transitioning:
            self.game.set_direction(direction)

    def toggle_pause(self) -> None:
        """Pause or resume the current game."""

        if self._is_over() or self._transitioning:
            return

        self.game.toggle_pause()

    def toggle_cheat_mode(self) -> bool:
        """Enable or disable cheat mode."""

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

        if self._transitioning:
            return "Wait until the next level starts"

        self.cheats.used = True

        if cheat is Cheat.INVINCIBLE:
            self.cheats.invincible = not self.cheats.invincible
            status = "ON" if self.cheats.invincible else "OFF"
            return f"Invincibility {status}"

        if cheat is Cheat.FREEZE_GHOSTS:
            self.cheats.freeze_ghosts = not self.cheats.freeze_ghosts
            status = "ON" if self.cheats.freeze_ghosts else "OFF"
            return f"Ghost freeze {status}"

        if cheat is Cheat.SPEED_BOOST:
            self.cheats.speed_boost = not self.cheats.speed_boost
            status = "ON" if self.cheats.speed_boost else "OFF"
            return f"Speed boost {status}"

        if cheat is Cheat.EXTRA_LIFE:
            self.game.lives += 1
            return f"Lives: {self.game.lives}"

        if cheat is Cheat.SKIP_LEVEL:
            self.game.force_win()
            self._check_level_end()
            return "Level skipped"

        if cheat is Cheat.POWER_UP:
            self.game.activate_power()
            return "Power-up active"

        if cheat is Cheat.LOW_TIME:
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
        """Generate a maze and construct the requested level."""

        level = self.config.levels[index]

        # Use the configured seed for the first level.
        # Later levels use the shared random generator.
        seed = self.config.seed if index == 0 else None

        maze = self._maze_factory(
            level.width,
            level.height,
            seed,
            self.rng,
        )

        logger.info(
            "Starting level %d: %dx%d, %d ghosts, speed %.2f",
            index + 1,
            level.width,
            level.height,
            level.ghost_count,
            level.ghost_speed,
        )

        return Game(
            maze,
            points_per_pacgum=self.config.points_per_pacgum,
            points_per_super_pacgum=(
                self.config.points_per_super_pacgum
            ),
            points_per_ghost=self.config.points_per_ghost,
            lives=lives,
            score=score,
            level_max_time=level.level_max_time,
            ghost_speed=level.ghost_speed,
            ghost_count=level.ghost_count,
            cheats=self.cheats,
            rng=self.rng,
        )

    def _next_level(self) -> None:
        """Create the next level while preserving score and lives."""

        next_index = self.level_index + 1

        try:
            new_game = self._build_game(
                index=next_index,
                lives=self.game.lives,
                score=self.game.score,
            )

        except (MazeGenerationError, ValueError) as error:
            logger.error(
                "Could not create level %d: %s",
                next_index + 1,
                error,
            )
            self.error = str(error)
            self._ended = GameState.GAME_OVER
            return

        self.game = new_game
        self.level_index = next_index
        self.transition_left = 0.0
        self._transitioning = False

    def _is_over(self) -> bool:
        """Return whether the complete session has ended."""

        return self._ended is not None

    def _check_level_end(self) -> None:
        """Check whether the current level or session has ended."""

        if self._is_over():
            return

        if self.game.state is GameState.GAME_OVER:
            self._ended = GameState.GAME_OVER
            return

        if (
            self.game.state is GameState.LEVEL_WON
            and not self._transitioning
        ):
            if self.level_index + 1 >= self.total_levels:
                self._ended = GameState.VICTORY
                logger.info("All levels completed. Player wins!")
            else:
                self._transitioning = True
                self.transition_left = LEVEL_TRANSITION_DELAY
                logger.info(
                    "Level %d completed. Preparing level %d.",
                    self.level_number,
                    self.level_number + 1,
                )

    def update(self, dt: float) -> None:
        """Advance the session by dt seconds."""

        self._check_level_end()

        if self._is_over():
            return

        if self._transitioning:
            self.transition_left -= max(0.0, dt)

            if self.transition_left <= 0:
                self._next_level()

            return

        self.game.update(dt)
        self._check_level_end()
