"""Invocation of the external ABC process."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar, cast

from ..networks import Aig, NamedAig, SequentialAig
from ._binary import abc_binary
from ._errors import AbcExecutionError, AbcTimeoutError

if TYPE_CHECKING:
    import os
    from collections.abc import Sequence

__all__ = ["run_commands", "run_script"]

AigT = TypeVar("AigT", bound=Aig)

_INPUT_FILE = "in.aig"
_OUTPUT_FILE = "out.aig"

# Substrings that mark a failure in ABC's output. ABC exits with status 0 even for
# unknown commands and unreadable files, so its output is the only signal available.
# Deliberately a whitelist rather than a bare search for "error", which would match
# benign banner text.
_ERROR_MARKERS = (
    "** cmd error",
    "unknown command",
    "cannot open",
    "cannot read",
    "cannot write",
    "wrong number of arguments",
    "there is no current network",
    "empty network",
    "syntax error",
)


def _find_error(output: str) -> str | None:
    """Scans captured ABC output for a known failure marker.

    Args:
        output: The output captured from ABC.

    Returns:
        The first offending line, or ``None`` if no marker was found.
    """
    for line in output.splitlines():
        lowered = line.lower()
        for marker in _ERROR_MARKERS:
            if marker in lowered:
                return line.strip()
    return None


def _join(commands: str | Sequence[str]) -> str:
    """Normalizes user-supplied ABC commands into a single command string.

    Args:
        commands: A single ``;``-separated command string, or a sequence of
            individual commands.

    Returns:
        The commands as one ``;``-separated string.

    Raises:
        ValueError: If no command was given, or a command contains a NUL byte.
    """
    joined = commands if isinstance(commands, str) else "; ".join(commands)
    if not joined.strip():
        msg = "no ABC commands given"
        raise ValueError(msg)
    if "\0" in joined:
        msg = "ABC commands must not contain NUL bytes"
        raise ValueError(msg)
    return joined


def _check_supported(ntk: Aig) -> None:
    """Rejects network types the bridge cannot round-trip.

    Args:
        ntk: The network handed to the bridge.

    Raises:
        TypeError: If ``ntk`` is a ``SequentialAig`` or not an ``Aig`` at all.
    """
    # SequentialAig must be tested first: it is registered as a subclass of Aig
    # on the C++ side, so an isinstance check against Aig would accept it and
    # the registers would be silently flattened into extra PI/PO pairs.
    if isinstance(ntk, SequentialAig):
        msg = (
            "SequentialAig is not supported by the ABC bridge yet. Writing "
            "registers to AIGER requires sequential write_aiger support in "
            "mockturtle, and reading ABC's sequential output back requires "
            "handling AIGER 1.9 bad-state properties in mockturtle's reader. "
            "Pass a combinational Aig instead."
        )
        raise TypeError(msg)
    if not isinstance(ntk, Aig):
        msg = f"expected an Aig, got {type(ntk).__name__}"
        raise TypeError(msg)


def run_commands(
    commands: str | Sequence[str],
    *,
    timeout: float | None = None,
    use_init_file: bool = False,
    cwd: str | os.PathLike[str] | None = None,
    binary: str | os.PathLike[str] | None = None,
) -> str:
    """Runs raw ABC commands and returns their combined output.

    No network is transferred; this is the escape hatch for commands such as
    ``version`` or ``print_stats`` on files the caller manages itself.

    Args:
        commands: A single ``;``-separated command string, or a sequence of
            individual commands.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        use_init_file: If ``False`` (default), ABC is invoked with ``-s`` so that
            no ``abc.rc`` is read and behaviour does not depend on the local
            install. Set to ``True`` to make the user's own aliases available.
        cwd: Working directory for the ABC process. Defaults to a fresh
            temporary directory, because ABC writes an ``abc.history`` file into
            wherever it runs. Pass a directory explicitly if the commands refer
            to files by relative path.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        Everything ABC wrote to its output.

    Raises:
        ValueError: If no command was given.
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
        AbcExecutionError: If ABC reported an error.
    """
    command = _join(commands)
    executable = Path(binary) if binary is not None else abc_binary()

    if cwd is None:
        with tempfile.TemporaryDirectory(prefix="aigverse-abc-") as scratch:
            return run_commands(
                command,
                timeout=timeout,
                use_init_file=use_init_file,
                cwd=scratch,
                binary=executable,
            )

    argv = [str(executable)]
    if not use_init_file:
        argv.append("-s")
    argv += ["-q", command]

    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        output = exc.output or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        msg = f"ABC did not terminate within {timeout} seconds"
        raise AbcTimeoutError(msg, binary=str(executable), command=command, output=output) from exc

    output = completed.stdout or ""

    # ABC always exits 0, so a non-zero status means it died (signal, OOM).
    if completed.returncode != 0:
        msg = f"ABC terminated with exit code {completed.returncode}"
        raise AbcExecutionError(msg, binary=str(executable), command=command, output=output)

    offending = _find_error(output)
    if offending is not None:
        msg = f"ABC reported an error: {offending}"
        raise AbcExecutionError(msg, binary=str(executable), command=command, output=output)

    return output


def run_script(
    ntk: AigT,
    commands: str | Sequence[str],
    *,
    timeout: float | None = None,
    use_init_file: bool = False,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Optimizes a network by piping it through an external ABC process.

    The network is written to a temporary binary AIGER file, ABC is invoked with
    ``read_aiger``, the given commands, and ``write_aiger``, and the result is
    read back. The returned network has the same type as ``ntk``: an ``Aig``
    yields an ``Aig``, a ``NamedAig`` yields a ``NamedAig`` with its input and
    output names preserved.

    ``commands`` must not contain the ``read_aiger``/``write_aiger`` steps; they
    are added automatically. Only commands the resolved ABC binary knows are
    valid -- ``resyn2`` and friends are ``abc.rc`` aliases rather than builtins,
    so use the wrappers in this module or :data:`~aigverse.abc.SCRIPTS`.

    Args:
        ntk: The combinational network to optimize.
        commands: A single ``;``-separated ABC command string, or a sequence of
            individual commands.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        use_init_file: If ``False`` (default), ABC is invoked with ``-s`` so that
            no ``abc.rc`` is read and results do not depend on the local install.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        TypeError: If ``ntk`` is a ``SequentialAig`` or not an ``Aig`` at all.
        ValueError: If no command was given.
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
        AbcExecutionError: If ABC reported an error or produced no usable output.
    """
    # Guard before resolving the binary, so an unsupported network type reports
    # that rather than "ABC not found" on a machine without ABC.
    _check_supported(ntk)
    command = _join(commands)

    from ..io import read_aiger_into_aig, write_aiger

    with tempfile.TemporaryDirectory(prefix="aigverse-abc-") as tmpdir:
        directory = Path(tmpdir)
        write_aiger(ntk, directory / _INPUT_FILE)

        # ABC tokenizes the command string itself, so a temporary directory
        # containing a space would break the file names. Running with cwd set to
        # the temporary directory keeps them bare and relative.
        script = f"read_aiger {_INPUT_FILE}; {command}; write_aiger -s {_OUTPUT_FILE}"
        output = run_commands(
            script,
            timeout=timeout,
            use_init_file=use_init_file,
            cwd=directory,
            binary=binary,
        )

        if verbose:
            print(output)  # ruff: ignore[print]

        executable = str(Path(binary) if binary is not None else abc_binary())
        result_path = directory / _OUTPUT_FILE
        if not result_path.is_file() or result_path.stat().st_size == 0:
            msg = "ABC produced no output network"
            raise AbcExecutionError(msg, binary=executable, command=script, output=output)

        try:
            result = read_aiger_into_aig(result_path)
        except RuntimeError as exc:
            msg = f"could not read the network ABC produced: {exc}"
            raise AbcExecutionError(msg, binary=executable, command=script, output=output) from exc

    # read_aiger_into_aig always yields a NamedAig; narrow it back to the input
    # type so the bridge is type-preserving.
    if isinstance(ntk, NamedAig):
        return cast("AigT", result)
    return cast("AigT", Aig(result))
