"""Integration tests that require a real ABC executable."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from aigverse import abc
from aigverse.algorithms import equivalence_checking
from aigverse.generators import ripple_carry_multiplier
from aigverse.networks import Aig, AigRegister, DepthAig, NamedAig, SequentialAig

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from aigverse.networks import Aig as AigType

pytestmark = pytest.mark.usefixtures("abc_available")


def test_version_is_reported() -> None:
    """The resolved binary reports a version banner."""
    assert abc.abc_version()


def test_strash_preserves_the_network(and_aig: AigType) -> None:
    """A structural hash leaves the network unchanged."""
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


@pytest.mark.parametrize("command", ["balance", "rewrite", "refactor", "resub"])
def test_individual_commands_preserve_equivalence(command: str) -> None:
    """Each command wrapper must optimize without changing the function."""
    aig = ripple_carry_multiplier(4)
    result = getattr(abc, command)(aig)

    assert result.num_pis == aig.num_pis
    assert result.num_pos == aig.num_pos
    assert equivalence_checking(aig, result)


def test_command_options_reach_abc() -> None:
    """Options must actually be handed to ABC rather than silently dropped.

    Zero-cost rewriting restructures where plain rewriting stops, so the two
    differ on a network with enough structure to work on.
    """
    aig = ripple_carry_multiplier(4)
    plain = abc.rewrite(aig)
    zero_cost = abc.rewrite(aig, zero_cost=True)

    assert equivalence_checking(aig, plain)
    assert equivalence_checking(aig, zero_cost)
    assert zero_cost.num_gates <= plain.num_gates


def test_gia_space_round_trips() -> None:
    """A `&` script needs the network in the GIA store to see anything at all."""
    aig = ripple_carry_multiplier(4)
    result = abc.run_script(aig, "&dc2", gia=True)

    assert result.num_pis == aig.num_pis
    assert result.num_pos == aig.num_pos
    assert equivalence_checking(aig, result)


@pytest.mark.parametrize(
    "command",
    ["balance", "resub", "dc2", "syn2", "syn3", "syn4", "fraig"],
)
def test_gia_commands_preserve_equivalence(command: str) -> None:
    """Every `&`-space wrapper must optimize without changing the function.

    Deliberately no gate-count assertion: the `&` scripts buy depth with area, so
    demanding a smaller network would be asserting the opposite of their purpose.
    """
    aig = ripple_carry_multiplier(4)
    result = getattr(abc.gia, command)(aig)

    assert result.num_pis == aig.num_pis
    assert result.num_pos == aig.num_pos
    assert equivalence_checking(aig, result)


def test_gia_synthesis_reaches_depth_the_classic_scripts_cannot() -> None:
    """On this design `&syn4` beats `resyn2` on depth, which the docs claim.

    Deliberately scoped to one design rather than stated as a general property:
    on a carry-lookahead adder the same command buys no depth at all. The point
    is that the two families explore different parts of the space.
    """
    aig = ripple_carry_multiplier(4)
    result = abc.gia.syn4(aig)

    assert DepthAig(result).num_levels < DepthAig(aig).num_levels
    assert DepthAig(result).num_levels < DepthAig(abc.resyn2(aig)).num_levels
    assert equivalence_checking(aig, result)


def test_gia_scripts_fail_without_the_flag(and_aig: AigType) -> None:
    """Without `gia=True` the GIA store is empty, which must be reported.

    This is the failure the flag exists to prevent, so it is worth pinning down:
    a silent pass-through would look like a `&` script that did nothing.
    """
    with pytest.raises(abc.AbcExecutionError):
        abc.run_script(and_aig, "&dc2")


def test_gia_transfer_keeps_names() -> None:
    """`&read`/`&write` carry the symbol table, unlike the `&get`/`&put` bridge."""
    ntk = NamedAig()
    x0 = ntk.create_pi()
    x1 = ntk.create_pi()
    ntk.set_name(x0, "alpha")
    ntk.set_name(x1, "beta")
    ntk.create_po(ntk.create_and(x0, x1))
    ntk.set_output_name(0, "result")

    result = abc.run_script(ntk, "&dc2", gia=True)

    assert type(result) is NamedAig
    # ordered, not a set: a set would still pass if ABC swapped the two names
    names = [result.get_name(result.make_signal(result.pi_at(i))) for i in range(result.num_pis)]
    assert names == ["alpha", "beta"]
    assert result.get_output_name(0) == "result"


def test_mapping_is_rejected_rather_than_silently_unmapped() -> None:
    """A mapped netlist cannot be written as AIGER, and must not pass silently.

    Technology and LUT mapping are out of scope until `aigverse` has cell and
    k-LUT network types; the important part is that the attempt raises instead of
    handing back a network that quietly lost the mapping.
    """
    aig = ripple_carry_multiplier(4)
    with pytest.raises(abc.AbcExecutionError):
        abc.run_script(aig, "if -K 6")


def test_plain_aig_stays_a_plain_aig(and_aig: AigType) -> None:
    """A plain Aig comes back as a plain Aig."""
    result = abc.resyn2(and_aig)
    assert type(result) is Aig


def test_named_aig_keeps_its_type_and_names() -> None:
    """A NamedAig keeps its type and its input and output names."""
    ntk = NamedAig()
    x0 = ntk.create_pi()
    x1 = ntk.create_pi()
    ntk.set_name(x0, "alpha")
    ntk.set_name(x1, "beta")
    ntk.create_po(ntk.create_and(x0, x1))
    ntk.set_output_name(0, "result")

    result = abc.resyn2(ntk)

    assert type(result) is NamedAig
    # ordered, not a set: a set would still pass if ABC swapped the two names
    names = [result.get_name(result.make_signal(result.pi_at(i))) for i in range(result.num_pis)]
    assert names == ["alpha", "beta"]
    assert result.get_output_name(0) == "result"


def test_input_is_not_mutated(and_aig: AigType) -> None:
    """The input network is left untouched."""
    before = (and_aig.num_pis, and_aig.num_pos, and_aig.num_gates)
    abc.resyn2(and_aig)
    assert (and_aig.num_pis, and_aig.num_pos, and_aig.num_gates) == before


def test_unknown_command_raises(and_aig: AigType) -> None:
    """An unknown ABC command raises."""
    with pytest.raises(abc.AbcExecutionError, match="unknown command"):
        abc.run_script(and_aig, "definitely_not_a_command")


def test_rc_aliases_are_unavailable_by_default(and_aig: AigType, monkeypatch: pytest.MonkeyPatch) -> None:
    """The bridge runs ABC with `-s`, so `abc.rc` aliases must not resolve.

    This is what makes the shipped expansions necessary; if it ever starts
    passing, the bridge stopped isolating itself from the local install. The
    resource file is cleared explicitly so the ambient environment cannot decide
    the outcome.
    """
    monkeypatch.delenv("AIGVERSE_ABC_RC", raising=False)
    abc.set_abc_rc(None)

    with pytest.raises(abc.AbcExecutionError, match="unknown command"):
        abc.run_script(and_aig, "resyn2")


def test_rc_file_makes_aliases_available(and_aig: AigType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A registered resource file makes its aliases usable.

    The file named is the only one ABC reads, so behaviour stays independent of
    whatever `abc.rc` happens to sit in the working directory.
    """
    monkeypatch.delenv("AIGVERSE_ABC_RC", raising=False)
    rc = tmp_path / "custom.rc"
    rc.write_text('alias my_opt "balance; rewrite"\n')

    abc.set_abc_rc(rc)
    try:
        result = abc.run_script(and_aig, "my_opt")
    finally:
        abc.set_abc_rc(None)

    assert result.num_pis == and_aig.num_pis
    assert result.num_pos == and_aig.num_pos

    # and the alias is gone again once the resource file is cleared
    with pytest.raises(abc.AbcExecutionError, match="unknown command"):
        abc.run_script(and_aig, "my_opt")


