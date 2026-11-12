"""Cheat mode: switches that let a reviewer reach every feature quickly."""

from dataclasses import dataclass
from enum import Enum, auto

SPEED_BOOST_FACTOR = 1.5


class Cheat(Enum):
    """Cheats that can be activated during a game session."""

    INVINCIBLE = auto()
    FREEZE_GHOSTS = auto()
    SPEED_BOOST = auto()
    EXTRA_LIFE = auto()
    SKIP_LEVEL = auto()
    POWER_UP = auto()
    LOW_TIME = auto()


@dataclass
class Cheats:
    """Store the cheat switches shared by every level of one run."""

    enabled: bool = False
    invincible: bool = False
    freeze_ghosts: bool = False
    speed_boost: bool = False
    used: bool = False
