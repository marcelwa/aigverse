"""Structured access to ABC's own network statistics.

ABC reports what it thinks of a network through ``print_stats`` (classic store)
and ``&ps`` (GIA store). Both print a single human-readable line; these helpers
run them and parse that line into an :class:`AbcStats`, so a script can compare
what ABC measured against what ``aigverse`` measures without scraping text.
"""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ._errors import AbcExecutionError
from ._runner import check_supported, resolve_binary, run_commands

if TYPE_CHECKING:
    import os

    from ..networks import Aig

__all__ = ["AbcStats", "gia_stats", "stats"]

_INPUT_FILE = "in.aig"

# ABC colours its statistics line, so the escape sequences come off first.
_ANSI = re.compile(r"\x1b\[[0-9;]*m")

_IO = re.compile(r"i/o\s*=\s*(\d+)\s*/\s*(\d+)")
_LATCHES = re.compile(r"lat\s*=\s*(\d+)")
_AND_GATES = re.compile(r"and\s*=\s*(\d+)")
_LEVELS = re.compile(r"lev\s*=\s*(\d+)")
_AVERAGE_LEVEL = re.compile(r"lev\s*=\s*\d+\s*\(([0-9.]+)\)")


@dataclass(frozen=True)
class AbcStats:
    """What ABC reports about a network.

    ABC's own network name is deliberately absent: the bridge transfers through
    a temporary file, so it is always that file's stem and never says anything
    about the network. It survives verbatim in :attr:`raw`.
    """

    #: Number of primary inputs.
    num_pis: int
    #: Number of primary outputs.
    num_pos: int
    #: Number of AND nodes.
    num_gates: int
    #: Depth in AND levels.
    num_levels: int
    #: Number of latches, or ``None`` where ABC did not report any -- ``&ps``
    #: omits the field entirely.
    num_registers: int | None = None
    #: Mean level over the outputs, reported by ``&ps`` only.
    average_level: float | None = None
    #: The unparsed line, so nothing ABC said is lost.
    raw: str = ""


def _parse(output: str, *, binary: str, command: str) -> AbcStats:
    """Parse ABC's statistics line.

    Args:
        output: Everything ABC wrote.
        binary: The executable that produced it, for the error message.
        command: The command that produced it, for the error message.

    Returns:
        The parsed statistics.

    Raises:
        AbcExecutionError: If no statistics line could be found.
    """
    for raw_line in output.splitlines():
        line = _ANSI.sub("", raw_line).strip()
        io = _IO.search(line)
        gates = _AND_GATES.search(line)
        levels = _LEVELS.search(line)
        if not (io and gates and levels):
            continue

        latches = _LATCHES.search(line)
        average = _AVERAGE_LEVEL.search(line)
        return AbcStats(
            num_pis=int(io.group(1)),
            num_pos=int(io.group(2)),
            num_gates=int(gates.group(1)),
            num_levels=int(levels.group(1)),
            num_registers=int(latches.group(1)) if latches else None,
            average_level=float(average.group(1)) if average else None,
            raw=line,
        )

    msg = "could not find a statistics line in ABC's output"
    raise AbcExecutionError(msg, binary=binary, command=command, output=output)


def _collect(
    ntk: Aig,
    read_command: str,
    stats_command: str,
    *,
    timeout: float | None,
    binary: str | os.PathLike[str] | None,
) -> AbcStats:
    """Run a statistics command on a network and parse the result.

    Args:
        ntk: The network to measure.
        read_command: ABC command loading the network into the right store.
        stats_command: ABC command printing the statistics.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The parsed statistics.
    """
    check_supported(ntk)
    executable = resolve_binary(binary)

    from ..io import write_aiger

    with tempfile.TemporaryDirectory(prefix="aigverse-abc-") as tmpdir:
        directory = Path(tmpdir)
        write_aiger(ntk, directory / _INPUT_FILE)

        command = f"{read_command} {_INPUT_FILE}; {stats_command}"
        output = run_commands(command, timeout=timeout, cwd=directory, binary=executable)

    return _parse(output, binary=str(executable), command=command)


def stats(
    ntk: Aig,
    *,
    timeout: float | None = None,
    binary: str | os.PathLike[str] | None = None,
) -> AbcStats:
    """Reports ABC's ``print_stats`` for a network.

    Args:
        ntk: The combinational network to measure.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        What ABC reports about the network.

    Raises:
        TypeError: If ``ntk`` is a ``SequentialAig`` or not an ``Aig`` at all.
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
        AbcExecutionError: If ABC reported an error or printed nothing usable.
    """
    return _collect(ntk, "read_aiger", "print_stats", timeout=timeout, binary=binary)


def gia_stats(
    ntk: Aig,
    *,
    timeout: float | None = None,
    binary: str | os.PathLike[str] | None = None,
) -> AbcStats:
    """Reports ABC's ``&ps`` for a network.

    The GIA store's own view. It agrees with :func:`stats` on the counts, adds an
    average level, and reports no latch count.

    Args:
        ntk: The combinational network to measure.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        What ABC reports about the network.

    Raises:
        TypeError: If ``ntk`` is a ``SequentialAig`` or not an ``Aig`` at all.
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
        AbcExecutionError: If ABC reported an error or printed nothing usable.
    """
    # -x suppresses the colour codes; the parser strips them anyway, but this
    # keeps `raw` readable for anyone printing it.
    return _collect(ntk, "&read", "&ps -x", timeout=timeout, binary=binary)
