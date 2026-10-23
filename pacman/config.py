"""Configuration loading and validation for the Pac-Man game."""

import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

MIN_LEVELS = 10
DEFAULT_WIDTH = 15
DEFAULT_HEIGHT = 15
# Placeholder bounds: we will adjust them once we know what the
# assigned A-Maze-ing package accepts.
MIN_SIZE = 5
MAX_SIZE = 50
DEFAULT_HIGHSCORE_FILE = "highscores.json"


class ConfigError(Exception):
    """Fatal configuration error (the game cannot start)."""


@dataclass
class LevelConfig:
    """Size of one level's maze."""

    width: int
    height: int


@dataclass
class Config:
    """All game parameters, validated."""

    highscore_filename: str
    levels: list[LevelConfig]
    lives: int
    pacgum: int
    points_per_pacgum: int
    points_per_super_pacgum: int
    points_per_ghost: int
    seed: int
    level_max_time: int


class ConfigParser:
    """Reads a JSON-with-comments file and builds a valid Config."""

    def load_config(self, path: str) -> Config:
        """Load and validate the configuration file.

        Args:
            path: Path to the JSON configuration file.

        Returns:
            A fully validated Config (defaults used for bad values).

        Raises:
            ConfigError: If the file is unreadable or not a JSON object.
        """
        data = self.read_raw_config(path)
        return Config(
            highscore_filename=self.get_str(
                data, "highscore_filename", DEFAULT_HIGHSCORE_FILE),
            levels=self.parse_levels(data),
            lives=self.get_int(data, "lives", 3, 1, 99),
            pacgum=self.get_int(data, "pacgum", 42, 1, 10_000),
            points_per_pacgum=self.get_int(
                data, "points_per_pacgum", 10, 0, 1_000_000),
            points_per_super_pacgum=self.get_int(
                data, "points_per_super_pacgum", 50, 0, 1_000_000),
            points_per_ghost=self.get_int(
                data, "points_per_ghost", 200, 0, 1_000_000),
            seed=self.get_int(data, "seed", 42, 0, 2**31 - 1),
            level_max_time=self.get_int(
                data, "level_max_time", 90, 5, 3600),
        )

    def strip_comment(self, text: str) -> str:
        """Blank out whole-line comments starting with '#' or '//'."""
        keep: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                keep.append("")  # keep line numbers aligned
            else:
                keep.append(line)
        return "\n".join(keep)

    def read_raw_config(self, path: str) -> dict[str, Any]:
        """Read the file and return the parsed top-level JSON object."""
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError as e:
            raise ConfigError(f"file not found: {path}") from e
        except PermissionError as e:
            raise ConfigError(f"cannot read file: {path}") from e
        except UnicodeDecodeError as e:
            raise ConfigError(f"file is not valid UTF-8 text: {path}") from e
        except OSError as e:
            raise ConfigError(f"problem reading {path}: {e.strerror}") from e

        try:
            data = json.loads(self.strip_comment(text))
        except json.JSONDecodeError as e:
            raise ConfigError(
                f"invalid JSON at line {e.lineno}: {e.msg}") from e

        if not isinstance(data, dict):
            raise ConfigError("top level must be a JSON object")
        return data

    def get_int(self, data: dict[str, Any], key: str, default: int,
                min_value: int, max_value: int,
                context: str = "") -> int:
        """Return data[key] if it is an int in range, else the default."""
        name = f"{context}{key}"
        if key not in data:
            logger.warning("missing key '%s', using default %d",
                           name, default)
            return default

        value = data[key]
        # type(...) is int, not isinstance: True/False are ints in Python
        if type(value) is not int:
            logger.warning("'%s' must be an integer, using default %d",
                           name, default)
            return default

        if value < min_value or value > max_value:
            logger.warning("'%s'=%d out of range [%d, %d], using default %d",
                           name, value, min_value, max_value, default)
            return default
        return value

    def get_str(self, data: dict[str, Any], key: str, default: str) -> str:
        """Return data[key] if it is a non-empty string, else the default."""
        if key not in data:
            logger.warning("missing key '%s', using default '%s'",
                           key, default)
            return default

        value = data[key]
        if not isinstance(value, str) or not value.strip():
            logger.warning("'%s' must be a non-empty string, "
                           "using default '%s'", key, default)
            return default
        return value.strip()

    def parse_levels(self, data: dict[str, Any]) -> list[LevelConfig]:
        """Build the list of levels, padding to at least MIN_LEVELS."""
        raw = data.get("levels")
        if not isinstance(raw, list) or not raw:
            logger.warning("'levels' missing or not a non-empty list, "
                           "using %d default levels", MIN_LEVELS)
            return [LevelConfig(DEFAULT_WIDTH, DEFAULT_HEIGHT)
                    for _ in range(MIN_LEVELS)]

        result: list[LevelConfig] = []
        for i, entry in enumerate(raw):
            if not isinstance(entry, dict):
                logger.warning("level %d is not an object, "
                               "using default size", i)
                result.append(LevelConfig(DEFAULT_WIDTH, DEFAULT_HEIGHT))
                continue
            ctx = f"levels[{i}]."
            width = self.get_int(entry, "width", DEFAULT_WIDTH,
                                 MIN_SIZE, MAX_SIZE, ctx)
            height = self.get_int(entry, "height", DEFAULT_HEIGHT,
                                  MIN_SIZE, MAX_SIZE, ctx)
            result.append(LevelConfig(width, height))

        if len(result) < MIN_LEVELS:
            logger.warning("only %d levels given, padding to %d",
                           len(result), MIN_LEVELS)
            while len(result) < MIN_LEVELS:
                result.append(LevelConfig(DEFAULT_WIDTH, DEFAULT_HEIGHT))
        return result
