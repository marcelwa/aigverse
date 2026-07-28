"""Fixtures for the ABC bridge test suite."""

from __future__ import annotations

import os
import stat
import sys
from typing import TYPE_CHECKING

import pytest

from aigverse.abc import is_available
from aigverse.networks import Aig

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


@pytest.fixture
def abc_available() -> None:
    """Skips the test unless an ABC executable can be found.

    A fixture rather than a ``skipif`` condition: ``skipif`` is evaluated at
    import time, which would freeze the verdict before a test gets the chance to
    call ``set_abc_binary``.

    Setting ``AIGVERSE_REQUIRE_ABC`` turns the skip into a failure, so a CI job
    cannot silently pass with ABC missing.
    """
    if is_available():
        return
    if os.environ.get("AIGVERSE_REQUIRE_ABC"):
        pytest.fail("AIGVERSE_REQUIRE_ABC is set, but no ABC binary was found")
    pytest.skip("no ABC binary found; set AIGVERSE_ABC or put `abc` on PATH")


@pytest.fixture(autouse=True)
def _clear_abc_override() -> None:
    """Clears any explicit binary override left behind by a previous test."""
    from aigverse.abc import set_abc_binary

    set_abc_binary(None)


@pytest.fixture
def and_aig() -> Aig:
    """Creates a two-input AND network.

    Returns:
        An AIG with two primary inputs, one AND gate, and one primary output.
    """
    aig = Aig()
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    aig.create_po(aig.create_and(x0, x1))
    return aig


@pytest.fixture
def fake_abc(tmp_path: Path) -> Callable[[str], Path]:
    """Builds a stand-in ABC executable with scripted behaviour.

    ABC always exits 0 and writes everything to standard output, so the runner's
    failure detection cannot be exercised through exit codes. These shims
    reproduce each failure mode without needing ABC installed.

    Args:
        tmp_path: Directory the shim is written to.

    Returns:
        A factory taking the shim's Python body and returning its path.
    """

    def _make(body: str) -> Path:
        script = tmp_path / "fake-abc"
        script.write_text(f"#!{sys.executable}\nimport sys, pathlib, time\n{body}\n")
        script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        return script

    return _make
