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

__all__ = ["AbcStats", "collect_stats", "stats"]

_INPUT_FILE = "in.aig"

# ABC colours its statistics line, so the escape sequences come off first.
_ANSI = re.compile(r"\x1b\[[0-9;]*m")

_IO = re.compile(r"i/o\s*=\s*(\d+)\s*/\s*(\d+)")
# `print_stats` calls them latches, `&ps` calls them flops; both mean registers.
_REGISTERS = re.compile(r"(?:lat|ff)\s*=\s*(\d+)")
_AND_GATES = re.compile(r"and\s*=\s*(\d+)")
_LEVELS = re.compile(r"lev\s*=\s*(\d+)")
_AVERAGE_LEVEL = re.compile(r"lev\s*=\s*\d+\s*\(([0-9.]+)\)")
_MEMORY = re.compile(r"mem\s*=\s*([0-9.]+)\s*MB")


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
    #: Number of registers, or ``None`` where ABC reported no such field.
    #: ``print_stats`` calls them ``lat`` and ``&ps`` calls them ``ff``; both are
    #: read into this field, and ``&ps`` omits it entirely for a purely
    #: combinational network.
    num_registers: int | None = None
    #: Mean level over the outputs, reported by ``&ps`` only.
    average_level: float | None = None
    #: Memory ABC used for the network in megabytes, reported by ``&ps`` only.
    memory_mb: float | None = None
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

        registers = _REGISTERS.search(line)
        average = _AVERAGE_LEVEL.search(line)
        memory = _MEMORY.search(line)
        return AbcStats(
            num_pis=int(io.group(1)),
            num_pos=int(io.group(2)),
            num_gates=int(gates.group(1)),
            num_levels=int(levels.group(1)),
            num_registers=int(registers.group(1)) if registers else None,
            average_level=float(average.group(1)) if average else None,
            memory_mb=float(memory.group(1)) if memory else None,
            raw=line,
        )

    msg = "could not find a statistics line in ABC's output"
    raise AbcExecutionError(msg, binary=binary, command=command, output=output)


def collect_stats(
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

    .. warning::
        These are ABC's counts, not ``aigverse``'s, and the two can differ for the
        very same network. ABC structurally hashes as it reads, so any structural
        redundancy the network carried is gone before ``print_stats`` sees it: a
        16-bit carry-lookahead adder that ``aigverse`` reports as 186 gates comes
        back from here as 182. Use :attr:`~aigverse.networks.Aig.num_gates` to
        describe the network you hold, and this to describe what ABC worked on.

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
    return collect_stats(ntk, "read_aiger", "print_stats", timeout=timeout, binary=binary)
