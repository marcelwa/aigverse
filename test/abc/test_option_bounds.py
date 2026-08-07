"""Keeps the option bounds in sync with whatever ABC is installed.

`aigverse` pins no ABC version, so :data:`aigverse.abc._options.BOUNDS` can only
describe some ABC. Most of its entries are ranges ABC prints in a command's
``-h`` output; these tests parse them back out of the resolved binary and fail if
they moved, which is what makes the pinned-ABC CI job able to catch upstream
drift. The rest are enforced by ABC's code without appearing in ``-h`` and are
checked by behavior instead.
"""

from __future__ import annotations

import re
import subprocess
from typing import TYPE_CHECKING

import pytest

from aigverse import abc
from aigverse.abc._options import BOUNDS, Bound, check_option

if TYPE_CHECKING:
    from aigverse.networks import Aig

# `-K <num> : the max cut size (4 <= num <= 16) [default = 8]`
_CLOSED = re.compile(r"-(?P<switch>[A-Za-z]) *<?num>? *:.*?\((?P<low>-?\d+) *<= *num *<= *(?P<high>-?\d+)\)")
# `-N num   : the limit on added nodes (num >= 0) [default = 0]`
_OPEN = re.compile(r"-(?P<switch>[A-Za-z]) *<?num>? *:.*?\(num *(?P<operator>>=|>) *(?P<low>-?\d+)\)")
# `-M <num> : the min number of nodes saved after one step (0 <= num) [default = 1]`
_OPEN_REVERSED = re.compile(r"-(?P<switch>[A-Za-z]) *<?num>? *:.*?\((?P<low>-?\d+) *(?P<operator><=|<) *num\)")


def _usage(command: str) -> str:
    """Returns ABC's ``-h`` output for a command.

    Args:
        command: The ABC command, as typed.

    Returns:
        Everything ABC printed for ``<command> -h``.
    """
    completed = subprocess.run(
        [str(abc.abc_binary()), "-s", "-q", f"{command} -h"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    return completed.stdout


def _documented_ranges(usage: str) -> dict[str, tuple[int, int | None]]:
    """Extracts the switch ranges ABC prints in a usage message.

    Args:
        usage: ABC's ``-h`` output for one command.

    Returns:
        Mapping from switch letter to its ``(low, high)`` range, where ``high``
        is ``None`` for an open-ended one.
    """
    ranges: dict[str, tuple[int, int | None]] = {}
    for match in _CLOSED.finditer(usage):
        ranges[match["switch"]] = (int(match["low"]), int(match["high"]))
    for match in _OPEN.finditer(usage):
        low = int(match["low"]) + (1 if match["operator"] == ">" else 0)
        ranges.setdefault(match["switch"], (low, None))
    for match in _OPEN_REVERSED.finditer(usage):
        low = int(match["low"]) + (1 if match["operator"] == "<" else 0)
        ranges.setdefault(match["switch"], (low, None))
    return ranges


_DOCUMENTED = [bound for bound in BOUNDS.values() if bound.documented]
_UNDOCUMENTED = [bound for bound in BOUNDS.values() if not bound.documented]


@pytest.mark.usefixtures("abc_available")
@pytest.mark.parametrize("bound", _DOCUMENTED, ids=lambda b: f"{b.command}-{b.switch}")
def test_documented_bounds_match_abc(bound: Bound) -> None:
    """Every range this bridge encodes must still be the range ABC prints."""
    ranges = _documented_ranges(_usage(bound.command))

    assert bound.switch in ranges, (
        f"ABC no longer documents a range for `{bound.command} -{bound.switch}`; "
        f"either it moved into the code or the switch is gone."
    )
    assert ranges[bound.switch] == (bound.low, bound.high)


@pytest.mark.usefixtures("abc_available")
@pytest.mark.parametrize(
    "command",
    sorted({bound.command for bound in BOUNDS.values()}),
)
def test_no_documented_range_is_left_unencoded(command: str) -> None:
    """ABC gaining a range for a switch we expose must not go unnoticed.

    The other direction of the same check: a switch this bridge passes through
    without validating, for which ABC has since started documenting a range,
    would silently keep leaking `AbcExecutionError` where a `ValueError` belongs.
    """
    exposed = {bound.switch for bound in BOUNDS.values() if bound.command == command}
    documented = set(_documented_ranges(_usage(command)))

    unencoded = {switch for switch in documented & exposed if not BOUNDS[command, switch].documented}
    assert not unencoded, (
        f"ABC now documents a range for `{command} -{', -'.join(sorted(unencoded))}`; "
        f"mark the bound documented in _options.py so it is checked from now on."
    )


@pytest.mark.parametrize("bound", _UNDOCUMENTED, ids=lambda b: f"{b.command}-{b.switch}")
def test_undocumented_bounds_state_their_evidence(bound: Bound) -> None:
    """A bound ABC does not print cannot be machine-checked, so it must say why."""
    assert bound.evidence, (
        f"`{bound.command} -{bound.switch}` is not documented by ABC, so it needs "
        f"an `evidence` note recording where the range came from."
    )


@pytest.mark.usefixtures("abc_available")
def test_refactor_rejects_the_support_abc_rejects(and_aig: Aig) -> None:
    """The one undocumented bound worth pinning against a real ABC.

    ABC prints no range for `refactor -N` but refuses a support above 15 at
    runtime. If that ever changes, the wrapper is needlessly strict rather than
    wrong, so this checks the boundary from both sides.
    """
    abc.refactor(and_aig, max_support=15)

    with pytest.raises(abc.AbcExecutionError, match="cone size"):
        abc.run_script(and_aig, "refactor -N 16")


@pytest.mark.parametrize(
    ("command", "switch", "value", "message"),
    [
        ("resub", "K", 3, "cut must be between 4 and 16"),
        ("resub", "K", 17, "cut must be between 4 and 16"),
        ("resub", "N", 4, "inserts must be between 0 and 3"),
        ("refactor", "N", 16, "support must be between 1 and 15"),
        ("&resub", "S", 0, "support must be at least 1"),
        ("&deepsyn", "S", 101, "seed must be between 0 and 100"),
    ],
)
def test_check_option_reports_the_python_argument(command: str, switch: str, value: int, message: str) -> None:
    """The message must name the keyword the caller wrote, not the ABC switch."""
    name = message.split(" must", maxsplit=1)[0]
    with pytest.raises(ValueError, match=re.escape(message)):
        check_option(command, switch, value, name=name)


def test_check_option_rejects_an_unregistered_switch() -> None:
    """A missing table entry is a bug here, and must not pass silently."""
    with pytest.raises(KeyError):
        check_option("resub", "Z", 1, name="whatever")
