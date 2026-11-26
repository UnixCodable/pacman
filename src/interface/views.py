from time import sleep, time
from typing import Generator

import pygame as pg
import sys
from itertools import cycle

from src.game import GameState
from src.ghost import FRIGHTENED_SLOWDOWN
from src.maze import Direction
from .buttons import MenuButton
from ..config import ConfigParser
from ..session import GameSession
from .tools.scales import Scaling
from pyvidplayer2 import Video
from abc import ABC, abstractmethod
from .actions.views_actions import ViewAction

MAP_PATH = "src/interface/assets/map"

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
    def __init__(self, surface: pg.Surface):
        super().__init__(surface)
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
    def __init__(self, surface: pg.Surface):
        super().__init__(surface)
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

    def __init__(self, surface: pg.Surface):

        super().__init__(surface)

        self._running = True
        self._config = ConfigParser().load_config("config.json")
        self._session = GameSession(self._config)
        self._accumulated = 0

    def _calc_pos(self, pos: tuple[float, float], direction: Direction,
                  accumulator: float, time_interval: float):

        case_interval = self._tile_size * 2
        interval = case_interval * (1.0 - accumulator / time_interval)

        if direction == Direction.EAST:
            n_pos = (pos[0] - interval, pos[1])
        elif direction == Direction.WEST:
            n_pos = (pos[0] + interval, pos[1])
        elif direction == Direction.NORTH:
            n_pos = (pos[0], pos[1] + interval)
        elif direction == Direction.SOUTH:
            n_pos = (pos[0], pos[1] - interval)
        else:
            n_pos = (pos[0], pos[1])

        return n_pos

    def _draw_pellets(self):
        pellet_frame = pg.image.load('src/interface/assets/items/tile_0009.png')
        power_frame = pg.image.load('src/interface/assets/items/tile_0010.png')
        pellet_frame = pellet_frame.convert_alpha()
        pellet_frame = pg.transform.scale(pellet_frame, (self._tile_size, self._tile_size))
        power_frame = power_frame.convert_alpha()
        power_frame = pg.transform.scale(power_frame, (self._tile_size, self._tile_size))

        while self._running:

            for pos in self._session.game.pacgums:
                pos_scaled = (pos[0] * self._tile_size * 2 + self._tile_size,
                              pos[1] * self._tile_size * 2 + self._tile_size)
                self._surface.blit(pellet_frame, pos_scaled)

            for pos in self._session.game.super_pacgums:
                pos_scaled = (pos[0] * self._tile_size * 2 + self._tile_size,
                              pos[1] * self._tile_size * 2 + self._tile_size)
                self._surface.blit(power_frame, pos_scaled)

            yield

    def _draw_ghost(self, maze: pg.Surface, ghost_number: int):

        ghost = [
            pg.image.load(f'src/interface/assets/ghost/{ghost_number}/tile_0001.png'),
            pg.image.load(f'src/interface/assets/ghost/{ghost_number}/tile_0002.png'),
            pg.image.load(f'src/interface/assets/ghost/{ghost_number}/tile_0003.png'),
            pg.image.load(f'src/interface/assets/ghost/{ghost_number}/tile_0002.png'),
        ]

        frightened = [
            pg.image.load('src/interface/assets/ghost/frightened/tile_0001.png'),
            pg.image.load('src/interface/assets/ghost/frightened/tile_0002.png'),
            pg.image.load('src/interface/assets/ghost/frightened/tile_0003.png'),
            pg.image.load('src/interface/assets/ghost/frightened/tile_0002.png'),
        ]

        faces = [
            pg.image.load('src/interface/assets/faces/face_0001.png'),
            pg.image.load('src/interface/assets/faces/face_0002.png'),
            pg.image.load('src/interface/assets/faces/face_0003.png'),
            pg.image.load('src/interface/assets/faces/face_0004.png'),
            pg.image.load('src/interface/assets/faces/face_0005.png'),
            pg.image.load('src/interface/assets/faces/face_0006.png')
        ]

        ghost_sequence = cycle(ghost)
        frightened_sequence = cycle(frightened)
        face_sequence = cycle(faces)
        for _ in range(ghost_number):
            next(face_sequence)
        last_animation = 0.0
        last_face = 0.0
        # last_pos = self._session.game.ghosts[ghost_number].position
        # accumulator = 0

        while self._running:
            entity = self._session.game.ghosts[ghost_number]
            frightened_status = entity.frightened

            pos = entity.position
            pos_scaled = (pos[0] * self._tile_size * 2 + self._tile_size,
                          pos[1] * self._tile_size * 2 + self._tile_size)

            accumulator = entity.accumulator
            move_interval = entity.move_interval

            direction = entity.direction
            if frightened_status:
                exact_pos = self._calc_pos(
                    pos_scaled, direction, accumulator, move_interval * FRIGHTENED_SLOWDOWN)
            else:
                exact_pos = self._calc_pos(
                    pos_scaled, direction, accumulator, move_interval)

            current_time = time() / 1000

            if current_time - 0.00007 > last_animation:
                if frightened_status:
                    ghost_frame = next(frightened_sequence)
                    next(ghost_sequence)
                else:
                    ghost_frame = next(ghost_sequence)
                    next(frightened_sequence)
                ghost_frame = pg.transform.scale(
                    ghost_frame,
                    (self._tile_size, self._tile_size)
                )
                last_animation = current_time

            if current_time - 0.007 > last_face:
                face = next(face_sequence)
                face = pg.transform.scale(
                                    face,
                                    (self._tile_size, self._tile_size)
                                )
                last_face = current_time

            if not frightened_status:
                ghost_frame.blit(face, (0, 0))
            self._surface.blit(ghost_frame, exact_pos)

            yield

    def _draw_pacman(self, maze: pg.Surface):
        pacman = [
            pg.image.load('src/interface/assets/pacman/tile_0001.png'),
            pg.image.load('src/interface/assets/pacman/tile_0002.png'),
            pg.image.load('src/interface/assets/pacman/tile_0003.png'),
            pg.image.load('src/interface/assets/pacman/tile_0002.png'),
        ]

        player = self._session.game.player
        game = self._session.game

        pacman_sequence = cycle(pacman)
        last_dir = Direction.EAST
        last_time = 0.0

        while self._running:
            accumulator = game.accumulator

            pos = player.position
            pos_scaled = (pos[0] * self._tile_size * 2 + self._tile_size,
                          pos[1] * self._tile_size * 2 + self._tile_size)

            current_time = time() / 1000
            direction = player.direction
            exact_pos = self._calc_pos(pos_scaled, direction, accumulator, game.player_interval)

            if current_time - 0.00007 > last_time:
                pacman_frame = next(pacman_sequence)
                pacman_frame = pg.transform.scale(
                    pacman_frame,
                    (self._tile_size, self._tile_size)
                )
                if direction is None:
                    direction = last_dir
                if direction == Direction.WEST:
                    pacman_frame = pg.transform.flip(pacman_frame, 1, 0)
                    last_dir = Direction.WEST
                elif direction == Direction.NORTH:
                    pacman_frame = pg.transform.rotate(pacman_frame, 90)
                    last_dir = Direction.NORTH
                elif direction == Direction.SOUTH:
                    pacman_frame = pg.transform.rotate(pacman_frame, 270)
                    last_dir = Direction.SOUTH
                else:
                    last_dir = Direction.EAST
                last_time = current_time

            self._surface.blit(pacman_frame, exact_pos)

            yield

    def _draw_maze(self) -> pg.Surface:
        width = self._session.game.maze.width
        height = self._session.game.maze.height

        walls = {
            1: pg.image.load(f"{MAP_PATH}/tile_0067.png"),
            2: pg.image.load(f"{MAP_PATH}/tile_0087.png"),
            3: pg.image.load(f"{MAP_PATH}/tile_0080.png"),
            4: pg.image.load(f"{MAP_PATH}/tile_0068.png"),
            5: pg.image.load(f"{MAP_PATH}/tile_0063.png"),
            6: pg.image.load(f"{MAP_PATH}/tile_0101.png"),
            7: pg.image.load(f"{MAP_PATH}/tile_0091.png"),
            8: pg.image.load(f"{MAP_PATH}/tile_0086.png"),
            9: pg.image.load(f"{MAP_PATH}/tile_0061.png"),
            10: pg.image.load(f"{MAP_PATH}/tile_0099.png"),
            11: pg.image.load(f"{MAP_PATH}/tile_0071.png"),
            12: pg.image.load(f"{MAP_PATH}/tile_0100.png"),
            13: pg.image.load(f"{MAP_PATH}/tile_0072.png"),
            14: pg.image.load(f"{MAP_PATH}/tile_0090.png"),
            15: pg.image.load(f"{MAP_PATH}/tile_0219.png"),
        }

        tile_size = 16
        surface = pg.Surface((width * tile_size * 2 + tile_size,
                              height * tile_size * 2 + tile_size), pg.SRCALPHA)
        surface.fill(
            'gray17',
            pg.Rect(5, 5, surface.get_width() - 10, surface.get_height() - 10)
        )
        walls_pos = self._session.game.maze.walls
        intersections = {}

        for y in range(height + 1):
            for x in range(width + 1):
                intersections.update({(x, y): 0})

        for pos_y in range(len(walls_pos)):
            for pos_x, wall in enumerate(walls_pos[pos_y]):
                y = tile_size + (pos_y * tile_size * 2)
                x = tile_size + (pos_x * tile_size * 2)
                for w in wall:
                    if w == Direction.EAST:
                        surface.blit(walls[3], (x + tile_size, y))
                        try:
                            temp = intersections[(pos_x + 1, pos_y)] + 1
                            intersections.update({(pos_x + 1, pos_y): temp})
                            temp = intersections[(pos_x + 1, pos_y + 1)] + 10
                            intersections.update({(pos_x + 1, pos_y + 1): temp})
                        except KeyError:
                            pass
                    elif w == Direction.WEST:
                        surface.blit(walls[3], (x - tile_size, y))
                        try:
                            temp = intersections[(pos_x, pos_y)] + 1
                            intersections.update({(pos_x, pos_y): temp})
                            temp = intersections[(pos_x, pos_y + 1)] + 10
                            intersections.update({(pos_x, pos_y + 1): temp})
                        except KeyError:
                            pass
                    elif w == Direction.NORTH:
                        surface.blit(walls[12], (x, y - tile_size))
                        try:
                            temp = intersections[(pos_x, pos_y)] + 1000
                            intersections.update({(pos_x, pos_y): temp})
                            temp = intersections[(pos_x + 1, pos_y)] + 100
                            intersections.update({(pos_x + 1, pos_y): temp})
                        except KeyError:
                            pass
                    elif w == Direction.SOUTH:
                        surface.blit(walls[12], (x, y + tile_size))
                        try:
                            temp = intersections[(pos_x, pos_y + 1)] + 1000
                            intersections.update({(pos_x, pos_y + 1): temp})
                            temp = intersections[(pos_x + 1, pos_y + 1)] + 100
                            intersections.update({(pos_x + 1, pos_y + 1): temp})
                        except KeyError:
                            pass

        for pos, inter in intersections.items():
            x = pos[0] * tile_size * 2
            y = pos[1] * tile_size * 2
            binary = int('0b' + str(inter).replace('2', '1'), 2)
            try:
                surface.blit(walls[binary], (x, y))
            except KeyError:
                pass

        self._maze_scale = self._scale.maze(surface)
        self._tile_size = tile_size * self._maze_scale
        surface = pg.transform.scale_by(surface, self._maze_scale).convert_alpha()

        return surface

    def _update_hud(self, maze: pg.Surface) -> Generator:
        maze_width = maze.get_width()
        screen_width = self._surface.get_width()
        screen_height = self._surface.get_height()

        level_font = pg.font.Font("src/interface/assets/fonts/Emulogic.ttf",
                                  self._scale.text(2.5))

        level_text = level_font.render(f"LEVEL {self._session.level_number}",
                                       1, "white")

        hud_size = (screen_width - maze_width, screen_height)
        level_pos = ((hud_size[0] / 2 - level_text.get_width() / 2) + maze_width, 30)

        while self._running:

            self._surface.blit(level_text, (level_pos))

            yield

    def _get_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.event.post(pg.event.Event(ViewAction.EXIT.value))
                self._running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_RIGHT:
                    self._session.set_direction(Direction.EAST)
                if event.key == pg.K_LEFT:
                    self._session.set_direction(Direction.WEST)
                if event.key == pg.K_UP:
                    self._session.set_direction(Direction.NORTH)
                if event.key == pg.K_DOWN:
                    self._session.set_direction(Direction.SOUTH)
                if event.key == pg.K_l:
                    self._session.game.force_win()

    def run(self):

        state = self._session.game.state

        while self._running:

            maze = self._draw_maze()
            pacman = self._draw_pacman(maze)
            pellet = self._draw_pellets()
            hud = self._update_hud(maze)
            ghosts = []
            for ghost in range(len(self._session.game.ghosts)):
                ghosts.append(self._draw_ghost(maze, ghost))

            clock = pg.time.Clock()

            while self._running:
                state = self._session.game.state
                self._dt = clock.tick(60) / 1000
                if state == GameState.LEVEL_WON:
                    self._session.update(self._dt)
                    state = self._session.game.state
                    break
                if state == GameState.GAME_OVER:
                    pg.event.post(pg.event.Event(ViewAction.MENU.value))
                    self._running = False
                    break
                if state == GameState.VICTORY:
                    pg.event.post(pg.event.Event(ViewAction.MENU.value))
                    self._running = False
                    break
                self._surface.fill('mediumpurple4')
                self._surface.blit(maze, (0, 0))
                next(hud)
                next(pellet)
                next(pacman)
                for ghost in ghosts:
                    next(ghost)
                self._get_events()
                self._session.update(self._dt)
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

        self._footer = pg.image.load('src/interface/assets/footer.png')

    def _get_events(self):
        for event in pg.event.get(exclude=(pg.KEYUP, pg.MOUSEBUTTONUP)):
            if event.type == pg.QUIT:
                pg.event.post(pg.event.Event(ViewAction.EXIT.value))
                self._running = False
            if event.type == ViewAction.GAME.value:
                pg.event.post(pg.event.Event(ViewAction.GAME.value))
                self._running = False
            if event.type == ViewAction.EXIT.value:
                pg.event.post(pg.event.Event(ViewAction.EXIT.value))
                self._running = False

    def _background_animation(self) -> Generator:
        pacman = [
            pg.image.load('src/interface/assets/pacman/tile_0001.png'),
            pg.image.load('src/interface/assets/pacman/tile_0002.png'),
            pg.image.load('src/interface/assets/pacman/tile_0003.png'),
            pg.image.load('src/interface/assets/pacman/tile_0002.png'),
        ]
        x = 0
        y = 0
        pacman_sequence = cycle(pacman)
        last_time = 0.0
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
            self._menu_button_play.render()
            self._menu_button_leaderboard.render()
            self._menu_button_settings.render()
            self._menu_button_exit.render()
            self._get_events()
            pg.display.update()
