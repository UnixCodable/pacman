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
# """Maze generation for Pac-Man levels."""

# from dataclasses import dataclass

# from mazegenerator import MazeGenerator


# @dataclass(frozen=True)
# class Maze:
# 	"""A generated maze and the navigation data supplied by the generator."""

# 	cells: list[list[int]]
# 	entry: tuple[int, int]
# 	exit: tuple[int, int]
# 	shortest_path: str

# 	@classmethod
# 	def generate(cls, width: int, height: int, seed: int = 0,
# 				 perfect: bool = False) -> "Maze":
# 		"""Generate a maze with the requested dimensions and seed."""
# 		generator = MazeGenerator(
# 			size=(width, height),
# 			entry_cell=(0, 0),
# 			exit_cell=(height - 1, width - 1),
# 			perfect=perfect,
# 			seed=seed,
# 		)
# 		return cls(
# 			cells=generator.maze,
# 			entry=generator.maze_entry,
# 			exit=generator.maze_exit,
# 			shortest_path=generator.shortest_path,
# 		)

# 	@property
# 	def width(self) -> int:
# 		"""Return the number of columns in the maze."""
# 		return len(self.cells[0])

# 	@property
# 	def height(self) -> int:
# 		"""Return the number of rows in the maze."""
# 		return len(self.cells)

# 	def summary(self) -> str:
# 		"""Return a compact description useful while wiring up the game."""
# 		return (f"Maze: {self.width}x{self.height}, entry={self.entry}, "
# 				f"exit={self.exit}, path length={len(self.shortest_path)}")
