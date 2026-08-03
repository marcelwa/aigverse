"""Where downloaded benchmark files are kept."""

from __future__ import annotations

import os
import sys
from pathlib import Path

__all__ = ["CACHE_ENV_VAR", "benchmark_cache", "set_benchmark_cache"]

# Name of the environment variable overriding the cache location.
CACHE_ENV_VAR = "AIGVERSE_BENCHMARK_CACHE"

_override: Path | None = None


def _default_cache() -> Path:
    """Pick the per-user cache directory for the current platform.

    Follows the XDG base directory specification on Linux and the conventional
    locations elsewhere, rather than taking a dependency on ``platformdirs`` for
    one directory.

    Returns:
        The default cache directory. It is not created here.
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Local"
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Caches"
    else:
        base = os.environ.get("XDG_CACHE_HOME")
        root = Path(base) if base else Path.home() / ".cache"

    return root / "aigverse" / "benchmarks"


def set_benchmark_cache(path: str | os.PathLike[str] | None) -> Path | None:
    """Sets or clears the directory downloaded benchmarks are cached in.

    Applies process-wide and is intended to be called once during setup; it is
    not thread-safe.

    Args:
        path: The directory to use, or ``None`` to clear a previous override and
            fall back to the environment variable and the platform default.

    Returns:
        The resolved directory, or ``None`` if the override was cleared.
    """
    global _override  # ruff: ignore[global-statement]

    if path is None:
        _override = None
        return None

    _override = Path(path).expanduser().resolve()
    return _override


def benchmark_cache() -> Path:
    """Resolves the directory downloaded benchmarks are cached in.

    Resolution order: an explicit override set via :func:`set_benchmark_cache`,
    then the ``AIGVERSE_BENCHMARK_CACHE`` environment variable, then a per-user
    cache directory appropriate to the platform.

    Returns:
        The cache directory. It is not created here.
    """
    if _override is not None:
        return _override

    configured = os.environ.get(CACHE_ENV_VAR)
    if configured:
        return Path(configured).expanduser().resolve()

    return _default_cache()
