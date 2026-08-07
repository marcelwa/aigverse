"""Tests for the ABC statistics objects."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from aigverse import abc
from aigverse.abc import AbcExecutionError, AbcStats, gia, stats
from aigverse.abc._stats import _parse
from aigverse.algorithms import equivalence_checking
from aigverse.generators import carry_lookahead_adder, ripple_carry_multiplier
from aigverse.networks import DepthAig, SequentialAig

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from aigverse.networks import Aig


def test_sequential_is_rejected_before_discovery(monkeypatch: pytest.MonkeyPatch) -> None:
    """The stats helpers share the runner's type guard, ABC or no ABC.

    Args:
        monkeypatch: Used to hide any installed ABC.
    """
    monkeypatch.delenv("AIGVERSE_ABC", raising=False)
    monkeypatch.setenv("PATH", "")

    ntk = SequentialAig()
    a = ntk.create_pi()
    ro = ntk.create_ro()
    g = ntk.create_and(a, ro)
    ntk.create_po(g)
    ntk.create_ri(g)

    with pytest.raises(TypeError, match="SequentialAig is not supported"):
        stats(ntk)


@pytest.mark.skipif(sys.platform == "win32", reason="the fake ABC shims rely on POSIX executable bits")
def test_unparsable_output_is_reported(and_aig: Aig, fake_abc: Callable[[str], Path]) -> None:
    """An ABC that prints no statistics line must not yield a silent zero.

    Args:
        and_aig: A minimal two-input AND network.
        fake_abc: Factory for the stand-in ABC executable.
    """
    shim = fake_abc('print("nothing to see here")')
    with pytest.raises(AbcExecutionError, match="statistics line"):
        stats(and_aig, binary=shim)


@pytest.mark.usefixtures("abc_available")
def test_stats_agree_with_aigverse() -> None:
    """ABC's own counts must match what aigverse reports for the same network.

    This is the point of exposing them: an independent measurement of the same
    object. A disagreement means the AIGER transfer lost something.
    """
    aig = ripple_carry_multiplier(4)
    measured = stats(aig)

    assert measured.num_pis == aig.num_pis
    assert measured.num_pos == aig.num_pos
    assert measured.num_gates == aig.num_gates
    assert measured.num_levels == DepthAig(aig).num_levels


@pytest.mark.usefixtures("abc_available")
def test_gia_stats_agree_with_classic_stats() -> None:
    """The two stores must describe the same network identically."""
    aig = ripple_carry_multiplier(4)
    classic, from_gia = stats(aig), gia.stats(aig)

    assert (classic.num_pis, classic.num_pos) == (from_gia.num_pis, from_gia.num_pos)
    assert classic.num_gates == from_gia.num_gates
    assert classic.num_levels == from_gia.num_levels


@pytest.mark.usefixtures("abc_available")
def test_the_two_stores_report_different_extras() -> None:
    """`print_stats` reports latches, `&ps` reports an average level and memory.

    `&ps` omits the register field entirely for a combinational network -- it
    prints it as `ff` rather than `lat` when there is one, which
    `test_registers_are_parsed_from_either_spelling` covers.
    """
    aig = ripple_carry_multiplier(3)

    assert stats(aig).num_registers == 0
    assert stats(aig).average_level is None
    assert stats(aig).memory_mb is None
    assert gia.stats(aig).num_registers is None
    assert gia.stats(aig).average_level is not None
    assert gia.stats(aig).memory_mb is not None


@pytest.mark.usefixtures("abc_available")
def test_stats_are_immutable_and_keep_the_raw_line() -> None:
    """The object is a frozen record that never loses what ABC actually said."""
    measured = stats(ripple_carry_multiplier(3))

    assert isinstance(measured, AbcStats)
    assert "i/o" in measured.raw
    with pytest.raises(AttributeError):
        measured.num_gates = 0  # ty: ignore[invalid-assignment]


@pytest.mark.usefixtures("abc_available")
def test_stats_track_an_optimization() -> None:
    """Optimizing must move ABC's numbers, not just aigverse's."""
    aig = ripple_carry_multiplier(4)
    before = stats(aig)
    optimized = abc.compress2rs(aig)
    after = stats(optimized)

    assert after.num_gates <= before.num_gates
    assert after.num_gates == optimized.num_gates
    assert equivalence_checking(aig, optimized)


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("in : i/o =   1/   1  lat =    3  and =    1  lev = 1", 3),
        ("in : i/o =   1/   1  ff =     3  and =    1  lev = 1 (1.00)", 3),
        ("in : i/o =   1/   1  and =    1  lev = 1 (1.00)  mem = 0.00 MB", None),
    ],
    ids=["print_stats-lat", "gia-ff", "gia-combinational"],
)
def test_registers_are_parsed_from_either_spelling(line: str, expected: int | None) -> None:
    """`print_stats` prints `lat`, `&ps` prints `ff`, and both mean registers.

    Parsed directly rather than through ABC, because the bridge cannot yet hand a
    sequential network over -- the `ff` spelling only appears once it can, so
    without this the field would silently stay `None` for every such network.

    Args:
        line: A statistics line as ABC prints it.
        expected: The register count that must come out.
    """
    assert _parse(line, binary="abc", command="print_stats").num_registers == expected


def test_memory_is_parsed_from_the_gia_line() -> None:
    """`&ps` reports a memory figure that `print_stats` does not."""
    line = "in : i/o =   1/   1  and =    1  lev = 1 (1.00)  mem = 1.25 MB"

    assert _parse(line, binary="abc", command="&ps").memory_mb == pytest.approx(1.25)


@pytest.mark.usefixtures("abc_available")
def test_abc_counts_can_differ_from_aigverse_after_strashing() -> None:
    """ABC's counts describe the network ABC ended up with, not the one given.

    ABC structurally hashes as it reads, so a network carrying structural
    redundancy shrinks before `print_stats` ever sees it. Pinned rather than
    merely documented, because anyone building a benchmark table from `stats()`
    will otherwise attribute the gap to an optimization that never ran.
    """
    aig = carry_lookahead_adder(16)

    assert stats(aig).num_gates < aig.num_gates
