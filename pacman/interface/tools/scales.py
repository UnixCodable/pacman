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
