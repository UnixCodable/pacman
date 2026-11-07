"""Application entry point and startup error handling."""


import logging
import os
from collections.abc import Callable, Sequence
from typing import Any

from src.config import ConfigParser, ConfigError
from src.maze_loader import MazeGenerationError

EXIT_INTERRUPTED = 130

USAGE = "Usage: python pac-man.py <config-file>"

logger = logging.getLogger(__name__)

UIRunner = Callable[[Any], int]


def configure_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )


def load_ui_runner() -> UIRunner | None:
    """Load the graphical interface without hiding missing dependencies."""
    try:
        import src.ui
    except ModuleNotFoundError as error:
        if error.name == "pacman.ui":
            return None
        raise

    return getattr(src.ui, "run", None)


def main(
    argv: Sequence[str],
    run_ui: UIRunner | None = None,
) -> int:
    """Load configuration and start the graphical application.

    Return an exit code instead of raising errors during normal operation.
    """
    configure_logging()

    if len(argv) != 2:
        print(USAGE)
        return 1

    try:
        config = ConfigParser().load_config(argv[1])

    except ConfigError as error:
        print(f"Error: {error}")
        return 1

    try:
        runner = run_ui or load_ui_runner()

        if runner is None:
            print("Error: the graphical interface is not available")
            return 1

        return runner(config)

    except KeyboardInterrupt:
        print("Interrupted")
        return EXIT_INTERRUPTED

    except MazeGenerationError as error:
        print(f"Error: {error}")
        return 1

    except Exception as error:
        if os.environ.get("PACMAN_DEBUG"):
            raise

        logger.debug(
            "Unexpected application error",
            exc_info=True,
        )
        print(f"Error: unexpected problem: {error}")
        return 1
