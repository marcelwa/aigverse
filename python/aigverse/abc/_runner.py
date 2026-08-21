"""Invocation of the external ABC process."""

from __future__ import annotations

import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar, cast

from ..networks import Aig, NamedAig, SequentialAig
from ._binary import abc_binary, abc_rc, validate_binary
from ._errors import AbcExecutionError, AbcTimeoutError

if TYPE_CHECKING:
    import os
    from collections.abc import Sequence

__all__ = ["run_commands", "run_script"]

AigT = TypeVar("AigT", bound=Aig)

_INPUT_FILE = "in.aig"
_OUTPUT_FILE = "out.aig"

# Extra seconds granted to the process on top of a budget ABC was given itself.
# ABC needs to write its result out after its internal limit expires, and killing
# it in that window would throw away exactly the work the budget was meant to
# preserve.
_BACKSTOP_MARGIN = 60.0

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
    "there is no aig",
    "empty network",
    "syntax error",
    # emitted when the script left a mapped netlist or a LUT network behind,
    # which ABC refuses to write as AIGER
    "only possible for structurally hashed",
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


def budgeted_timeout(timeout: float | None) -> float | None:
    """Turns a user-facing budget into the process timeout that backs it.

    Commands that accept a budget of their own are given it, so that ABC stops on
    its own terms and returns the best result it has. The process timeout is then
    only a backstop for the case where ABC does not honour its budget at all --
    it is deliberately generous, because killing the process discards the work.

    Args:
        timeout: The budget the caller asked for, or ``None`` for no limit.

    Returns:
        The process timeout to enforce, or ``None`` for no limit.
    """
    return None if timeout is None else timeout + _BACKSTOP_MARGIN


def resolve_binary(binary: str | os.PathLike[str] | None) -> Path:
    """Resolves the ABC executable a call should use.

    A per-call override is validated exactly as
    :func:`~aigverse.abc.set_abc_binary` validates the process-wide one, so a
    path that does not exist or is not executable is reported as an
    :exc:`AbcNotFoundError` rather than escaping as an ``OSError`` from
    :mod:`subprocess`.

    Args:
        binary: An explicit override, or ``None`` to use the configured one.

    Returns:
        Path to the ABC executable.

    Raises:
        AbcNotFoundError: If no ABC executable could be located, or the given
            override does not point at an executable file.
    """
    if binary is None:
        return abc_binary()
    return validate_binary(Path(binary), source="the binary argument")


def check_supported(ntk: Aig) -> None:
    """Rejects anything that is not an AIG.

    Args:
        ntk: The network handed to the bridge.

    Raises:
        TypeError: If ``ntk`` is not an ``Aig``.
    """
    if not isinstance(ntk, Aig):
        msg = f"expected an Aig, got {type(ntk).__name__}"
        raise TypeError(msg)


