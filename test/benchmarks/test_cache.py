"""Tests for benchmark cache resolution."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from aigverse.benchmarks import CACHE_ENV_VAR, benchmark_cache, set_benchmark_cache


@pytest.fixture(autouse=True)
def _clear_override() -> None:
    """Clears an override left behind by a previous test."""
    set_benchmark_cache(None)


def test_the_explicit_override_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`set_benchmark_cache` takes precedence over the environment.

    Args:
        tmp_path: Directory used as the override.
        monkeypatch: Used to set a competing environment variable.
    """
    monkeypatch.setenv(CACHE_ENV_VAR, str(tmp_path / "from-env"))
    set_benchmark_cache(tmp_path / "explicit")

    assert benchmark_cache() == (tmp_path / "explicit").resolve()


def test_the_environment_variable_is_used(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With no override, the environment decides.

    Args:
        tmp_path: Directory pointed at by the variable.
        monkeypatch: Used to set the variable.
    """
    monkeypatch.setenv(CACHE_ENV_VAR, str(tmp_path))

    assert benchmark_cache() == tmp_path.resolve()


def test_clearing_the_override_falls_back(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Passing None must restore the lower-precedence sources.

    Args:
        tmp_path: Directory used for both sources in turn.
        monkeypatch: Used to set the environment variable.
    """
    monkeypatch.setenv(CACHE_ENV_VAR, str(tmp_path / "from-env"))
    set_benchmark_cache(tmp_path / "explicit")
    assert set_benchmark_cache(None) is None

    assert benchmark_cache() == (tmp_path / "from-env").resolve()


def test_the_default_is_a_per_user_cache_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    """With nothing configured, benchmarks land somewhere conventional.

    Not the working directory: a sweep run from a repository checkout must not
    scatter downloaded circuits through it.

    Args:
        monkeypatch: Used to clear the environment variable.
    """
    monkeypatch.delenv(CACHE_ENV_VAR, raising=False)

    default = benchmark_cache()

    assert default.parts[-2:] == ("aigverse", "benchmarks")
    assert default.is_absolute()
    assert default != Path.cwd()


@pytest.mark.skipif(sys.platform == "win32", reason="XDG_CACHE_HOME is a POSIX convention")
def test_xdg_cache_home_is_honoured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """On Linux the XDG base directory specification decides where the cache goes.

    Args:
        tmp_path: Directory used as XDG_CACHE_HOME.
        monkeypatch: Used to set the environment.
    """
    monkeypatch.delenv(CACHE_ENV_VAR, raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))

    if sys.platform == "darwin":
        pytest.skip("macOS uses ~/Library/Caches rather than XDG")

    assert benchmark_cache() == tmp_path / "aigverse" / "benchmarks"
