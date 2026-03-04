"""aigverse: A Python Library for Logic Networks, Synthesis, and Optimization."""

from __future__ import annotations

import os
import sys
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

from ._version import version as __version__

if sys.platform == "win32":

    def _dll_patch() -> None:
        package_dir = Path(__file__).resolve().parent
        candidate_dirs = [package_dir / "bin", package_dir]

        for dll_dir in candidate_dirs:
            if dll_dir.is_dir():
                os.add_dll_directory(str(dll_dir))

    _dll_patch()
    del _dll_patch

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
