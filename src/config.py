"""Configuration loading and validation for the Pac-Man game."""

import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

MAX_LEVELS = 10

DEFAULT_WIDTH = 15
DEFAULT_HEIGHT = 15
DEFAULT_GHOST_SPEED = 1.0
DEFAULT_LEVEL_MAX_TIME = 90
DEFAULT_GHOST_COUNT = 2

MIN_SIZE = 5
MAX_SIZE = 50

DEFAULT_HIGHSCORE_FILE = "highscores.json"


class ConfigError(Exception):
    """Fatal configuration error (the game cannot start)."""


@dataclass
class LevelConfig:
    """Settings that control the difficulty of one level."""

    width: int
    height: int
    ghost_speed: float
    level_max_time: int
    ghost_count: int


@dataclass
class Config:
    """All game parameters, validated."""

    highscore_filename: str
    levels: list[LevelConfig]
    lives: int
    points_per_pacgum: int
    points_per_super_pacgum: int
    points_per_ghost: int
    seed: int


class ConfigParser:
    """Reads a JSON-with-comments file and builds a valid Config."""

    def load_config(self, path: str) -> Config:
        """Load and validate the configuration file."""
        data = self.read_raw_config(path)

        return Config(
            highscore_filename=self.get_str(
                data,
                "highscore_filename",
                DEFAULT_HIGHSCORE_FILE,
            ),
            levels=self.parse_levels(data),
            lives=self.get_int(data, "lives", 3, 1, 99),
            points_per_pacgum=self.get_int(
                data, "points_per_pacgum", 10, 0, 1_000_000
            ),
            points_per_super_pacgum=self.get_int(
                data, "points_per_super_pacgum", 50, 0, 1_000_000
            ),
            points_per_ghost=self.get_int(
                data, "points_per_ghost", 200, 0, 1_000_000
            ),
            seed=self.get_int(data, "seed", 42, 1, 2**31 - 1),
        )

    def strip_comment(self, text: str) -> str:
        """Blank out whole-line comments starting with '#' or '//'."""
        keep: list[str] = []

        for line in text.splitlines():
            stripped = line.strip()

            if stripped.startswith("#") or stripped.startswith("//"):
                keep.append("")
            else:
                keep.append(line)

        return "\n".join(keep)

    def read_raw_config(self, path: str) -> dict[str, Any]:
        """Read the file and return the parsed top-level JSON object."""
        try:
            with open(path, encoding="utf-8") as file:
                text = file.read()

        except FileNotFoundError as error:
            raise ConfigError(f"file not found: {path}") from error

        except PermissionError as error:
            raise ConfigError(f"cannot read file: {path}") from error

        except UnicodeDecodeError as error:
            raise ConfigError(
                f"file is not valid UTF-8 text: {path}"
            ) from error

        except OSError as error:
            raise ConfigError(
                f"problem reading {path}: {error.strerror}"
            ) from error

        try:
            data = json.loads(self.strip_comment(text))

        except json.JSONDecodeError as error:
            raise ConfigError(
                f"invalid JSON at line {error.lineno}: {error.msg}"
            ) from error

        except RecursionError as error:
            raise ConfigError("JSON is nested too deeply") from error

        if not isinstance(data, dict):
            raise ConfigError("top level must be a JSON object")

        return data

    def get_int(
        self,
        data: dict[str, Any],
        key: str,
        default: int,
        min_value: int,
        max_value: int,
        context: str = "",
    ) -> int:
        """Return an integer in range, otherwise use the default."""
        name = f"{context}{key}"

        if key not in data:
            logger.warning(
                "missing key '%s', using default %d",
                name,
                default,
            )
            return default

        value = data[key]

        if type(value) is not int:
            logger.warning(
                "'%s' must be an integer, using default %d",
                name,
                default,
            )
            return default

        if not min_value <= value <= max_value:
            logger.warning(
                "'%s'=%d out of range [%d, %d], using default %d",
                name,
                value,
                min_value,
                max_value,
                default,
            )
            return default

        return value

    def get_float(
        self,
        data: dict[str, Any],
        key: str,
        default: float,
        min_value: float,
        max_value: float,
        context: str = "",
    ) -> float:
        """Return a valid numeric setting, otherwise use the default."""
        name = f"{context}{key}"

        if key not in data:
            logger.warning(
                "missing key '%s', using default %.2f",
                name,
                default,
            )
            return default

        value = data[key]

        if type(value) not in (int, float):
            logger.warning(
                "'%s' must be a number, using default %.2f",
                name,
                default,
            )
            return default

        value = float(value)

        if not min_value <= value <= max_value:
            logger.warning(
                "'%s'=%.2f out of range [%.2f, %.2f], "
                "using default %.2f",
                name,
                value,
                min_value,
                max_value,
                default,
            )
            return default

        return value

    def get_str(
        self,
        data: dict[str, Any],
        key: str,
        default: str,
    ) -> str:
        """Return a non-empty string, otherwise use the default."""
        if key not in data:
            logger.warning(
                "missing key '%s', using default '%s'",
                key,
                default,
            )
            return default

        value = data[key]

        if not isinstance(value, str) or not value.strip():
            logger.warning(
                "'%s' must be a non-empty string, using default '%s'",
                key,
                default,
            )
            return default

        return value.strip()

    def parse_levels(
        self,
        data: dict[str, Any],
    ) -> list[LevelConfig]:
        """Parse between one and ten level configurations."""
        raw = data.get("levels")

        if not isinstance(raw, list) or not raw:
            logger.warning(
                "'levels' missing or invalid, using one default level"
            )
            raw = [{}]

        if len(raw) > MAX_LEVELS:
            raise ConfigError(
                f"a maximum of {MAX_LEVELS} levels is allowed; "
                f"received {len(raw)}"
            )

        result: list[LevelConfig] = []

        for index, entry in enumerate(raw):
            context = f"levels[{index}]."

            if not isinstance(entry, dict):
                logger.warning(
                    "level %d is not an object; using default settings",
                    index + 1,
                )
                entry = {}

            width = self.get_int(
                entry,
                "width",
                DEFAULT_WIDTH,
                MIN_SIZE,
                MAX_SIZE,
                context,
            )

            height = self.get_int(
                entry,
                "height",
                DEFAULT_HEIGHT,
                MIN_SIZE,
                MAX_SIZE,
                context,
            )

            ghost_speed = self.get_float(
                entry,
                "ghost_speed",
                DEFAULT_GHOST_SPEED,
                0.1,
                5.0,
                context,
            )

            level_max_time = self.get_int(
                entry,
                "level_max_time",
                DEFAULT_LEVEL_MAX_TIME,
                5,
                3600,
                context,
            )

            ghost_count = self.get_int(
                entry,
                "ghost_count",
                DEFAULT_GHOST_COUNT,
                1,
                10,
                context,
            )

            result.append(
                LevelConfig(
                    width=width,
                    height=height,
                    ghost_speed=ghost_speed,
                    level_max_time=level_max_time,
                    ghost_count=ghost_count,
                )
            )

        return result
