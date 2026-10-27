import pygame as pg
import sys
from views import Menu, Settings, Leaderboard, Game
from actions.views_actions import ViewAction

pg.init()
pg.display.set_caption("Pacman: 50 years later")


class Window:
    def __init__(self):
        pg.display.set_mode((1920, 1080))
        self._running = True
        self.menu = Menu()
        self.settings = Settings()
        self.leaderboard = Leaderboard()
        self.game = Game()

    def launch(self) -> None:
        self.menu.run()
        while self._running:
            for event in pg.event.get():
                if event.type == ViewAction.SETTINGS.value:
                    self.settings.run()
                if event.type == ViewAction.LEADERBOARD.value:
                    self.leaderboard.run()
                if event.type == ViewAction.EXIT.value:
                    self._running = False
                    break
                if event.type == ViewAction.GAME.value:
                    self.game.run()
        pg.quit()
        sys.exit(0)


if __name__ == "__main__":
    display = Window()
    display.launch()
