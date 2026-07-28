"""Discovery and configuration of the external ABC executable."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from ._errors import AbcNotFoundError, AbcTimeoutError

__all__ = [
    "ABC_ENV_VAR",
    "ABC_RC_ENV_VAR",
    "abc_binary",
    "abc_rc",
    "abc_version",
    "find_abc_binary",
    "is_available",
    "set_abc_binary",
    "set_abc_rc",
]

# Name of the environment variable pointing at the ABC executable.
ABC_ENV_VAR = "AIGVERSE_ABC"

# Name of the environment variable pointing at an ABC resource file.
ABC_RC_ENV_VAR = "AIGVERSE_ABC_RC"

# Executable names searched on PATH, in order. Debian and Ubuntu install ABC as
# `berkeley-abc` to avoid a name clash.
_CANDIDATE_NAMES = ("abc", "berkeley-abc")

_HINT = (
    f"aigverse does not ship ABC. Install it (e.g. from "
    f"https://github.com/berkeley-abc/abc, a distribution package, conda-forge, or "
    f"oss-cad-suite) and either put it on PATH as 'abc' or point aigverse at it via "
    f"the {ABC_ENV_VAR} environment variable or aigverse.abc.set_abc_binary()."
)

_override: Path | None = None
_rc_override: Path | None = None


def _validate(path: Path, *, source: str) -> Path:
    """Checks that a candidate path is an executable file.

    Args:
        path: The candidate path.
        source: Human-readable description of where the path came from.

    Returns:
        The resolved absolute path.

    Raises:
        AbcNotFoundError: If the path does not exist or is not executable.
    """
    resolved = path.expanduser()
    if not resolved.is_file():
        msg = f"{source} points to '{path}', which is not an existing file.\n{_HINT}"
        raise AbcNotFoundError(msg)
    if not os.access(resolved, os.X_OK):
        msg = f"{source} points to '{path}', which is not executable.\n{_HINT}"
        raise AbcNotFoundError(msg)
    return resolved.resolve()


def set_abc_binary(path: str | os.PathLike[str] | None) -> Path | None:
    """Sets or clears an explicit path to the ABC executable.

    The explicit override takes precedence over the ``AIGVERSE_ABC`` environment
    variable and over a ``PATH`` lookup. It applies process-wide and is intended
    to be called once during setup; it is not thread-safe.

    Args:
        path: Path to the ABC executable, or ``None`` to clear a previously set
            override and fall back to environment and ``PATH`` discovery.

    Returns:
        The resolved absolute path, or ``None`` if the override was cleared.

    Raises:
        AbcNotFoundError: If ``path`` does not exist or is not executable.
    """
    global _override  # ruff: ignore[global-statement]

    if path is None:
        _override = None
        return None

    _override = _validate(Path(path), source="set_abc_binary()")
    return _override


def find_abc_binary() -> Path | None:
    """Resolves the ABC executable without raising.

    Resolution order: an explicit override set via :func:`set_abc_binary`, then
    the ``AIGVERSE_ABC`` environment variable, then a ``PATH`` lookup for ``abc``
    and ``berkeley-abc``.

    Returns:
        The resolved absolute path, or ``None`` if no candidate was found.
    """
    # Revalidate: an override configured earlier may since have been deleted or
    # lost its executable bit, and reporting it as available would surface an
    # OSError from subprocess instead of the documented AbcNotFoundError.
    if _override is not None:
        if _override.is_file() and os.access(_override, os.X_OK):
            return _override
        return None

    env_value = os.environ.get(ABC_ENV_VAR)
    if env_value:
        candidate = Path(env_value).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
        return None

    for name in _CANDIDATE_NAMES:
        found = shutil.which(name)
        if found:
            return Path(found).resolve()

    return None


def abc_binary() -> Path:
    """Resolves the ABC executable.

    Returns:
        The resolved absolute path to the ABC executable.

    Raises:
        AbcNotFoundError: If no ABC executable could be located.
    """
    resolved = find_abc_binary()
    if resolved is not None:
        return resolved

    env_value = os.environ.get(ABC_ENV_VAR)
    if env_value:
        msg = f"{ABC_ENV_VAR} is set to '{env_value}', but that is not an executable file.\n{_HINT}"
    else:
        names = " or ".join(repr(name) for name in _CANDIDATE_NAMES)
        msg = f"No ABC executable found: neither {names} is on PATH.\n{_HINT}"
    raise AbcNotFoundError(msg)


def is_available() -> bool:
    """Reports whether an ABC executable can be located.

    This never raises and never starts a process, so it is safe to call in a
    module guard or a test skip condition.

    Returns:
        ``True`` if an ABC executable was found, ``False`` otherwise.
    """
    return find_abc_binary() is not None


def abc_version(*, timeout: float | None = 10.0) -> str:
    """Queries the version banner of the resolved ABC executable.

    Useful to confirm that whatever was discovered really is Berkeley ABC, since
    discovery itself deliberately does not start a process.

    Args:
        timeout: Seconds to wait for ABC to respond, or ``None`` to wait forever.

    Returns:
        The trimmed output of ABC's ``version`` command.

    Raises:
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
    """
    binary = abc_binary()
    # ABC drops an `abc.history` file into its working directory on every run,
    # so keep it out of whatever directory the caller happens to be in.
    try:
        with tempfile.TemporaryDirectory(prefix="aigverse-abc-") as scratch:
            completed = subprocess.run(
                [str(binary), "-s", "-q", "version"],
                cwd=scratch,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=timeout,
            )
    except subprocess.TimeoutExpired as exc:
        msg = f"ABC did not report its version within {timeout} seconds"
        raise AbcTimeoutError(msg, binary=str(binary), command="version", output="") from exc

    return completed.stdout.strip()


def set_abc_rc(path: str | os.PathLike[str] | None) -> Path | None:
    """Sets or clears an ABC resource file to load before every command.

    The bridge normally runs ABC with ``-s`` so that no ``abc.rc`` is read and
    results do not depend on the local installation. Registering a resource file
    here keeps that isolation -- the file given is the only one loaded -- while
    making its aliases available to :func:`~aigverse.abc.run_script` and
    :func:`~aigverse.abc.run_commands`.

    It applies process-wide and is intended to be called once during setup; it is
    not thread-safe.

    Args:
        path: Path to an ABC resource file, or ``None`` to clear a previously set
            one and go back to running without any.

    Returns:
        The resolved absolute path, or ``None`` if the resource file was cleared.

    Raises:
        AbcNotFoundError: If ``path`` does not exist or is not a file.
    """
    global _rc_override  # ruff: ignore[global-statement]

    if path is None:
        _rc_override = None
        return None

    resolved = Path(path).expanduser()
    if not resolved.is_file():
        msg = f"set_abc_rc() points to '{path}', which is not an existing file."
        raise AbcNotFoundError(msg)

    _rc_override = resolved.resolve()
    return _rc_override


def abc_rc() -> Path | None:
    """Resolves the ABC resource file loaded before every command.

    Resolution order: an explicit path set via :func:`set_abc_rc`, then the
    ``AIGVERSE_ABC_RC`` environment variable.

    Returns:
        The resolved absolute path, or ``None`` if no resource file is configured.
    """
    if _rc_override is not None:
        return _rc_override if _rc_override.is_file() else None

    env_value = os.environ.get(ABC_RC_ENV_VAR)
    if env_value:
        candidate = Path(env_value).expanduser()
        if candidate.is_file():
            return candidate.resolve()

    return None
