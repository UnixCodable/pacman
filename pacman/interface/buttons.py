import pygame as pg

from enum import Enum
from tools.scales import Scaling
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

        self._tag = tag
        self._action = action
        self._surface = surface
        self._scale = Scaling(self._surface)
        self._pos = pos
        self._clickable = False

        self._rect = pg.Rect(pos, dimensions)
        self._arrow_cursor = pg.Cursor(pg.SYSTEM_CURSOR_ARROW)
        self._clickable_cursor = pg.Cursor(pg.SYSTEM_CURSOR_HAND)
        # self._sound = pg.mixer.Sound("assets/sound/button.mp3")

    @abstractmethod
    def render(self) -> None:
        pass

    @abstractmethod
    def _collide(self) -> None:
        pass


class MenuButton(Button):
    def __init__(self,
                 pos: tuple[int, int],
                 dimensions: tuple[int, int],
                 tag: str,
                 surface: pg.Surface,
                 action: Enum) -> None:

        super().__init__(pos, tag, surface, dimensions, action)

        self._color = pg.Color('lightslateblue')
        self._color_hover = pg.Color('goldenrod1')
        self._font = pg.font.Font("pacman/interface/assets/fonts/Emulogic.ttf",
                                  self._scale.text(2.5))

    def render(self) -> None:

        self._collide()

        center_text = ((self._rect.width - self._text.get_width()) / 2,
                       (self._rect.height - self._text.get_height()) / 2 * 0.6)

        self._surface.blit(self._text,
                           (self._pos[0] + center_text[0],
                            self._pos[1] + center_text[1]))

    def _collide(self) -> None:
        mouse = pg.mouse.get_pos()

        if self._rect.collidepoint(mouse):

            # if self._clickable is False:
            #     pg.mixer.Channel(1).play(self._sound)
            self._text = self._font.render(self._tag, True, self._color_hover)
            self._clickable = True

            pg.draw.rect(self._surface, self._color_hover, self._rect, 6, 10)
            pg.mouse.set_cursor(self._clickable_cursor)

            for event in pg.event.get():
                if event.type == pg.MOUSEBUTTONUP and event.button == 1:
                    pg.event.post(pg.event.Event(self._action.value))
                    pg.mouse.set_cursor(self._arrow_cursor)

            return

        elif self._clickable is True:
            self._clickable = False
            pg.mouse.set_cursor(self._arrow_cursor)

        self._text = self._font.render(self._tag, True, self._color)
        pg.draw.rect(self._surface, self._color, self._rect, 6, 10)

        return
