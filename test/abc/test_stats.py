"""Tests for the ABC statistics objects."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from aigverse import abc
from aigverse.abc import AbcExecutionError, AbcNotFoundError, AbcStats, gia, stats
from aigverse.abc._stats import _parse
from aigverse.algorithms import equivalence_checking
from aigverse.generators import carry_lookahead_adder, ripple_carry_multiplier
from aigverse.networks import AigRegister, DepthAig, SequentialAig

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from aigverse.networks import Aig


def test_sequential_reaches_discovery_rather_than_the_type_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    """A SequentialAig must get past the type guard the stats helpers share.

    It is registered as an `Aig` subclass on the C++ side, so it has to be
    dispatched explicitly rather than merely accepted; failing on discovery with
    no ABC present is what shows it was not refused on type.

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

    with pytest.raises(AbcNotFoundError):
        stats(ntk)


def test_a_non_network_is_still_rejected_on_type(monkeypatch: pytest.MonkeyPatch) -> None:
    """Widening the guard to sequential networks must not widen it to anything.

    Args:
        monkeypatch: Used to hide any installed ABC.
    """
    monkeypatch.delenv("AIGVERSE_ABC", raising=False)
    monkeypatch.setenv("PATH", "")

    with pytest.raises(TypeError, match="expected an Aig"):
        stats("not a network")  # ty: ignore[invalid-argument-type]


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

    Parsed directly rather than through ABC so that both spellings are pinned
    from one place, including the combinational case where `&ps` omits the field.

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


def _sequential_aig(init: int | None) -> SequentialAig:
    """Builds a one-register sequential network with the given reset value.

    Args:
        init: The register's reset value, or ``None`` to leave it undefined.

    Returns:
        The network.
    """
    ntk = SequentialAig()
    a = ntk.create_pi()
    ro = ntk.create_ro()
    g = ntk.create_and(a, ro)
    ntk.create_po(g)
    ntk.create_ri(g)

    if init is not None:
        register = AigRegister()
        register.init = init
        ntk.set_register(0, register)

    return ntk


@pytest.mark.usefixtures("abc_available")
@pytest.mark.parametrize("init", [0, 1], ids=["reset-zero", "reset-one"])
def test_registers_are_reported_for_a_sequential_network(init: int) -> None:
    """Both stores must count the registers of a real sequential network.

    The end-to-end counterpart of the parser test above: `&ps` calls them `ff`,
    so this is the case that would silently report `None` if only `lat` were
    matched.

    Args:
        init: The register's reset value.
    """
    ntk = _sequential_aig(init)

    assert stats(ntk).num_registers == ntk.num_registers
    assert gia.stats(ntk).num_registers == ntk.num_registers


@pytest.mark.usefixtures("abc_available")
def test_an_undefined_reset_survives_the_classic_store() -> None:
    """A register with no defined reset must not change shape on the way in."""
    ntk = _sequential_aig(None)
    measured = stats(ntk)

    assert measured.num_pis == ntk.num_pis
    assert measured.num_registers == ntk.num_registers
    assert measured.num_gates == ntk.num_gates


@pytest.mark.xfail(
    reason=(
        "`&read` rewrites don't-care-initialized flip-flops on the way into the "
        "GIA store -- it reports 'Converted 0 1-valued FFs and 1 DC-valued FFs' "
        "and adds a primary input, a register and three AND nodes to model the "
        "undefined value. Every `gia` wrapper therefore returns a network with a "
        "different interface than it was given, silently. Registers with a reset "
        "of 0 or 1 are unaffected."
    ),
    strict=True,
)
@pytest.mark.usefixtures("abc_available")
def test_an_undefined_reset_survives_the_gia_store() -> None:
    """The same guarantee, in the `&` space, where it does not currently hold."""
    ntk = _sequential_aig(None)
    measured = gia.stats(ntk)

    assert measured.num_pis == ntk.num_pis
    assert measured.num_registers == ntk.num_registers
    assert measured.num_gates == ntk.num_gates
