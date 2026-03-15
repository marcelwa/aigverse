from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from aigverse.networks import NamedAig

if TYPE_CHECKING:
    from aigverse.networks import AigSignal


def test_named_aig(
    named_aig_test_circuit: tuple[NamedAig, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal],
) -> None:
    aig, x1, x2, x3, n4, n5, n6 = named_aig_test_circuit

    # Check that NamedAig has the specific naming methods
    assert hasattr(aig, "set_network_name")
    assert hasattr(aig, "get_network_name")
    assert hasattr(aig, "has_name")
    assert hasattr(aig, "set_name")
    assert hasattr(aig, "get_name")
    assert hasattr(aig, "has_output_name")
    assert hasattr(aig, "set_output_name")
    assert hasattr(aig, "get_output_name")

    assert aig.get_network_name() == "test_circuit"

    # Test that inputs have names
    assert aig.has_name(x1)
    assert aig.has_name(x2)
    assert aig.has_name(x3)
    assert aig.get_name(x1) == "input1"
    assert aig.get_name(x2) == "input2"
    assert aig.get_name(x3) == "input3"

    # Test setting names on internal signals
    aig.set_name(n4, "and_gate1")
    aig.set_name(n5, "and_gate2")
    assert aig.has_name(n4)
    assert aig.has_name(n5)
    assert aig.get_name(n4) == "and_gate1"
    assert aig.get_name(n5) == "and_gate2"

    # Create primary outputs with names
    po1_idx = aig.create_po(n6, "output1")
    po2_idx = aig.create_po(n5, "output2")

    # Test output names
    assert aig.has_output_name(po1_idx)
    assert aig.has_output_name(po2_idx)
    assert aig.get_output_name(po1_idx) == "output1"
    assert aig.get_output_name(po2_idx) == "output2"

    # Test setting output names after creation
    aig.set_output_name(po1_idx, "renamed_output1")
    assert aig.get_output_name(po1_idx) == "renamed_output1"


def test_named_aig_without_names(named_aig_no_names: NamedAig) -> None:
    """Test that NamedAig still works when names are not provided."""
    aig = named_aig_no_names

    # Basic functionality should still work
    assert aig.num_pis == 2
    assert aig.num_pos == 1
    assert aig.num_gates == 1


def test_named_aig_copy_constructor(named_aig_basic: NamedAig) -> None:
    """Test that NamedAig copy constructor preserves names."""
    aig1 = named_aig_basic

    # Copy constructor
    aig2 = NamedAig(aig1)

    # Check that names are preserved
    assert aig2.get_network_name() == "top"
    assert aig2.num_pis == 2
    assert aig2.num_pos == 1

    # Get the signals in the new AIG
    x1_copy = aig2.make_signal(aig2.pi_at(0))
    x2_copy = aig2.make_signal(aig2.pi_at(1))

    assert aig2.has_name(x1_copy)
    assert aig2.has_name(x2_copy)
    assert aig2.get_name(x1_copy) == "x0"
    assert aig2.get_name(x2_copy) == "x1"
    assert aig2.has_output_name(0)
    assert aig2.get_output_name(0) == "out"


def test_named_aig_repr(named_aig_basic: NamedAig) -> None:
    aig = named_aig_basic

    assert repr(aig) == "NamedAig(name=top, pis=2, pos=1, gates=1)"


def test_named_aig_clone_and_copy_preserve_names(named_aig_basic: NamedAig) -> None:
    aig = named_aig_basic

    cloned = aig.clone()
    shallow = copy.copy(aig)
    deep = copy.deepcopy(aig)

    for candidate in (cloned, shallow, deep):
        assert isinstance(candidate, NamedAig)
        assert candidate.get_network_name() == "top"
        assert candidate.get_name(candidate.make_signal(candidate.pi_at(0))) == "x0"
        assert candidate.get_name(candidate.make_signal(candidate.pi_at(1))) == "x1"
        assert candidate.has_output_name(0)
        assert candidate.get_output_name(0) == "out"


def test_named_aig_complex_circuit(
    named_aig_full_adder: tuple[
        NamedAig,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
        AigSignal,
        int,
        int,
    ],
) -> None:
    """Test a more complex circuit with multiple levels and names."""
    aig, a, b, cin, a_xor_b, sum_out, a_and_b, cin_and_xor, cout, sum_idx, cout_idx = named_aig_full_adder

    # Verify structure
    assert aig.num_pis == 3
    assert aig.num_pos == 2
    assert aig.get_network_name() == "full_adder"

    # Verify all names
    assert aig.get_name(a) == "a"
    assert aig.get_name(b) == "b"
    assert aig.get_name(cin) == "cin"
    assert aig.get_name(a_xor_b) == "a_xor_b"
    assert aig.get_name(sum_out) == "sum"
    assert aig.get_name(a_and_b) == "a_and_b"
    assert aig.get_name(cin_and_xor) == "cin_and_xor"
    assert aig.get_name(cout) == "cout"
    assert aig.get_output_name(sum_idx) == "sum"
    assert aig.get_output_name(cout_idx) == "carry_out"