def check_gia_supported(ntk: Aig) -> None:
    """Rejects networks the GIA store would silently reshape.

    ABC's ``&read`` rewrites a flip-flop whose reset is neither 0 nor 1 -- it
    reports *Converted 0 1-valued FFs and 1 DC-valued FFs* and models the
    undefined value with an extra primary input, an extra register, and three AND
    nodes. The result would come back with a different interface than it went in
    with, so the network is refused before ABC is started. The classic store
    carries the same network across untouched.

    A reset of 1 is converted too, by complementing the flip-flop, but that costs
    no input and no register and leaves an equivalent network, so it is allowed
    through -- it comes back with a reset of 0.

    Args:
        ntk: The network handed to a ``&``-space command.

    Raises:
        ValueError: If ``ntk`` has a register whose reset value is undefined.
    """
    if not isinstance(ntk, SequentialAig):
        return

    for index in range(ntk.num_registers):
        # mockturtle's `register_init`: 0 and 1 are the defined resets, while
        # `dont_care` (2) and `unknown` (3) both mean "no reset value".
        if ntk.register_at(index).init not in {0, 1}:
            msg = (
                f"register {index} has no defined reset value, which ABC's GIA store cannot "
                "represent: `&read` would model it with an extra primary input and register. "
                "Set an explicit reset of 0 or 1 with `set_register`, or use the classic "
                "namespace, which transfers the network unchanged."
            )
            raise ValueError(msg)


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
    ``version`` or ``print_stats`` on files the caller manages themselves.

    Args:
        commands: A single ``;``-separated command string, or a sequence of
            individual commands.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        use_init_file: If ``False`` (default), ABC is invoked with ``-s`` so that
            no ``abc.rc`` is read and behaviour does not depend on the local
            install. Set to ``True`` to let ABC pick up an ``abc.rc`` from the
            working directory. Prefer :func:`~aigverse.abc.set_abc_rc`, which
            loads one specific file and keeps the isolation.
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
    executable = resolve_binary(binary)

    if cwd is None:
        with tempfile.TemporaryDirectory(prefix="aigverse-abc-") as scratch:
            return run_commands(
                command,
                timeout=timeout,
                use_init_file=use_init_file,
                cwd=scratch,
                binary=executable,
            )

    # A resource file registered via set_abc_rc() is loaded explicitly rather than
    # by dropping -s, so it stays the only one ABC reads and behaviour does not
    # depend on whichever abc.rc happens to sit in the working directory.
    resource_file = abc_rc()
    if resource_file is not None:
        command = f"source {shlex.quote(str(resource_file))}; {command}"

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
    gia: bool = False,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Optimizes a network by piping it through an external ABC process.

    The network is written to a temporary binary AIGER file, ABC is invoked with
    a read command, the given commands, and a write command, and the result is
    read back. The returned network has the same type as ``ntk``: an ``Aig``
    yields an ``Aig``, a ``NamedAig`` yields a ``NamedAig`` with its input and
    output names preserved, and a ``SequentialAig`` yields a ``SequentialAig``
    with its registers and their reset values intact.

    ABC keeps two independent network stores, and a command only ever sees the
    one it belongs to. By default the network is loaded with ``read_aiger`` into
    the classic store, where the commands without a ``&`` prefix operate
    (``balance``, ``rewrite``, ``refactor``, ``resub``, and hence every script in
    :data:`~aigverse.abc.SCRIPTS`). The ``&``-prefixed commands of ABC9 operate
    on a separate store, the GIA, which stays empty in that mode -- a script such
    as ``"&syn2"`` fails with *there is no AIG* unless it starts with ``&get``.
    Set ``gia=True`` to load the network straight into the GIA with ``&read``
    instead, which is the cheaper and lossless way to run a ``&`` script.

    ``commands`` must not contain the read and write steps; they are added
    automatically. Only commands the resolved ABC binary knows are valid --
    ``resyn2`` and friends are ``abc.rc`` aliases rather than builtins, so use
    the wrappers in this module or :data:`~aigverse.abc.SCRIPTS`.

    Args:
        ntk: The network to optimize.
        commands: A single ``;``-separated ABC command string, or a sequence of
            individual commands.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        use_init_file: If ``False`` (default), ABC is invoked with ``-s`` so that
            no ``abc.rc`` is read and results do not depend on the local install.
            A resource file registered with :func:`~aigverse.abc.set_abc_rc` is
            loaded regardless, making its aliases available.
        gia: If ``True``, transfer the network through ``&read``/``&write`` so it
            lands in ABC9's GIA store and ``&``-prefixed commands can be used
            directly. The classic commands then see nothing instead. Mixing the
            two within one script is possible with ``&get``/``&put``, but those
            do not carry I/O names across, whereas ``&read``/``&write`` do.
        verbose: If ``True``, print everything ABC wrote. This is the captured
            output, not ABC's own ``-v`` reporting -- that differs per command and
            is left to the caller to add to ``commands``.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        TypeError: If ``ntk`` is not an ``Aig``.
        ValueError: If no command was given, or if ``gia`` is set and ``ntk`` has
            a register whose reset value is undefined.
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
        AbcExecutionError: If ABC reported an error or produced no usable output.
    """
    # Guard before resolving the binary, so an unsupported network type reports
    # that rather than "ABC not found" on a machine without ABC.
    check_supported(ntk)
    if gia:
        check_gia_supported(ntk)
    command = _join(commands)

    from ..io import read_aiger_into_aig, read_aiger_into_sequential_aig, write_aiger

    # SequentialAig must be tested before Aig: it is registered as a subclass on
    # the C++ side, so an `isinstance` check against Aig would accept it and pick
    # the combinational reader, which does not preserve registers.
    sequential = isinstance(ntk, SequentialAig)

    with tempfile.TemporaryDirectory(prefix="aigverse-abc-") as tmpdir:
        directory = Path(tmpdir)
        write_aiger(ntk, directory / _INPUT_FILE)

        # `write_aiger` drops the symbol table unless -s is given, while `&write`
        # always keeps it.
        read_cmd, write_cmd = ("&read", "&write") if gia else ("read_aiger", "write_aiger -s")

        # ABC tokenizes the command string itself, so a temporary directory
        # containing a space would break the file names. Running with cwd set to
        # the temporary directory keeps them bare and relative.
        script = f"{read_cmd} {_INPUT_FILE}; {command}; {write_cmd} {_OUTPUT_FILE}"
        output = run_commands(
            script,
            timeout=timeout,
            use_init_file=use_init_file,
            cwd=directory,
            binary=binary,
        )

        if verbose:
            print(output)  # ruff: ignore[print]

        executable = str(resolve_binary(binary))
        result_path = directory / _OUTPUT_FILE
        if not result_path.is_file() or result_path.stat().st_size == 0:
            msg = "ABC produced no output network"
            raise AbcExecutionError(msg, binary=executable, command=script, output=output)

        try:
            reader = read_aiger_into_sequential_aig if sequential else read_aiger_into_aig
            result = reader(result_path)
        except RuntimeError as exc:
            msg = f"could not read the network ABC produced: {exc}"
            raise AbcExecutionError(msg, binary=executable, command=script, output=output) from exc

    # read_aiger_into_sequential_aig already yields a SequentialAig, and
    # read_aiger_into_aig yields a NamedAig; narrow the latter back to a plain Aig
    # when that is what came in, so the bridge is type-preserving.
    if sequential or isinstance(ntk, NamedAig):
        return cast("AigT", result)
    return cast("AigT", Aig(result))
