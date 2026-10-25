"""Game state and rules (no graphics)."""

from enum import Enum, auto

from pacman.entities import Player
from pacman.maze import Direction, Maze

MAX_FRAME_TIME = 0.25


class GameState(Enum):
    """High level state of a running game."""

    PLAYING = auto()
    PAUSED = auto()
    # More states will be added later:
    # LEVEL_WON, GAME_OVER, VICTORY


class Game:
    """Owns the maze and the player and advances them over time."""

    def __init__(self, maze: Maze, move_interval: float = 0.15) -> None:
        """Create a game on a maze, with the player at its start."""
        self.maze = maze
        self.player = Player(maze.player_start())
        self.state = GameState.PLAYING
        self.move_interval = move_interval
        self._accumulator = 0.0

    def set_direction(self, direction: Direction) -> None:
        """Set the player's desired direction."""
        self.player.desired = direction

    def toggle_pause(self) -> None:
        """Toggle between PLAYING and PAUSED states."""
        if self.state is GameState.PLAYING:
            self.state = GameState.PAUSED
        elif self.state is GameState.PAUSED:
            self.state = GameState.PLAYING

    def update(self, dt: float) -> None:
        """Advance the world by dt seconds (ignored unless PLAYING)."""
        if self.state is not GameState.PLAYING:
            return

        # Clamp dt between 0 and MAX_FRAME_TIME.
        dt = max(0.0, min(dt, MAX_FRAME_TIME))
        self._accumulator += dt

        # Move the player at regular intervals.
        while self._accumulator >= self.move_interval:
            self._accumulator -= self.move_interval
            self.player.step(self.maze)
