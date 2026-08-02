"""The EPFL combinational benchmark suite.

The suite lives at https://github.com/lsils/benchmarks and is the standard
yardstick for logic synthesis. These helpers fetch its AIGER files on demand,
cache them, and hand back networks, so a script can name a benchmark instead of
carrying a downloader and a checked-in copy of the data.

The 20 arithmetic and random/control circuits are supported. The suite's three
MtM benchmarks are not: they live on Zenodo rather than in the git repository.

Nothing is downloaded at import time, and nothing is bundled with `aigverse`.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.parse
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

# The suite is versioned by commit rather than by release, and its circuits do
# change. The default is therefore a pinned commit rather than `master`: two
# people running the same code must get the same circuits, and a moving default
# would not even be self-consistent, since whoever already has a warm cache would
# keep the old file forever while a newcomer downloads the new one.
#
# Kept current by the `lsils/benchmarks` custom manager in renovate.json5.
DEFAULT_REVISION = "0060e156826e733d69bf5b3322d1bdd0d03a1f9a"

# A revision becomes a path component of the cache, so it has to be one: an
# absolute value would discard the cache root entirely and `..` would climb out
# of it. Git refs may contain slashes, so those are allowed and simply nest.
_SAFE_REVISION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")

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

#: Every benchmark this loader supports.
#:
#: The suite as published has 23 circuits. The three MtM ("more than ten
#: million gates") benchmarks are not among these: they are distributed via
#: Zenodo rather than the git repository, and at several gigabytes apiece they
#: want a different delivery story than an on-demand download.
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


def _check_revision(revision: str) -> str:
    """Rejects a revision that would not be safe as a cache path component.

    Args:
        revision: The revision to check.

    Returns:
        The revision, unchanged.

    Raises:
        ValueError: If the revision is empty, absolute, contains a ``..``
            component, or holds characters a git ref cannot.
    """
    if not _SAFE_REVISION.match(revision) or ".." in revision.split("/"):
        msg = (
            f"invalid revision {revision!r}: expected a git commit, tag or branch, "
            f"which must not be absolute or contain a '..' component"
        )
        raise ValueError(msg)
    return revision


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
            Defaults to a pinned commit, so results are reproducible; pass
            ``"master"`` to follow the branch instead.
        cache_dir: Directory to cache into, overriding the configured one.
        timeout: Seconds to wait for the download.

    Returns:
        Path to the local AIGER file.

    Raises:
        ValueError: If ``name`` is not part of the suite, or ``revision`` is not
            usable as a path component.
        OSError: If the benchmark could not be downloaded.
    """
    category = _category_of(name)
    _check_revision(revision)

    from pathlib import Path as _Path

    root = _Path(cache_dir).expanduser() if cache_dir is not None else benchmark_cache()
    directory = root / revision / category
    target = directory / f"{name}.aig"
    if target.is_file() and target.stat().st_size > 0:
        return target

    # quote() keeps the slashes a ref may legitimately contain, and escapes
    # anything else that would change the meaning of the URL
    url = _URL.format(revision=urllib.parse.quote(revision, safe="/"), category=category, name=name)
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
            Defaults to a pinned commit, so results are reproducible; pass
            ``"master"`` to follow the branch instead.
        cache_dir: Directory to cache into, overriding the configured one.
        timeout: Seconds to wait for the download.

    Returns:
        The benchmark network, with its I/O names.

    Raises:
        ValueError: If ``name`` is not part of the suite, or ``revision`` is not
            usable as a path component.
        OSError: If the benchmark could not be downloaded.
        RuntimeError: If the downloaded file could not be parsed.
    """
    from ..io import read_aiger_into_aig

    path = epfl_path(name, revision=revision, cache_dir=cache_dir, timeout=timeout)
    return read_aiger_into_aig(path)