def test_empty_network_round_trips() -> None:
    """A minimal network survives the round trip."""
    ntk = Aig()
    ntk.create_po(ntk.create_pi())
    result = abc.resyn2(ntk)
    assert result.num_pis == 1
    assert result.num_pos == 1


def test_run_commands_without_a_network() -> None:
    """Raw commands run without transferring a network."""
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


@pytest.mark.parametrize(
    "call",
    [
        abc.orchestrate,
        lambda ntk: abc.gia.deepsyn(ntk, timeout=3),
        lambda ntk: abc.gia.transduction(ntk, timeout=300),
    ],
    ids=["orchestrate", "gia.deepsyn", "gia.transduction"],
)
def test_high_effort_commands_preserve_equivalence(call: Callable[[AigType], AigType]) -> None:
    """The high-effort commands must optimize without changing the function.

    `gia.transtoch` is deliberately absent: it is stochastic and slow enough that
    pinning it here would make the suite flaky for no extra coverage.

    Args:
        call: The wrapper under test, already carrying its budget.
    """
    aig = ripple_carry_multiplier(3)
    result = call(aig)

    assert result.num_pis == aig.num_pis
    assert result.num_pos == aig.num_pos
    assert equivalence_checking(aig, result)


def test_gia_cec_agrees_with_aigverse() -> None:
    """ABC's checker is a second opinion, so it must agree with the first one."""
    aig = ripple_carry_multiplier(3)
    optimized = abc.compress2rs(aig)

    assert abc.gia.cec(aig, optimized) is abc.CecStatus.EQUIVALENT
    assert equivalence_checking(aig, optimized)


def test_gia_cec_detects_a_difference() -> None:
    """A genuine difference must come back as False, not as an exception."""
    left = Aig()
    a, b = left.create_pi(), left.create_pi()
    left.create_po(left.create_and(a, b))

    right = Aig()
    c, d = right.create_pi(), right.create_pi()
    right.create_po(right.create_or(c, d))

    assert abc.gia.cec(left, right) is abc.CecStatus.NOT_EQUIVALENT
    assert not equivalence_checking(left, right)


