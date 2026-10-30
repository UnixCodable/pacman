import pygame as pg
import sys
from pyvidplayer2 import Video
from views import Cinematics, Menu, Settings, Leaderboard, Game
from actions.views_actions import ViewAction

pg.init()
pg.display.set_caption("Pacman: 44 years later")


class Window:
    def __init__(self):
        self._surface = pg.display.set_mode((1440, 1080))
        self._running = True
        self._intro = Cinematics(
            Video('pacman/interface/assets/cinematics/intro.mp4'),
            self._surface
        )
        self._menu = Menu(self._surface)
        self._settings = Settings()
        self._leaderboard = Leaderboard()
        self._game = Game()

    def launch(self) -> None:
        self._intro.run()
        self._menu.run()
        while self._running:
            for event in pg.event.get():
                if event.type == ViewAction.SETTINGS.value:
                    self._settings.run()
                if event.type == ViewAction.LEADERBOARD.value:
                    self._leaderboard.run()
                if event.type == ViewAction.GAME.value:
                    self._game.run()
                if event.type == ViewAction.EXIT.value:
                    self._running = False
                    break
        pg.quit()
        sys.exit(0)


if __name__ == "__main__":
    display = Window()
    display.launch()
