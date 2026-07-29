"""Tests for the individual ABC command wrappers.

The command strings these build are asserted against a stand-in ABC that always
fails, because the generated script is carried on the raised error. That keeps the
argument translation covered without needing ABC installed.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from aigverse.abc import (
    AbcExecutionError,
    balance,
    gia_balance,
    gia_dc2,
    gia_fraig,
    gia_resub,
    gia_syn2,
    gia_syn3,
    gia_syn4,
    refactor,
    resub,
    rewrite,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from aigverse.networks import Aig

# The fake-ABC shims rely on the executable bit, which does not carry over on Windows.
pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="the fake ABC shims rely on POSIX executable bits")

_FAILING = 'print("** cmd error: stop right there")'


def _command_for(run: Callable[[], object]) -> str:
    """Runs a wrapper against a failing ABC and returns the script it generated.

    Args:
        run: A zero-argument callable invoking the wrapper under test.

    Returns:
        The full ABC script the bridge assembled.
    """
    with pytest.raises(AbcExecutionError) as excinfo:
        run()
    return excinfo.value.command


@pytest.mark.parametrize(
    ("call", "expected"),
    [
        (lambda ntk, abc: balance(ntk, binary=abc), "balance"),
        (lambda ntk, abc: balance(ntk, minimize_levels=False, binary=abc), "balance -l"),
        (lambda ntk, abc: balance(ntk, exor=True, duplicate=True, binary=abc), "balance -d -x"),
        (lambda ntk, abc: rewrite(ntk, binary=abc), "rewrite"),
        (lambda ntk, abc: rewrite(ntk, zero_cost=True, binary=abc), "rewrite -z"),
        (lambda ntk, abc: rewrite(ntk, preserve_levels=False, binary=abc), "rewrite -l"),
        (lambda ntk, abc: refactor(ntk, binary=abc), "refactor"),
        (lambda ntk, abc: refactor(ntk, max_support=12, zero_cost=True, binary=abc), "refactor -N 12 -z"),
        (lambda ntk, abc: resub(ntk, binary=abc), "resub"),
        (lambda ntk, abc: resub(ntk, max_cut_size=6, binary=abc), "resub -K 6"),
        (lambda ntk, abc: resub(ntk, max_cut_size=12, max_inserts=2, binary=abc), "resub -K 12 -N 2"),
    ],
    ids=[
        "balance-default",
        "balance-no-level-minimization",
        "balance-exor-and-duplication",
        "rewrite-default",
        "rewrite-zero-cost",
        "rewrite-no-level-preservation",
        "refactor-default",
        "refactor-support-and-zero-cost",
        "resub-default",
        "resub-cut-size",
        "resub-cut-size-and-inserts",
    ],
)
def test_options_translate_to_abc_switches(
    call: Callable[[Aig, Path], object],
    expected: str,
    and_aig: Aig,
    fake_abc: Callable[[str], Path],
) -> None:
    """Keyword arguments must map onto exactly the ABC switches they claim to.

    Args:
        call: Invokes the wrapper under test with a network and a binary.
        expected: The ABC command the wrapper is expected to build.
        and_aig: A minimal two-input AND network.
        fake_abc: Factory for the stand-in ABC executable.
    """
    shim = fake_abc(_FAILING)
    script = _command_for(lambda: call(and_aig, shim))

    # the generated script wraps the command in the read and write steps
    assert f"; {expected}; " in script


def test_level_switch_is_inverted(and_aig: Aig, fake_abc: Callable[[str], Path]) -> None:
    """ABC's `-l` toggles a default of "preserve levels", so it must appear only
    when preservation is switched off -- getting this backwards silently changes
    what every wrapper optimizes for.

    Args:
        and_aig: A minimal two-input AND network.
        fake_abc: Factory for the stand-in ABC executable.
    """
    shim = fake_abc(_FAILING)
    assert " -l" not in _command_for(lambda: rewrite(and_aig, preserve_levels=True, binary=shim))
    assert " -l" in _command_for(lambda: rewrite(and_aig, preserve_levels=False, binary=shim))


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda ntk: refactor(ntk, max_support=0), "max_support must be positive"),
        (lambda ntk: resub(ntk, max_cut_size=3), "max_cut_size must be between 4 and 16"),
        (lambda ntk: resub(ntk, max_cut_size=17), "max_cut_size must be between 4 and 16"),
        (lambda ntk: resub(ntk, max_inserts=4), "max_inserts must be between 0 and 3"),
    ],
    ids=["refactor-support", "resub-cut-too-small", "resub-cut-too-large", "resub-inserts"],
)
def test_out_of_range_options_are_rejected(
    call: Callable[[Aig], object],
    message: str,
    and_aig: Aig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Values ABC would reject are caught here, before a process is started.

    Args:
        call: Invokes the wrapper under test with an out-of-range option.
        message: Expected substring of the raised error.
        and_aig: A minimal two-input AND network.
        monkeypatch: Used to hide any installed ABC.
    """
    monkeypatch.delenv("AIGVERSE_ABC", raising=False)
    monkeypatch.setenv("PATH", "")

    with pytest.raises(ValueError, match=message):
        call(and_aig)