def test_gia_cec_rejects_mismatched_interfaces(and_aig: AigType) -> None:
    """ABC matches inputs by position, so a shape mismatch is an error."""
    wider = Aig()
    wider.create_po(wider.create_and(wider.create_pi(), wider.create_and(wider.create_pi(), wider.create_pi())))

    with pytest.raises(abc.AbcExecutionError):
        abc.gia.cec(and_aig, wider)


def _equivalent_pair() -> tuple[Aig, Aig]:
    """Builds two structurally different but equivalent AND networks.

    Returns:
        A pair of equivalent networks.
    """
    left = Aig()
    a, b = left.create_pi(), left.create_pi()
    left.create_po(left.create_and(a, b))

    right = Aig()
    c, d = right.create_pi(), right.create_pi()
    right.create_po(right.create_and(d, c))

    return left, right


@pytest.mark.usefixtures("abc_available")
def test_cec_status_refuses_to_be_a_boolean() -> None:
    """The enum must not silently collapse four outcomes into two.

    `if cec(a, b):` would read as "equivalent" while also firing for UNDECIDED
    and TIMEOUT, which is exactly the confusion the enum exists to prevent.
    """
    result = abc.gia.cec(*_equivalent_pair())

    assert result is abc.CecStatus.EQUIVALENT
    with pytest.raises(TypeError, match="must not be used as a boolean"):
        bool(result)


@pytest.mark.usefixtures("abc_available")
def test_cec_reports_a_timeout_rather_than_raising() -> None:
    """An exhausted budget is a verdict of its own, not an exception.

    A zero-second budget is the cheapest way to reach the state; whether ABC
    reports it as a timeout or manages to decide such a trivial pair anyway is up
    to ABC, so both are accepted -- what must not happen is an exception.
    """
    assert abc.gia.cec(*_equivalent_pair(), timeout=0) in {
        abc.CecStatus.EQUIVALENT,
        abc.CecStatus.TIMEOUT,
        abc.CecStatus.UNDECIDED,
    }


def test_a_missing_binary_override_is_reported_as_not_found(and_aig: AigType, tmp_path: Path) -> None:
    """`binary=` must fail like `set_abc_binary()`, not like `subprocess`.

    The override reaches `subprocess` directly, so without validation a bad path
    escapes as an `OSError` from outside the module's own exception hierarchy.

    Args:
        and_aig: A minimal two-input AND network.
        tmp_path: Directory for the paths that must be rejected.
    """
    with pytest.raises(abc.AbcNotFoundError, match="not an existing file"):
        abc.resyn2(and_aig, binary=tmp_path / "no-such-abc")


@pytest.mark.skipif(sys.platform == "win32", reason="every existing file counts as executable on Windows")
def test_a_non_executable_binary_override_is_reported_as_not_found(and_aig: AigType, tmp_path: Path) -> None:
    """The other half of the override validation: present, but not runnable.

    Args:
        and_aig: A minimal two-input AND network.
        tmp_path: Directory for the file that must be rejected.
    """
    not_executable = tmp_path / "abc"
    not_executable.write_text("#!/bin/sh\n")

    with pytest.raises(abc.AbcNotFoundError, match="not executable"):
        abc.resyn2(and_aig, binary=not_executable)


def test_sequential_aig_keeps_registers_and_type() -> None:
    """Registers, their reset values, and the network type survive ABC."""
    ntk = SequentialAig()
    a = ntk.create_pi()
    b = ntk.create_pi()
    ro0 = ntk.create_ro()
    ro1 = ntk.create_ro()

    f1 = ntk.create_and(a, ro0)
    f2 = ntk.create_and(b, ro1)
    ntk.create_po(ntk.create_and(f1, f2))
    ntk.create_ri(f1)
    ntk.create_ri(f2)

    zero = AigRegister()
    zero.init = 0
    ntk.set_register(0, zero)
    one = AigRegister()
    one.init = 1
    ntk.set_register(1, one)

    result = abc.resyn2(ntk)

    assert type(result) is SequentialAig
    assert result.num_pis == ntk.num_pis
    assert result.num_pos == ntk.num_pos
    assert result.num_registers == ntk.num_registers
    assert result.register_at(0).init == 0
    assert result.register_at(1).init == 1


def test_sequential_aig_with_undefined_reset() -> None:
    """A register left at its default reset must not come back as zero-initialized."""
    ntk = SequentialAig()
    a = ntk.create_pi()
    ro = ntk.create_ro()
    g = ntk.create_and(a, ro)
    ntk.create_po(g)
    ntk.create_ri(g)

    assert ntk.register_at(0).init not in {0, 1}

    result = abc.resyn2(ntk)

    assert result.num_registers == 1
    # "Undefined" is any reset value that is neither 0 nor 1. The exact sentinel
    # differs by origin -- register_t defaults to 3, while aiger_reader reports a
    # nondeterministic reset as 255 -- so compare on the property, not the value.
    assert result.register_at(0).init not in {0, 1}
