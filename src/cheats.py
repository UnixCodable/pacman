"""Cheat mode: switches that let a reviewer reach every feature quickly."""

from dataclasses import dataclass
from enum import Enum

SPEED_BOOST_FACTOR = 1.5
LOW_TIME_SECONDS = 10.0


class Cheat(Enum):
    """Every cheat a reviewer can trigger."""

    INVINCIBLE = "invincibility"
    FREEZE_GHOSTS = "ghost freeze"
    SPEED_BOOST = "speed boost"
    EXTRA_LIFE = "extra life"
    SKIP_LEVEL = "skip level"
    POWER_UP = "power-up"
    LOW_TIME = "low time"


@dataclass
class Cheats:
    """Store the cheat switches shared by every level of one run."""

    enabled: bool = False
    invincible: bool = False
    freeze_ghosts: bool = False
    speed_boost: bool = False
    used: bool = False
