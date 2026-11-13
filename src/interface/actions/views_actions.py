import pygame as pg
from enum import Enum


class ViewAction(Enum):
    """Enum inherited class that keep a list of actions specific to views
    with random generated numbers for pygame.event.
    """
    LEADERBOARD = pg.event.custom_type()
    SETTINGS = pg.event.custom_type()
    MENU = pg.event.custom_type()
    GAME = pg.event.custom_type()
    EXIT = pg.event.custom_type()
