"""Checks the shipped script expansions against ABC's own ``abc.rc``.

`resyn2` and friends are aliases defined in ABC's resource file, not builtin
commands, and the bridge ships its own expansions so results do not depend on a
local ``abc.rc``. That trades one problem for another: the expansions could
silently drift from what upstream ABC actually defines.

This test closes that gap. It parses the ``abc.rc`` belonging to the ABC the rest
of the suite runs against and asserts that every shipped expansion still matches,
so a drift shows up when the pinned ABC revision is bumped rather than in a user's
results.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from aigverse.abc import SCRIPTS, find_abc_binary

_ALIAS = re.compile(r'^alias\s+(\S+)\s+"?(.*?)"?\s*$')


def _locate_abc_rc() -> Path | None:
    """Finds the ``abc.rc`` belonging to the ABC binary under test.

    Returns:
        Path to the resource file, or ``None`` if it could not be located.
    """
    configured = os.environ.get("AIGVERSE_ABC_RC")
    if configured and Path(configured).is_file():
        return Path(configured)

    binary = find_abc_binary()
    if binary is None:
        return None

    # ABC's abc.rc sits next to the binary in a source build
    candidate = binary.parent / "abc.rc"
    return candidate if candidate.is_file() else None


def _parse_aliases(rc: Path) -> dict[str, str]:
    """Reads every ``alias`` definition from an ABC resource file.

    Args:
        rc: Path to the resource file.

    Returns:
        Mapping from alias name to its unexpanded body.
    """
    aliases: dict[str, str] = {}
    for raw in rc.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line.startswith("alias "):
            continue
        match = _ALIAS.match(line)
        if match:
            aliases[match.group(1)] = match.group(2)
    return aliases


def _expand(body: str, aliases: dict[str, str], depth: int = 0) -> tuple[str, ...]:
    """Expands an alias body into builtin commands.

    Args:
        body: The alias body, a ``;``-separated command list.
        aliases: All alias definitions from the resource file.
        depth: Current recursion depth, guarding against cyclic aliases.

    Returns:
        The commands with every alias resolved.

    Raises:
        RecursionError: If the aliases reference each other cyclically.
    """
    if depth > 10:
        msg = "alias expansion did not terminate"
        raise RecursionError(msg)

    commands: list[str] = []
    for part in body.split(";"):
        command = part.strip()
        if not command:
            continue
        head, _, rest = command.partition(" ")
        if head in aliases:
            expanded = _expand(aliases[head], aliases, depth + 1)
            # a trailing argument applies to the last command of the expansion
            if rest:
                expanded = (*expanded[:-1], f"{expanded[-1]} {rest.strip()}")
            commands.extend(expanded)
        else:
            commands.append(command)
    return tuple(commands)


@pytest.mark.parametrize("name", sorted(SCRIPTS))
def test_expansion_matches_abc_rc(name: str) -> None:
    """The shipped expansion still matches what ABC's ``abc.rc`` defines.

    Args:
        name: Name of the script under test.
    """
    rc = _locate_abc_rc()
    if rc is None:
        # This check is the only thing standing between an upstream alias change
        # and silently wrong results, so where ABC is mandatory it must not skip.
        if os.environ.get("AIGVERSE_REQUIRE_ABC"):
            pytest.fail("AIGVERSE_REQUIRE_ABC is set, but no abc.rc was found next to the binary")
        pytest.skip("no abc.rc found; set AIGVERSE_ABC_RC to enable this check")

    aliases = _parse_aliases(rc)
    if name not in aliases:
        # dc2 is a builtin, so it legitimately has no alias
        pytest.skip(f"{name!r} is not an alias in this abc.rc")

    assert _expand(aliases[name], aliases) == SCRIPTS[name]
