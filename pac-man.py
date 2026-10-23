"""Entry point of the Pac-Man game."""

import logging
import sys

from pacman.config import ConfigError, ConfigParser


def main() -> int:
    """Parse arguments, load the config and start the game."""
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s: %(message)s")

    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py <config.json>")
        return 1

    try:
        config = ConfigParser().load_config(sys.argv[1])
    except ConfigError as e:
        print(f"Error: {e}")
        return 1

    logging.info("Config loaded: %d levels, %d lives",
                 len(config.levels), config.lives)
    # Later: start the game here.
    return 0


if __name__ == "__main__":
    sys.exit(main())