@pytest.mark.parametrize(
    ("call", "expected"),
    [
        (lambda ntk, abc: gia_balance(ntk, binary=abc), "&b"),
        (lambda ntk, abc: gia_balance(ntk, delay_only=True, and_only=True, binary=abc), "&b -d -a"),
        (lambda ntk, abc: gia_resub(ntk, binary=abc), "&resub"),
        (lambda ntk, abc: gia_resub(ntk, max_inserts=2, max_support=6, binary=abc), "&resub -N 2 -S 6"),
        (lambda ntk, abc: gia_dc2(ntk, binary=abc), "&dc2"),
        (lambda ntk, abc: gia_dc2(ntk, update_levels=False, binary=abc), "&dc2 -l"),
        (lambda ntk, abc: gia_syn2(ntk, binary=abc), "&syn2"),
        (lambda ntk, abc: gia_syn2(ntk, delay_relaxation=0, binary=abc), "&syn2 -R 0"),
        (lambda ntk, abc: gia_syn3(ntk, binary=abc), "&syn3"),
        (lambda ntk, abc: gia_syn4(ntk, binary=abc), "&syn4"),
        (lambda ntk, abc: gia_fraig(ntk, conflict_limit=100, binary=abc), "&fraig -C 100"),
    ],
    ids=[
        "gia-balance-default",
        "gia-balance-delay-and-only",
        "gia-resub-default",
        "gia-resub-limits",
        "gia-dc2-default",
        "gia-dc2-no-level-update",
        "gia-syn2-default",
        "gia-syn2-relaxation-zero",
        "gia-syn3",
        "gia-syn4",
        "gia-fraig-conflict-limit",
    ],
)
def test_gia_options_translate_to_abc_switches(
    call: Callable[[Aig, Path], object],
    expected: str,
    and_aig: Aig,
    fake_abc: Callable[[str], Path],
) -> None:
    """The `&`-space wrappers must build their commands and take the GIA path.

    Args:
        call: Invokes the wrapper under test with a network and a binary.
        expected: The ABC command the wrapper is expected to build.
        and_aig: A minimal two-input AND network.
        fake_abc: Factory for the stand-in ABC executable.
    """
    shim = fake_abc(_FAILING)
    script = _command_for(lambda: call(and_aig, shim))

    assert f"; {expected}; " in script
    # a `&` command against the classic store would silently see nothing.
    # Not anchored to the start: a resource file registered via AIGVERSE_ABC_RC
    # prepends a `source` step to what ABC is actually asked to run.
    assert "&read in.aig" in script
    assert "read_aiger" not in script
    assert script.endswith("&write out.aig")


def test_delay_relaxation_of_zero_is_not_dropped(and_aig: Aig, fake_abc: Callable[[str], Path]) -> None:
    """`0` is a meaningful relaxation ratio and must survive the `None` default.

    Args:
        and_aig: A minimal two-input AND network.
        fake_abc: Factory for the stand-in ABC executable.
    """
    shim = fake_abc(_FAILING)
    assert "-R 0" in _command_for(lambda: gia_syn2(and_aig, delay_relaxation=0, binary=shim))


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda ntk: gia_resub(ntk, max_inserts=-1), "-N limit must not be negative"),
        (lambda ntk: gia_syn2(ntk, delay_relaxation=-1), "delay_relaxation must not be negative"),
        (lambda ntk: gia_fraig(ntk, conflict_limit=-1), "conflict_limit must not be negative"),
    ],
    ids=["gia-resub-inserts", "gia-syn2-relaxation", "gia-fraig-conflicts"],
)
def test_negative_gia_options_are_rejected(
    call: Callable[[Aig], object],
    message: str,
    and_aig: Aig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Negative limits are caught here, before a process is started.

    Args:
        call: Invokes the wrapper under test with a negative option.
        message: Expected substring of the raised error.
        and_aig: A minimal two-input AND network.
        monkeypatch: Used to hide any installed ABC.
    """
    monkeypatch.delenv("AIGVERSE_ABC", raising=False)
    monkeypatch.setenv("PATH", "")

    with pytest.raises(ValueError, match=message):
        call(and_aig)
