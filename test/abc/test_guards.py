"""Tests for the network-type guards, which must not need ABC installed."""

from __future__ import annotations

import pytest

from aigverse.abc import run_script
from aigverse.networks import Aig, NamedAig, SequentialAig


def test_sequential_aig_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """SequentialAig must be refused rather than silently flattened.

    It is registered as a subclass of Aig on the C++ side, so without an explicit
    guard nanobind up-casts it and the registers degrade into extra PI/PO pairs.
    The check must also run before the binary is resolved, so the message is
    accurate on a machine without ABC -- hence the emptied PATH.
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
        run_script(ntk, "balance")


def test_non_network_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-network argument is rejected before ABC is looked up."""
    monkeypatch.delenv("AIGVERSE_ABC", raising=False)
    monkeypatch.setenv("PATH", "")
    with pytest.raises(TypeError, match="expected an Aig"):
        run_script("not a network", "balance")  # ty: ignore[invalid-argument-type]


def test_named_aig_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    """NamedAig is what read_aiger_into_aig returns, so it must pass the guard.

    With no ABC present the call still fails, but on discovery rather than type.
    """
    from aigverse.abc import AbcNotFoundError

    monkeypatch.delenv("AIGVERSE_ABC", raising=False)
    monkeypatch.setenv("PATH", "")

    ntk = NamedAig()
    ntk.create_po(ntk.create_pi())

    with pytest.raises(AbcNotFoundError):
        run_script(ntk, "balance")


def test_empty_commands_rejected_before_discovery(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty command string is rejected before ABC is looked up."""
    monkeypatch.delenv("AIGVERSE_ABC", raising=False)
    monkeypatch.setenv("PATH", "")

    ntk = Aig()
    ntk.create_po(ntk.create_pi())

    with pytest.raises(ValueError, match="no ABC commands"):
        run_script(ntk, "   ")
