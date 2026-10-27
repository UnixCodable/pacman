import pygame as pg
import sys
from abc import ABC, abstractmethod


class View(ABC):

    @abstractmethod
    def _get_events(self):
        pass

    @abstractmethod
    def run(self):
        pass


class Settings(View):
    def __init__(self):
        self._running = True

    def _get_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit(0)

    def run(self):
        while self._running:
            self._get_events()
            pg.display.flip()


class Leaderboard(View):
    def __init__(self):
        self._running = True

    def _get_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit(0)

    def run(self):
        while self._running:
            self._get_events()
            pg.display.flip()


class Game(View):
    def __init__(self):
        self._running = True

    def _get_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit(0)

    def run(self):
        while self._running:
            self._get_events()
            pg.display.flip()


class Menu(View):
    def __init__(self):
        self._running = True

    def _get_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit(0)

    def run(self):
        while self._running:
            self._get_events()
            pg.display.flip()
