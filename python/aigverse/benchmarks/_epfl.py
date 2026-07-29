"""The EPFL combinational benchmark suite.

The suite lives at https://github.com/lsils/benchmarks and is the standard
yardstick for logic synthesis. These helpers fetch its AIGER files on demand,
cache them, and hand back networks, so a script can name a benchmark instead of
carrying a downloader and a checked-in copy of the data.

Nothing is downloaded at import time, and nothing is bundled with `aigverse`.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from typing import TYPE_CHECKING

from ._cache import benchmark_cache

if TYPE_CHECKING:
    import os
    from pathlib import Path

    from ..networks import NamedAig

__all__ = [
    "EPFL_ARITHMETIC",
    "EPFL_BENCHMARKS",
    "EPFL_RANDOM_CONTROL",
    "epfl",
    "epfl_names",
    "epfl_path",
]

_URL = "https://raw.githubusercontent.com/lsils/benchmarks/{revision}/{category}/{name}.aig"

# The suite is versioned by commit rather than by release. Pinning the default
# keeps a benchmark meaning the same thing tomorrow as it does today; pass
# `revision=` to follow the branch instead.
DEFAULT_REVISION = "master"

#: The ten arithmetic benchmarks.
EPFL_ARITHMETIC: frozenset[str] = frozenset({
    "adder",
    "bar",
    "div",
    "hyp",
    "log2",
    "max",
    "multiplier",
    "sin",
    "sqrt",
    "square",
})

#: The ten random/control benchmarks.
EPFL_RANDOM_CONTROL: frozenset[str] = frozenset({
    "arbiter",
    "cavlc",
    "ctrl",
    "dec",
    "i2c",
    "int2float",
    "mem_ctrl",
    "priority",
    "router",
    "voter",
})

#: Every benchmark in the suite.
EPFL_BENCHMARKS: frozenset[str] = EPFL_ARITHMETIC | EPFL_RANDOM_CONTROL

_CATEGORIES: dict[str, frozenset[str]] = {
    "arithmetic": EPFL_ARITHMETIC,
    "random_control": EPFL_RANDOM_CONTROL,
}


def epfl_names(category: str | None = None) -> tuple[str, ...]:
    """Lists the available benchmark names.

    Args:
        category: ``"arithmetic"`` or ``"random_control"``, or ``None`` for all.

    Returns:
        The names, sorted.

    Raises:
        ValueError: If ``category`` is not a known category.
    """
    if category is None:
        return tuple(sorted(EPFL_BENCHMARKS))
    try:
        return tuple(sorted(_CATEGORIES[category]))
    except KeyError:
        known = ", ".join(sorted(_CATEGORIES))
        msg = f"unknown category {category!r}; available categories: {known}"
        raise ValueError(msg) from None


def _category_of(name: str) -> str:
    """Finds the category a benchmark belongs to.

    Args:
        name: The benchmark name.

    Returns:
        The category directory it lives in.

    Raises:
        ValueError: If ``name`` is not part of the suite.
    """
    for category, members in _CATEGORIES.items():
        if name in members:
            return category

    known = ", ".join(sorted(EPFL_BENCHMARKS))
    msg = f"unknown EPFL benchmark {name!r}; available benchmarks: {known}"
    raise ValueError(msg)


def epfl_path(
    name: str,
    *,
    revision: str = DEFAULT_REVISION,
    cache_dir: str | os.PathLike[str] | None = None,
    timeout: float = 60.0,
) -> Path:
    """Downloads an EPFL benchmark and returns the local file.

    The download is cached, so repeated calls cost nothing after the first. Use
    this when the AIGER file itself is wanted; :func:`epfl` parses it for you.

    Args:
        name: The benchmark name, e.g. ``"adder"``. See :func:`epfl_names`.
        revision: Git revision of the benchmark repository to fetch from.
        cache_dir: Directory to cache into, overriding the configured one.
        timeout: Seconds to wait for the download.

    Returns:
        Path to the local AIGER file.

    Raises:
        ValueError: If ``name`` is not part of the suite.
        OSError: If the benchmark could not be downloaded.
    """
    category = _category_of(name)

    from pathlib import Path as _Path

    root = _Path(cache_dir).expanduser() if cache_dir is not None else benchmark_cache()
    directory = root / revision / category
    target = directory / f"{name}.aig"
    if target.is_file() and target.stat().st_size > 0:
        return target

    url = _URL.format(revision=revision, category=category, name=name)
    directory.mkdir(parents=True, exist_ok=True)

    # Download to a sibling first: an interrupted transfer must not leave a
    # truncated file behind that later calls would happily treat as cached.
    partial = target.with_suffix(".aig.part")
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # ruff: ignore[suspicious-url-open-usage]
            partial.write_bytes(response.read())
    except (urllib.error.URLError, TimeoutError) as exc:
        partial.unlink(missing_ok=True)
        msg = f"could not download the EPFL benchmark {name!r} from {url}: {exc}"
        raise OSError(msg) from exc

    partial.replace(target)
    return target


def epfl(
    name: str,
    *,
    revision: str = DEFAULT_REVISION,
    cache_dir: str | os.PathLike[str] | None = None,
    timeout: float = 60.0,
) -> NamedAig:
    """Loads an EPFL benchmark as a network.

    The result is a :class:`~aigverse.networks.NamedAig`, which is an
    :class:`~aigverse.networks.Aig` carrying the input and output names from the
    AIGER symbol table. It is accepted anywhere an ``Aig`` is, so the names come
    along at no cost to the caller.

    Args:
        name: The benchmark name, e.g. ``"adder"``. See :func:`epfl_names`.
        revision: Git revision of the benchmark repository to fetch from.
        cache_dir: Directory to cache into, overriding the configured one.
        timeout: Seconds to wait for the download.

    Returns:
        The benchmark network, with its I/O names.

    Raises:
        ValueError: If ``name`` is not part of the suite.
        OSError: If the benchmark could not be downloaded.
        RuntimeError: If the downloaded file could not be parsed.
    """
    from ..io import read_aiger_into_aig

    path = epfl_path(name, revision=revision, cache_dir=cache_dir, timeout=timeout)
    return read_aiger_into_aig(path)
