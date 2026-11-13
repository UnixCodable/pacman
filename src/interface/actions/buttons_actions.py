import pygame as pg
from enum import Enum


class ButtonAction(Enum):
    """Enum inherited class that keep a list of actions
    with random generated numbers for pygame.event.
    """
    SCROLL_DOWN = pg.event.custom_type()
    SCROLL_UP = pg.event.custom_type()
    MINUS_SOUND = pg.event.custom_type()
    PLUS_SOUND = pg.event.custom_type()
