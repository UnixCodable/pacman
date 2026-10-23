"""Tests for the configuration parser."""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from pacman.config import ConfigError, ConfigParser


def write(tmp_path: Path, text: str, name: str = "config.json") -> str:
    """Write a temporary config file and return its path."""
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_valid_config(tmp_path: Path) -> None:
    cfg = {"lives": 5, "seed": 7, "highscore_filename": "hs.json",
           "levels": [{"width": 10, "height": 12}] * 10}
    c = ConfigParser().load_config(write(tmp_path, json.dumps(cfg)))
    assert c.lives == 5
    assert c.seed == 7
    assert c.highscore_filename == "hs.json"
    assert len(c.levels) == 10
    assert c.levels[0].width == 10


def test_comments_are_ignored(tmp_path: Path) -> None:
    text = '# a comment\n{\n  // another\n  "lives": 4\n}\n'
    c = ConfigParser().load_config(write(tmp_path, text))
    assert c.lives == 4


def test_missing_file() -> None:
    with pytest.raises(ConfigError, match="not found"):
        ConfigParser().load_config("/does/not/exist.json")


def test_directory_instead_of_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        ConfigParser().load_config(str(tmp_path))


@pytest.mark.parametrize("text", ["", "{,}", '{"lives": 3,}', "not json"])
def test_invalid_json(tmp_path: Path, text: str) -> None:
    with pytest.raises(ConfigError, match="invalid JSON"):
        ConfigParser().load_config(write(tmp_path, text))


@pytest.mark.parametrize("text", ["[1, 2]", '"hello"', "42", "null"])
def test_top_level_not_object(tmp_path: Path, text: str) -> None:
    with pytest.raises(ConfigError, match="JSON object"):
        ConfigParser().load_config(write(tmp_path, text))


def test_binary_file(tmp_path: Path) -> None:
    p = tmp_path / "bin.json"
    p.write_bytes(b"\xff\xfe\x00\x80")
    with pytest.raises(ConfigError):
        ConfigParser().load_config(str(p))


@pytest.mark.parametrize("bad", ["three", -5, 1000, True, 3.5, None, [3]])
def test_bad_lives_falls_back_to_default(
        tmp_path: Path, bad: Any,
        caplog: pytest.LogCaptureFixture) -> None:
    path = write(tmp_path, json.dumps({"lives": bad}))
    with caplog.at_level(logging.WARNING):
        c = ConfigParser().load_config(path)
    assert c.lives == 3
    assert "lives" in caplog.text


def test_empty_object_gives_all_defaults(tmp_path: Path) -> None:
    c = ConfigParser().load_config(write(tmp_path, "{}"))
    assert c.lives == 3
    assert c.seed == 42
    assert c.level_max_time == 90
    assert c.points_per_ghost == 200
    assert c.highscore_filename == "highscores.json"
    assert len(c.levels) == 10


def test_unknown_keys_ignored(tmp_path: Path) -> None:
    c = ConfigParser().load_config(
        write(tmp_path, '{"lives": 2, "banana": [1, 2, 3]}'))
    assert c.lives == 2


def test_empty_filename_uses_default(tmp_path: Path) -> None:
    c = ConfigParser().load_config(
        write(tmp_path, '{"highscore_filename": "  "}'))
    assert c.highscore_filename == "highscores.json"


@pytest.mark.parametrize("levels", [[], "abc", {"a": 1}, 5, None])
def test_bad_levels_container(tmp_path: Path, levels: Any) -> None:
    c = ConfigParser().load_config(
        write(tmp_path, json.dumps({"levels": levels})))
    assert len(c.levels) == 10


def test_level_entry_not_object(tmp_path: Path) -> None:
    c = ConfigParser().load_config(
        write(tmp_path, json.dumps({"levels": ["oops"]})))
    assert len(c.levels) == 10
    assert c.levels[0].width == 15


def test_short_levels_list_is_padded_not_replaced(tmp_path: Path) -> None:
    data = {"levels": [{"width": 9, "height": 9}] * 3}
    c = ConfigParser().load_config(write(tmp_path, json.dumps(data)))
    assert len(c.levels) == 10
    assert c.levels[0].width == 9    # user's levels are kept
    assert c.levels[9].width == 15   # padding uses defaults


def test_bad_level_size_uses_default(tmp_path: Path) -> None:
    data = {"levels": [{"width": -1, "height": "x"}]}
    c = ConfigParser().load_config(write(tmp_path, json.dumps(data)))
    assert (c.levels[0].width, c.levels[0].height) == (15, 15)


# ---- end-to-end tests of the command line ----

def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "pac-man.py", *args],
                          capture_output=True, text=True)


def test_cli_no_argument() -> None:
    r = run_cli()
    assert r.returncode == 1
    assert "Usage" in r.stdout
    assert "Traceback" not in r.stderr


def test_cli_missing_file() -> None:
    r = run_cli("nope.json")
    assert r.returncode == 1
    assert "Error" in r.stdout
    assert "Traceback" not in r.stderr


def test_cli_valid(tmp_path: Path) -> None:
    r = run_cli(write(tmp_path, "{}"))
    assert r.returncode == 0
    assert "Traceback" not in r.stderr