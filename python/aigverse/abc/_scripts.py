"""Canonical ABC optimization scripts, expanded to builtin commands.

`resyn2`, `compress2rs` and friends are *aliases* defined in ABC's ``abc.rc``
resource file, not builtin commands. A build that cannot find an ``abc.rc``
rejects them with ``unknown command``, and a user with a customized ``abc.rc``
would silently get something else.

The bridge therefore ships the expansions itself and runs ABC with ``-s`` so no
resource file is read at all. The expansions below are transcribed from the
``abc.rc`` distributed with Berkeley ABC and resolved through both alias levels
(``b`` -> ``balance``, ``rw`` -> ``rewrite``, ``rwz`` -> ``rewrite -z``,
``rf`` -> ``refactor``, ``rfz`` -> ``refactor -z``, ``rs`` -> ``resub``,
``rsz`` -> ``resub -z``), so every command below is a builtin.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ["SCRIPTS", "expand_script"]

# Mapping from script name to its expansion into builtin ABC commands.
SCRIPTS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    # alias resyn "b; rw; rwz; b; rwz; b"
    "resyn": (
        "balance",
        "rewrite",
        "rewrite -z",
        "balance",
        "rewrite -z",
        "balance",
    ),
    # alias resyn2 "b; rw; rf; b; rw; rwz; b; rfz; rwz; b"
    "resyn2": (
        "balance",
        "rewrite",
        "refactor",
        "balance",
        "rewrite",
        "rewrite -z",
        "balance",
        "refactor -z",
        "rewrite -z",
        "balance",
    ),
    # alias resyn3 "b; rs; rs -K 6; b; rsz; rsz -K 6; b; rsz -K 5; b"
    "resyn3": (
        "balance",
        "resub",
        "resub -K 6",
        "balance",
        "resub -z",
        "resub -z -K 6",
        "balance",
        "resub -z -K 5",
        "balance",
    ),
    # alias compress "b -l; rw -l; rwz -l; b -l; rwz -l; b -l"
    "compress": (
        "balance -l",
        "rewrite -l",
        "rewrite -z -l",
        "balance -l",
        "rewrite -z -l",
        "balance -l",
    ),
    # alias compress2 "b -l; rw -l; rf -l; b -l; rw -l; rwz -l; b -l; rfz -l; rwz -l; b -l"
    "compress2": (
        "balance -l",
        "rewrite -l",
        "refactor -l",
        "balance -l",
        "rewrite -l",
        "rewrite -z -l",
        "balance -l",
        "refactor -z -l",
        "rewrite -z -l",
        "balance -l",
    ),
    # alias resyn2rs "b; rs -K 6; rw; rs -K 6 -N 2; rf; rs -K 8; b; rs -K 8 -N 2;
    #                 rw; rs -K 10; rwz; rs -K 10 -N 2; b; rs -K 12; rfz;
    #                 rs -K 12 -N 2; rwz; b"
    "resyn2rs": (
        "balance",
        "resub -K 6",
        "rewrite",
        "resub -K 6 -N 2",
        "refactor",
        "resub -K 8",
        "balance",
        "resub -K 8 -N 2",
        "rewrite",
        "resub -K 10",
        "rewrite -z",
        "resub -K 10 -N 2",
        "balance",
        "resub -K 12",
        "refactor -z",
        "resub -K 12 -N 2",
        "rewrite -z",
        "balance",
    ),
    # alias compress2rs -- as resyn2rs, with -l on every command
    "compress2rs": (
        "balance -l",
        "resub -K 6 -l",
        "rewrite -l",
        "resub -K 6 -N 2 -l",
        "refactor -l",
        "resub -K 8 -l",
        "balance -l",
        "resub -K 8 -N 2 -l",
        "rewrite -l",
        "resub -K 10 -l",
        "rewrite -z -l",
        "resub -K 10 -N 2 -l",
        "balance -l",
        "resub -K 12 -l",
        "refactor -z -l",
        "resub -K 12 -N 2 -l",
        "rewrite -z -l",
        "balance -l",
    ),
    # dc2 is a builtin; listed for uniformity with the other named scripts
    "dc2": ("dc2",),
})


def expand_script(name: str) -> tuple[str, ...]:
    """Expands a canonical ABC script name into builtin commands.

    Args:
        name: The script name, e.g. ``"resyn2"``. See :data:`SCRIPTS` for the
            available names.

    Returns:
        The commands the script consists of, all of them ABC builtins.

    Raises:
        KeyError: If ``name`` is not a known script.
    """
    try:
        return SCRIPTS[name]
    except KeyError:
        known = ", ".join(sorted(SCRIPTS))
        msg = f"unknown ABC script {name!r}; available scripts: {known}"
        raise KeyError(msg) from None
