import pygame as pg
import sys
from pyvidplayer2 import Video
from abc import ABC, abstractmethod
from actions.views_actions import ViewAction


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
                pg.event.post(pg.event.Event(ViewAction.EXIT.value))
                self._running = False

    def run(self):
        while self._running:
            self._get_events()
            pg.image.frombuffer()
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
        self._video: Video = video
        self._video.set_speed(speed)
        self._video.seek_frame(begin_frame)
        self._surface = surface
        self._end_frame = end_frame if end_frame else 0
        self._running = True

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
        self._running = True
        self._surface = surface
        self._footer = pg.image.load('pacman/interface/assets/footer.png')

    def _get_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.event.post(pg.event.Event(ViewAction.EXIT.value))
                self._running = False

    def run(self):
        self._surface.fill('goldenrod2')

        surface_w = self._surface.get_width()
        surface_h = self._surface.get_height()
        footer_w = self._footer.get_width()

        footer_scale = ((surface_w * 100) / footer_w) / 100
        scaled_footer = pg.transform.scale_by(self._footer, footer_scale)

        while self._running:
            self._get_events()
            self._surface.blit(scaled_footer, (0, surface_h - scaled_footer.get_height()))
            pg.display.flip()
