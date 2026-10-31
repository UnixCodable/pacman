import pygame as pg


def scale_size(x: float, y: float, surface: pg.Surface) -> tuple[int, int]:
    width = surface.get_width()
    height = surface.get_height()
    x /= 100
    y /= 100
    return (int(width * x), int(height * y))


def scale_pos(x: float, y: float, surface: pg.Surface) -> tuple[int, int]:
    width = surface.get_width()
    height = surface.get_height()
    return (int(width * x), int(height * y))


def scale_text(scale: float, surface: pg.Surface) -> int:
    width = surface.get_width()
    return int(width * scale)
