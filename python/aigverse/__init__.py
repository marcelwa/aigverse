"""aigverse: A Python Library for Logic Networks, Synthesis, and Optimization."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from ._version import version as __version__

if TYPE_CHECKING:
    from . import algorithms, io, networks, utils

_LAZY_SUBMODULES = {
    "algorithms",
    "io",
    "networks",
    "utils",
}

__all__ = [
    "__version__",
    "algorithms",
    "io",
    "networks",
    "utils",
]


def __getattr__(name: str) -> object:
    if name in _LAZY_SUBMODULES:
        module = import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


def __dir__() -> list[str]:
    return sorted(set(globals()) | _LAZY_SUBMODULES)
