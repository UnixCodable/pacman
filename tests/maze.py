"""Integration tests: the game on mazes made by the real generator."""

import random

import pytest

from pacman.game import Game
from pacman.maze import Direction
from pacman.maze_loader import MazeGeneration

SIZES = [(15, 15), (16, 16), (14, 10), (21, 15), (31, 21)]


def random_walk(game: Game, rng: random.Random, ticks: int) -> list[
        tuple[int, int]]:
    """Press random directions and return every position visited."""
    path = [game.player.position]
    for _ in range(ticks):
        game.set_direction(rng.choice(list(Direction)))
        game.update(game.move_interval)
        path.append(game.player.position)
    return path


@pytest.mark.parametrize("size", SIZES)
def test_player_never_enters_blocked_cell_or_crosses_wall(
        size: tuple[int, int]) -> None:
    maze = MazeGeneration().generate_maze(size[0], size[1], 42,
                                          random.Random(0))
    game = Game(maze)
    assert not maze.is_blocked(*game.player.position)
    path = random_walk(game, random.Random(7), 3000)
    for before, after in zip(path, path[1:]):
        assert not maze.is_blocked(*after)
        assert after == before or after in maze.neighbors(*before)


def test_player_stands_still_until_first_key() -> None:
    maze = MazeGeneration().generate_maze(16, 16, 42, random.Random(0))
    game = Game(maze)
    start = game.player.position
    for _ in range(20):
        game.update(0.15)
    assert game.player.position == start
    assert game.player.direction is None


def test_same_seed_same_inputs_same_game() -> None:
    def run() -> list[tuple[int, int]]:
        maze = MazeGeneration().generate_maze(16, 16, 42, random.Random(0))
        return random_walk(Game(maze), random.Random(3), 500)
    assert run() == run()


def test_player_can_explore_most_of_the_maze() -> None:
    maze = MazeGeneration().generate_maze(15, 15, 42, random.Random(0))
    path = random_walk(Game(maze), random.Random(1), 20000)
    assert len(set(path)) > 0.9 * len(maze.open_cells())
