"""Failure-detection tests driven by a stand-in ABC executable.

ABC exits 0 for unknown commands and unreadable files and writes everything to
standard output, so the runner cannot rely on exit codes. These shims reproduce
each failure mode so the detection ladder is covered without ABC installed.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from aigverse.abc import AbcExecutionError, AbcTimeoutError, run_script

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from aigverse.networks import Aig

# The fake-ABC shims rely on the executable bit, which does not carry over on Windows.
requires_posix = pytest.mark.skipif(
    sys.platform == "win32", reason="the fake ABC shims rely on POSIX executable bits"
)

pytestmark = requires_posix

# Copies the input to the output, i.e. a well-behaved ABC that changes nothing.
_HAPPY = """
cwd = pathlib.Path.cwd()
(cwd / "out.aig").write_bytes((cwd / "in.aig").read_bytes())
"""


@requires_posix
def test_happy_path_round_trips(and_aig: Aig, fake_abc: Callable[[str], Path]) -> None:
    result = run_script(and_aig, "balance", binary=fake_abc(_HAPPY))
    assert result.num_pis == and_aig.num_pis
    assert result.num_pos == and_aig.num_pos
    assert result.num_gates == and_aig.num_gates


@requires_posix
def test_unknown_command_is_detected(and_aig: Aig, fake_abc: Callable[[str], Path]) -> None:
    """ABC prints an error and still exits 0."""
    shim = fake_abc('print("** cmd error: unknown command \'nope\'")\nsys.exit(0)')
    with pytest.raises(AbcExecutionError, match="unknown command"):
        run_script(and_aig, "nope", binary=shim)


@requires_posix
def test_missing_output_is_detected(and_aig: Aig, fake_abc: Callable[[str], Path]) -> None:
    """A silent no-op leaves no output file behind."""
    shim = fake_abc('print("all good")\nsys.exit(0)')
    with pytest.raises(AbcExecutionError, match="no output network"):
        run_script(and_aig, "balance", binary=shim)


@requires_posix
def test_empty_output_is_detected(and_aig: Aig, fake_abc: Callable[[str], Path]) -> None:
    shim = fake_abc('(pathlib.Path.cwd() / "out.aig").write_bytes(b"")')
    with pytest.raises(AbcExecutionError, match="no output network"):
        run_script(and_aig, "balance", binary=shim)


@requires_posix
def test_garbage_output_is_reported(and_aig: Aig, fake_abc: Callable[[str], Path]) -> None:
    """A truncated or corrupt result must surface as an ABC error, not a crash."""
    shim = fake_abc('(pathlib.Path.cwd() / "out.aig").write_bytes(b"not an aiger file")')
    with pytest.raises(AbcExecutionError):
        run_script(and_aig, "balance", binary=shim)


@requires_posix
def test_timeout_is_reported(and_aig: Aig, fake_abc: Callable[[str], Path]) -> None:
    shim = fake_abc("time.sleep(30)")
    with pytest.raises(AbcTimeoutError, match="did not terminate"):
        run_script(and_aig, "balance", timeout=0.5, binary=shim)


@requires_posix
def test_error_carries_diagnostics(and_aig: Aig, fake_abc: Callable[[str], Path]) -> None:
    """The captured output is the only diagnostic ABC provides, so it must survive."""
    shim = fake_abc('print("** cmd error: something went wrong")')
    with pytest.raises(AbcExecutionError) as excinfo:
        run_script(and_aig, "balance", binary=shim)

    assert "something went wrong" in excinfo.value.output
    assert str(shim) == excinfo.value.binary
    assert "read_aiger" in excinfo.value.command


@requires_posix
def test_non_zero_exit_is_reported(and_aig: Aig, fake_abc: Callable[[str], Path]) -> None:
    """ABC normally exits 0; a non-zero status means it died."""
    shim = fake_abc("sys.exit(139)")
    with pytest.raises(AbcExecutionError, match="exit code 139"):
        run_script(and_aig, "balance", binary=shim)
