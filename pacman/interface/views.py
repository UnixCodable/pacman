from time import time
from typing import Generator

import pygame as pg
import sys
from itertools import cycle
from buttons import MenuButton
from tools.scales import Scaling
from pyvidplayer2 import Video
from abc import ABC, abstractmethod
from actions.views_actions import ViewAction


class View(ABC):

    def __init__(self, surface: pg.Surface) -> None:
        self._running = True
        self._surface = surface
        self._scale = Scaling(self._surface)

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
                pg.event.post(pg.event.Event(ViewAction.EXIT.value))
                self._running = False

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
                pg.event.post(pg.event.Event(ViewAction.EXIT.value))
                self._running = False

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
                pg.event.post(pg.event.Event(ViewAction.EXIT.value))
                self._running = False

    def run(self):
        while self._running:
            self._get_events()
            pg.display.flip()


class Cinematics(View):

    def __init__(self,
                 video: Video,
                 surface: pg.Surface,
                 speed: float = 1,
                 begin_frame: int = 1,
                 end_frame: int | None = None):

        super().__init__(surface)

        self._video: Video = video
        self._video.set_speed(speed)
        self._video.seek_frame(begin_frame)
        self._end_frame = end_frame if end_frame else 0

    def _get_events(self) -> None:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self._video.stop()
                pg.event.post(pg.event.Event(ViewAction.EXIT.value))
                self._running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self._video.set_speed(1)
                    if self._end_frame > 0:
                        self._video.seek_frame(self._end_frame - 2)
                    else:
                        self._video.seek_frame(self._video.frame_count - 2)

    def run(self) -> None:
        self._video.resize(self._surface.get_size())
        while self._running:
            if self._video.frame == self._end_frame:
                break
            self._get_events()
            self._video.draw(self._surface, (0, 0))
            pg.display.update()
        self._video.stop()


class Menu(View):
    def __init__(self, surface: pg.Surface):

        super().__init__(surface)

        self._footer = pg.image.load('pacman/interface/assets/footer.png')
        self._fill_auth = True

    def _get_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.event.post(pg.event.Event(ViewAction.EXIT.value))
                self._running = False

    def _background_animation(self) -> Generator:
        pacman = [
            pg.image.load('pacman/interface/assets/pacman/tile_0001.png'),
            pg.image.load('pacman/interface/assets/pacman/tile_0002.png'),
            pg.image.load('pacman/interface/assets/pacman/tile_0003.png'),
            pg.image.load('pacman/interface/assets/pacman/tile_0002.png'),
        ]
        x = 0
        y = 0
        pacman_sequence = cycle(pacman)
        last_time = 0
        commands = (5, 0)
        while self._running:
            current_time = time() / 1000
            for event in pg.event.get(pg.KEYUP):
                if event.type == pg.KEYUP:
                    if event.key == pg.K_UP:
                        commands = (0, -5)
                    if event.key == pg.K_DOWN:
                        commands = (0, 5)
                    if event.key == pg.K_LEFT:
                        commands = (-5, 0)
                    if event.key == pg.K_RIGHT:
                        commands = (5, 0)
            if current_time - 0.00007 > last_time:
                pacman_frame = next(pacman_sequence)
                if commands[0] < 0:
                    pacman_frame = pg.transform.flip(pacman_frame, 1, 0)
                elif commands[1] < 0:
                    pacman_frame = pg.transform.rotate(pacman_frame, 90)
                elif commands[1] > 0:
                    pacman_frame = pg.transform.rotate(pacman_frame, 270)
                last_time = current_time
                x += commands[0]
                y += commands[1]
            self._surface.blit(pacman_frame, (x, y))
            yield

    def _update_buttons(self) -> None:
        width = self._surface.get_width()
        height = self._surface.get_height() * 0.7

        size_play = self._scale.size(15, 5)
        size_leaderboard = self._scale.size(33, 5)
        size_settings = self._scale.size(25, 5)
        size_exit = self._scale.size(15, 5)

        pos_play = ((width / 2) - (size_play[0] / 2), height / 4)
        pos_leaderboard = ((width / 2) - (size_leaderboard[0] / 2), height / 4 * 2)
        pos_settings = ((width / 2) - (size_settings[0] / 2), height / 4 * 3)
        pos_exit = ((width / 2) - (size_exit[0] / 2), height / 4 * 4)

        self._menu_button_play = MenuButton(
            pos_play,
            size_play,
            "Play",
            self._surface,
            ViewAction.GAME)

        self._menu_button_leaderboard = MenuButton(
            pos_leaderboard,
            size_leaderboard,
            "Leaderboard",
            self._surface,
            ViewAction.LEADERBOARD)

        self._menu_button_settings = MenuButton(
            pos_settings,
            size_settings,
            "Settings",
            self._surface,
            ViewAction.SETTINGS)

        self._menu_button_exit = MenuButton(
            pos_exit,
            size_exit,
            "Exit",
            self._surface,
            ViewAction.EXIT)

    def run(self):

        self._update_buttons()
        animation = self._background_animation()

        while self._running:
            self._surface.fill('lightcyan')
            next(animation)
            self._get_events()
            self._menu_button_play.render()
            self._menu_button_leaderboard.render()
            self._menu_button_settings.render()
            self._menu_button_exit.render()
            pg.display.update()

