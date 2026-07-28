"""Integration tests that require a real ABC executable."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aigverse import abc
from aigverse.algorithms import equivalence_checking
from aigverse.generators import ripple_carry_multiplier
from aigverse.networks import Aig, NamedAig

if TYPE_CHECKING:
    from pathlib import Path

    from aigverse.networks import Aig as AigType

pytestmark = pytest.mark.usefixtures("abc_available")


def test_version_is_reported() -> None:
    assert abc.abc_version()


def test_strash_preserves_the_network(and_aig: AigType) -> None:
    result = abc.run_script(and_aig, "strash")
    assert result.num_pis == and_aig.num_pis
    assert result.num_pos == and_aig.num_pos
    assert result.num_gates == and_aig.num_gates


@pytest.mark.parametrize("script", ["resyn", "resyn2", "resyn3", "compress2rs", "dc2"])
def test_scripts_preserve_equivalence(script: str) -> None:
    """Every shipped script must optimize without changing the function."""
    aig = ripple_carry_multiplier(4)
    result = getattr(abc, script)(aig)

    assert result.num_pis == aig.num_pis
    assert result.num_pos == aig.num_pos
    assert result.num_gates <= aig.num_gates
    assert equivalence_checking(aig, result)


def test_plain_aig_stays_a_plain_aig(and_aig: AigType) -> None:
    result = abc.resyn2(and_aig)
    assert type(result) is Aig


def test_named_aig_keeps_its_type_and_names() -> None:
    ntk = NamedAig()
    x0 = ntk.create_pi()
    x1 = ntk.create_pi()
    ntk.set_name(x0, "alpha")
    ntk.set_name(x1, "beta")
    ntk.create_po(ntk.create_and(x0, x1))
    ntk.set_output_name(0, "result")

    result = abc.resyn2(ntk)

    assert type(result) is NamedAig
    names = {result.get_name(result.make_signal(result.pi_at(i))) for i in range(result.num_pis)}
    assert names == {"alpha", "beta"}
    assert result.get_output_name(0) == "result"


def test_input_is_not_mutated(and_aig: AigType) -> None:
    before = (and_aig.num_pis, and_aig.num_pos, and_aig.num_gates)
    abc.resyn2(and_aig)
    assert (and_aig.num_pis, and_aig.num_pos, and_aig.num_gates) == before


def test_unknown_command_raises(and_aig: AigType) -> None:
    with pytest.raises(abc.AbcExecutionError, match="unknown command"):
        abc.run_script(and_aig, "definitely_not_a_command")


def test_rc_aliases_are_unavailable_by_default(and_aig: AigType) -> None:
    """The bridge runs ABC with `-s`, so `abc.rc` aliases must not resolve.

    This is what makes the shipped expansions necessary; if it ever starts
    passing, the bridge stopped isolating itself from the local install.
    """
    with pytest.raises(abc.AbcExecutionError, match="unknown command"):
        abc.run_script(and_aig, "resyn2")


def test_empty_network_round_trips() -> None:
    ntk = Aig()
    ntk.create_po(ntk.create_pi())
    result = abc.resyn2(ntk)
    assert result.num_pis == 1
    assert result.num_pos == 1


def test_run_commands_without_a_network() -> None:
    output = abc.run_commands("version")
    assert "abc" in output.lower()


def test_no_history_file_is_left_behind(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ABC writes an `abc.history` file wherever it runs; it must not leak out.

    Every ABC invocation creates one, so without a scratch directory each call
    would litter whatever directory the caller happened to be in.
    """
    monkeypatch.chdir(tmp_path)

    abc.abc_version()
    abc.run_commands("version")

    aig = Aig()
    aig.create_po(aig.create_pi())
    abc.resyn2(aig)

    assert list(tmp_path.iterdir()) == []
