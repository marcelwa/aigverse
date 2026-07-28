"""Tests for locating and configuring the ABC executable."""

from __future__ import annotations

import stat
from typing import TYPE_CHECKING

import pytest

from aigverse.abc import (
    ABC_ENV_VAR,
    AbcNotFoundError,
    abc_binary,
    find_abc_binary,
    is_available,
    set_abc_binary,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def stub(tmp_path: Path) -> Path:
    """Creates an executable stub file standing in for ABC."""
    path = tmp_path / "abc"
    path.write_text("#!/bin/sh\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def test_is_available_never_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ABC_ENV_VAR, raising=False)
    monkeypatch.setenv("PATH", "")
    assert is_available() is False


def test_env_var_is_used(monkeypatch: pytest.MonkeyPatch, stub: Path) -> None:
    monkeypatch.setenv(ABC_ENV_VAR, str(stub))
    assert find_abc_binary() == stub.resolve()
    assert is_available() is True


def test_explicit_override_beats_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, stub: Path) -> None:
    other = tmp_path / "other-abc"
    other.write_text("#!/bin/sh\n")
    other.chmod(other.stat().st_mode | stat.S_IEXEC)

    monkeypatch.setenv(ABC_ENV_VAR, str(stub))
    set_abc_binary(other)
    assert find_abc_binary() == other.resolve()


def test_override_can_be_cleared(monkeypatch: pytest.MonkeyPatch, stub: Path) -> None:
    monkeypatch.setenv(ABC_ENV_VAR, str(stub))
    set_abc_binary(stub)
    assert set_abc_binary(None) is None
    assert find_abc_binary() == stub.resolve()


def test_override_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(AbcNotFoundError, match="not an existing file"):
        set_abc_binary(tmp_path / "nope")


def test_override_rejects_non_executable(tmp_path: Path) -> None:
    path = tmp_path / "not-exec"
    path.write_text("")
    with pytest.raises(AbcNotFoundError, match="not executable"):
        set_abc_binary(path)


def test_env_var_pointing_nowhere_is_not_found(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A bogus environment variable must not silently fall through to PATH."""
    monkeypatch.setenv(ABC_ENV_VAR, str(tmp_path / "nope"))
    assert find_abc_binary() is None


def test_error_message_is_actionable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ABC_ENV_VAR, raising=False)
    monkeypatch.setenv("PATH", "")
    with pytest.raises(AbcNotFoundError, match=ABC_ENV_VAR):
        abc_binary()


def test_path_lookup_finds_berkeley_abc(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Debian and Ubuntu install ABC as `berkeley-abc`."""
    path = tmp_path / "berkeley-abc"
    path.write_text("#!/bin/sh\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)

    monkeypatch.delenv(ABC_ENV_VAR, raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    assert find_abc_binary() == path.resolve()
