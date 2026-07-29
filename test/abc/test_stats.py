"""Tests for the ABC statistics objects."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from aigverse import abc
from aigverse.abc import AbcExecutionError, AbcStats, gia_stats, stats
from aigverse.algorithms import equivalence_checking
from aigverse.generators import ripple_carry_multiplier
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
    classic, gia = stats(aig), gia_stats(aig)

    assert (classic.num_pis, classic.num_pos) == (gia.num_pis, gia.num_pos)
    assert classic.num_gates == gia.num_gates
    assert classic.num_levels == gia.num_levels


@pytest.mark.usefixtures("abc_available")
def test_the_two_stores_report_different_extras() -> None:
    """`print_stats` reports latches, `&ps` reports an average level."""
    aig = ripple_carry_multiplier(3)

    assert stats(aig).num_registers == 0
    assert stats(aig).average_level is None
    assert gia_stats(aig).num_registers is None
    assert gia_stats(aig).average_level is not None


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
