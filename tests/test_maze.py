"""Tests for maze generation."""

from pacman.maze import Maze


def test_generate_maze_contains_generator_output() -> None:
    maze = Maze.generate(width=8, height=6, seed=42)

    assert maze.width == 8
    assert maze.height == 6
    assert len(maze.cells) == 6
    assert all(len(row) == 8 for row in maze.cells)
    assert maze.entry == (0, 0)
    assert 0 <= maze.exit[0] < maze.height
    assert 0 <= maze.exit[1] < maze.width
    assert maze.shortest_path


def test_seed_reproduces_maze() -> None:
    first = Maze.generate(width=8, height=6, seed=42)
    second = Maze.generate(width=8, height=6, seed=42)

    assert first.cells == second.cells
    assert first.shortest_path == second.shortest_path
