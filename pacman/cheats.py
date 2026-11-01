from enum import Enum
from dataclasses import dataclass

SPEED_BOOST_FACTOR = 1.6
LOW_TIME_SECONDS = 5.0


class Cheat(Enum):

    INVINCIBLE = "invincibility"
    FREEZE_GHOSTS = "ghost freeze"
    SPEED_BOOST = "speed boost"
    EXTRA_LIFE = "extra life"
    SKIP_LEVEL = "skip level"
    POWER_UP = "power-up"
    LOW_TIME = "low time"


@dataclass
class Cheats:

    """Stores cheat settings shared across every level in a run."""

    enabled: bool = False
    invincible: bool = False
    freeze_ghosts: bool = False
    speed_boost: bool = False
    used: bool = False
