"""The ranges ABC accepts for the numeric options this bridge exposes.

Every wrapper validates its options against this table before ABC is started, so
an out-of-range value is a :exc:`ValueError` naming the Python argument rather
than an :exc:`~aigverse.abc.AbcExecutionError` carrying an ABC message.

ABC is the authority on these ranges and `aigverse` pins no ABC version, so the
table can only ever describe some ABC. Two things keep it honest:

- Most ranges are printed by ABC itself in a command's ``-h`` output, e.g.
  ``-K <num> : the max cut size (4 <= num <= 16)``. Those carry
  :attr:`Bound.documented`, and ``test_option_bounds.py`` parses them back out of
  the resolved binary and fails if they moved. The pinned-ABC CI job therefore
  catches upstream drift.
- A few are enforced by ABC's code without appearing in ``-h`` -- ``refactor``
  rejects a support above 15 at runtime while documenting no range at all. Those
  are marked undocumented, cite what ABC reports, and cannot be machine-checked.

A user running an ABC whose ranges differ still gets a clear failure: the command
reaches ABC and its complaint comes back as an ``AbcExecutionError``.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ["BOUNDS", "Bound", "check_option"]


@dataclass(frozen=True)
class Bound:
    """The range ABC accepts for one numeric switch of one command."""

    #: The ABC command, as typed, e.g. ``"resub"`` or ``"&deepsyn"``.
    command: str
    #: The switch letter, without the dash, e.g. ``"K"``.
    switch: str
    #: Smallest accepted value.
    low: int
    #: Largest accepted value, or ``None`` where ABC imposes no upper limit.
    high: int | None = None
    #: Whether ABC prints this range in the command's ``-h`` output. Only the
    #: documented ones can be checked against a real binary.
    documented: bool = True
    #: Why an undocumented bound is believed to hold.
    evidence: str = ""


def _table(*bounds: Bound) -> Mapping[tuple[str, str], Bound]:
    return MappingProxyType({(bound.command, bound.switch): bound for bound in bounds})


BOUNDS: Final[Mapping[tuple[str, str], Bound]] = _table(
    # -- classic space ----------------------------------------------------
    Bound(
        "refactor",
        "N",
        low=1,
        high=15,
        documented=False,
        evidence="ABC prints no range but rejects larger values at runtime with "
        "'Error: The cone size cannot exceed 15.'",
    ),
    Bound("refactor", "M", low=0),
    Bound("resub", "K", low=4, high=16),
    Bound("resub", "N", low=0, high=3),
    Bound("resub", "M", low=0),
    Bound(
        "resub",
        "F",
        low=0,
        documented=False,
        evidence="ABC prints only a default of 0 for the ODC fanout levels.",
    ),
    Bound("orchestrate", "K", low=4, high=16),
    Bound("orchestrate", "N", low=0, high=3),
    Bound(
        "orchestrate",
        "F",
        low=0,
        documented=False,
        evidence="ABC prints only a default of 0 for the ODC fanout levels.",
    ),
    # -- & space ----------------------------------------------------------
    Bound(
        "&b",
        "N",
        low=0,
        documented=False,
        evidence="ABC prints only a default of 1000000000 for the fanout limit.",
    ),
    Bound("&resub", "N", low=0),
    Bound("&resub", "S", low=1),
    Bound("&resub", "D", low=1),
    Bound("&syn2", "R", low=0),
    Bound(
        "&fraig",
        "C",
        low=0,
        documented=False,
        evidence="ABC prints only a default of 1000000 for the conflict limit.",
    ),
    Bound(
        "&deepsyn",
        "I",
        low=1,
        documented=False,
        evidence="ABC prints only a default of 1 for the iteration count.",
    ),
    Bound(
        "&deepsyn",
        "T",
        low=0,
        documented=False,
        evidence="ABC documents 0 as 'no timeout', which implies a floor of 0.",
    ),
    Bound(
        "&deepsyn",
        "A",
        low=0,
        documented=False,
        evidence="ABC documents 0 as 'no limit', which implies a floor of 0.",
    ),
    Bound(
        "&deepsyn",
        "J",
        low=1,
        documented=False,
        evidence="ABC prints only a default of 1000000000 for the number of steps "
        "without improvement; a patience of zero would stop before starting.",
    ),
    Bound("&deepsyn", "S", low=0, high=100),
    Bound(
        "&transduction",
        "S",
        low=0,
        high=4,
        documented=False,
        evidence="ABC enumerates the five fanin sort types individually rather than printing a range.",
    ),
    Bound(
        "&transduction",
        "P",
        low=0,
        documented=False,
        evidence="ABC prints only a default of 0 for the script parameters.",
    ),
    Bound(
        "&transduction",
        "R",
        low=0,
        documented=False,
        evidence="ABC documents 0 as 'no random', which implies a floor of 0.",
    ),
    Bound(
        "&transduction",
        "T",
        low=0,
        high=8,
        documented=False,
        evidence="ABC enumerates the nine transduction types individually rather than printing a range.",
    ),
    Bound(
        "&transduction",
        "I",
        low=0,
        documented=False,
        evidence="ABC documents 0 as 'no shuffle', which implies a floor of 0.",
    ),
    Bound(
        "&transtoch",
        "N",
        low=0,
        documented=False,
        evidence="ABC prints only a default for the restart count.",
    ),
    Bound(
        "&transtoch",
        "M",
        low=0,
        documented=False,
        evidence="ABC prints only a default of 10 for the hop count.",
    ),
    Bound(
        "&transtoch",
        "R",
        low=0,
        documented=False,
        evidence="ABC prints only a default for the random seed.",
    ),
    Bound(
        "&transtoch",
        "P",
        low=1,
        documented=False,
        evidence="ABC prints only a default of 1 for the thread count; fewer than one worker is meaningless.",
    ),
    Bound(
        "&cec",
        "C",
        low=0,
        documented=False,
        evidence="ABC prints only a default of 1000 for the conflict limit.",
    ),
    Bound(
        "&cec",
        "T",
        low=0,
        documented=False,
        evidence="ABC documents 0 as 'no limit', which implies a floor of 0.",
    ),
)


def check_option(command: str, switch: str, value: int, *, name: str) -> None:
    """Validates one option value against what ABC accepts.

    Args:
        command: The ABC command the switch belongs to, e.g. ``"resub"``.
        switch: The switch letter, without the dash, e.g. ``"K"``.
        value: The value to check.
        name: The Python argument name, used in the message so the error names
            what the caller wrote rather than an ABC switch.

    Raises:
        KeyError: If no bound is registered for the command and switch, which is
            a bug in this module rather than a caller error.
        ValueError: If ``value`` is outside the range ABC accepts.
    """
    bound = BOUNDS[command, switch]

    if bound.high is None:
        if value < bound.low:
            msg = f"{name} must be at least {bound.low}, got {value}"
            raise ValueError(msg)
        return

    if not bound.low <= value <= bound.high:
        msg = f"{name} must be between {bound.low} and {bound.high}, got {value}"
        raise ValueError(msg)
