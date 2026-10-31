import pygame as pg

from enum import Enum
from abc import ABC, abstractmethod


class Button(ABC):
    """An abstract class for creating pygame buttons
    """
    def __init__(self,
                 pos: tuple[int, int],
                 tag: str,
                 surface: pg.Surface,
                 dimensions: tuple[int, int],
                 action: Enum) -> None:

        self._pos = pos
        self._tag = tag
        self._action = action
        self._surface = surface
        self._clickable = False

        self._rect = pg.Rect(pos, dimensions)
        self._arrow_cursor = pg.Cursor(pg.SYSTEM_CURSOR_ARROW)
        self._clickable_cursor = pg.Cursor(pg.SYSTEM_CURSOR_HAND)
        self._sound = pg.mixer.Sound("assets/sound/button.mp3")

    @abstractmethod
    def render(self) -> None:
        pass

    @abstractmethod
    def _collide(self) -> None:
        pass


class MenuButton(Button):
    def __init__(self,
                 pos: tuple[int, int],
                 tag: str,
                 surface: pg.Surface,
                 action: Enum) -> None:

        super().__init__(pos, tag, scale_size(0.15, 0.05), surface, action)

        self._color = pg.Color(255, 255, 255)
        self._color_hover = pg.Color(255, 228, 54)
        self._font = pg.font.Font("assets/fonts/Starjhol.ttf",
                                  scale_text(0.025))

    def render(self) -> None:

        self.text = self.font.render(self.tag, True, self.color)
        center_text = ((self.rect.width - self.text.get_width()) / 2,
                       (self.rect.height - self.text.get_height()) / 2 * 0.6)

        pg.draw.rect(self._surface, self.color, self.rect, 6, 10)
        self._surface.blit(self.text, (self.pos[0] + center_text[0],
                           self.pos[1] + center_text[1]))

        self._collide()

    def _collide(self) -> None:

        mouse = pg.mouse.get_pos()

        if self.rect.collidepoint(mouse):

            if self.clickable is False:
                pg.mixer.Channel(1).play(self.sound)

            self.clickable = True
            pg.mouse.set_cursor(self.clickable_cursor)
            pg.Surface.fill(
                Window.surface, self.color_hover, self.rect, pg.BLEND_MIN)
            pg.Surface.fill(
                self.text, self.color_hover, special_flags=pg.BLEND_MIN)

            for event in pg.event.get():
                if event.type == pg.MOUSEBUTTONUP and event.button == 1:
                    pg.event.post(pg.event.Event(self.action.value))
                    pg.mouse.set_cursor(self.arrow_cursor)

        elif self.clickable is True:
            self.clickable = False
            pg.mouse.set_cursor(self.arrow_cursor)
