"""Load, validate, and save the Pac-Man high-score table."""
import json
import logging
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_ENTRIES = 10
MAX_NAME_LENGTH = 10
DEFAULT_NAME = "Player"


@dataclass
class HighscoreEntry:
    """One player's name and achieved score."""

    name: str
    score: int


def sanitize_name(raw: str) -> str:
    """Keep ASCII letters, digits, and spaces in a player name."""
    cleaned = "".join(
        char for char in raw
        if char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        or char in "abcdefghijklmnopqrstuvwxyz"
        or char in "0123456789"
        or char == " "
    )

    cleaned = cleaned.strip()[:MAX_NAME_LENGTH].strip()

    return cleaned if cleaned else DEFAULT_NAME


def is_valid_score(value: object) -> bool:
    """Return whether a score is a non-negative integer."""
    return type(value) is int and value >= 0


class HighscoreTable:
    """Manage a sorted table of the best Pac-Man scores."""

    def __init__(
        self,
        path: str | Path,
        limit: int = MAX_ENTRIES,
    ) -> None:
        if limit <= 0:
            raise ValueError("High-score limit must be positive.")

        self.path = Path(path)
        self.limit = limit
        self.entries: list[HighscoreEntry] = []

        self.load()

    def load(self) -> None:
        """Load valid entries from the JSON file without raising errors."""
        self.entries = []

        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)

        except FileNotFoundError:
            logger.info("High-score file does not exist: %s", self.path)
            return

        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            logger.warning(
                "Could not load high scores from %s: %s",
                self.path,
                error,
            )
            return

        if not isinstance(data, list):
            logger.warning("High-score file must contain a JSON list.")
            return

        for item in data:
            if (
                isinstance(item, dict)
                and isinstance(item.get("name"), str)
                and is_valid_score(item.get("score"))
            ):
                self.entries.append(
                    HighscoreEntry(
                        name=sanitize_name(item["name"]),
                        score=item["score"],
                    )
                )
            else:
                logger.warning("Ignoring invalid high-score entry: %r", item)

        self._sort()

    def _sort(self) -> None:
        """Sort scores from highest to lowest, preserving tie order."""
        self.entries.sort(
            key=lambda entry: entry.score,
            reverse=True,
        )
        self.entries = self.entries[:self.limit]

    def qualifies(self, score: int) -> bool:
        """Return whether a score would enter the high-score table."""
        if not is_valid_score(score):
            return False

        if len(self.entries) < self.limit:
            return True

        return score > self.entries[-1].score

    def add(self, name: str, score: int) -> int:
        """Add a qualifying score and return its zero-based rank."""
        if not is_valid_score(score) or not self.qualifies(score):
            return -1

        rank = sum(
            entry.score >= score
            for entry in self.entries
        )

        self.entries.insert(
            rank,
            HighscoreEntry(
                name=sanitize_name(name),
                score=score,
            ),
        )

        self._sort()
        return rank

    def save(self) -> bool:
        """Save the table atomically using a temporary file."""
        temporary_path: str | None = None

        try:
            # Ensure the destination folder exists.
            self.path.parent.mkdir(parents=True, exist_ok=True)

            # Create the temporary file in the same folder so that
            # os.replace() can perform an atomic replacement.
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary_path = file.name

                json.dump(
                    [asdict(entry) for entry in self.entries],
                    file,
                    indent=2,
                )
                file.write("\n")

            os.replace(temporary_path, self.path)
            return True

        except OSError as error:
            logger.error(
                "Could not save high scores to %s: %s",
                self.path,
                error,
            )
            return False

        finally:
            # Remove an unfinished temporary file if saving failed.
            if temporary_path is not None and os.path.exists(temporary_path):
                try:
                    os.unlink(temporary_path)
                except OSError:
                    logger.warning(
                        "Could not remove temporary high-score file: %s",
                        temporary_path,
                    )
