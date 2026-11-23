import pygame as pg


class Scaling:
    def __init__(self, surface: pg.Surface):
        self._surface = surface

    def size(self, x: float, y: float) -> tuple[int, int]:
        width = self._surface.get_width()
        height = self._surface.get_height()
        x /= 100
        y /= 100
        return (int(width * x), int(height * y))

    def pos(self, x: float, y: float) -> tuple[int, int]:
        width = self._surface.get_width()
        height = self._surface.get_height()
        x /= 100
        y /= 100
        return (int(width * x), int(height * y))

    def text(self, scale: float) -> int:
        width = self._surface.get_width()
        scale /= 100
        return int(width * scale)

    def maze(self, maze: pg.Surface) -> float:
        screen_height = self._surface.get_height()

        maze_initial_height = maze.get_height()
        maze_initial_width = maze.get_width()

        height_ratio = screen_height / maze_initial_height
        width_ratio = screen_height / maze_initial_width

        return min([height_ratio, width_ratio])
