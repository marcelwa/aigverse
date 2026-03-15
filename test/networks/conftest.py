from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aigverse.networks import Aig, DepthAig, FanoutAig, NamedAig, SequentialAig

if TYPE_CHECKING:
    from aigverse.networks import AigSignal


@pytest.fixture
def aig_with_two_pis() -> tuple[Aig, AigSignal, AigSignal]:
    """Create an AIG with two primary inputs.

    Returns:
        A tuple containing the AIG and its two primary input signals.
    """
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    return aig, x1, x2


@pytest.fixture
def aig_with_single_pi() -> tuple[Aig, AigSignal]:
    """Create an AIG with one primary input.

    Returns:
        A tuple containing the AIG and its PI signal.
    """
    aig = Aig()
    x1 = aig.create_pi()
    return aig, x1


@pytest.fixture
def aig_with_single_and(aig_with_two_pis: tuple[Aig, AigSignal, AigSignal]) -> tuple[Aig, AigSignal]:
    """Create an AIG with two PIs and one AND gate.

    Args:
        aig_with_two_pis: A pre-built AIG with two primary inputs.

    Returns:
        A tuple with the AIG and the AND gate signal.
    """
    base_aig, _x1, _x2 = aig_with_two_pis
    aig = base_aig.clone()
    x1 = aig.make_signal(aig.pi_at(0))
    x2 = aig.make_signal(aig.pi_at(1))
    gate = aig.create_and(x1, x2)
    return aig, gate


@pytest.fixture
def named_aig_basic() -> NamedAig:
    """Create a simple named AIG with two named inputs and one named output.

    Returns:
        A NamedAig configured with a small named circuit.
    """
    aig = NamedAig()
    aig.set_network_name("top")
    x0 = aig.create_pi("x0")
    x1 = aig.create_pi("x1")
    gate = aig.create_and(x0, x1)
    aig.set_name(gate, "and0")
    aig.create_po(gate, "out")
    return aig


@pytest.fixture
def depth_aig_single_and() -> tuple[DepthAig, AigSignal]:
    """Create a depth AIG with two inputs and a single AND output.

    Returns:
        A tuple with the DepthAig and its gate signal.
    """
    aig = DepthAig()
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    gate = aig.create_and(x0, x1)
    aig.create_po(gate)
    return aig, gate


@pytest.fixture
def fanout_aig_branching() -> tuple[FanoutAig, AigSignal, AigSignal, AigSignal]:
    """Create a FanoutAig with a branching gate fanout pattern.

    Returns:
        A tuple containing the network and three internal gate signals.
    """
    aig = FanoutAig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()

    n4 = aig.create_and(x1, x2)
    n5 = aig.create_and(n4, x3)
    n6 = aig.create_and(n4, n5)
    aig.create_po(n6)

    return aig, n4, n5, n6


@pytest.fixture
def fanout_aig_linear() -> tuple[FanoutAig, AigSignal, AigSignal]:
    """Create a FanoutAig where the first gate has a single fanout.

    Returns:
        A tuple containing the network and two gate signals.
    """
    aig = FanoutAig()
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    gate0 = aig.create_and(x0, x1)
    gate1 = aig.create_and(gate0, x2)
    aig.create_po(gate1)

    return aig, gate0, gate1


@pytest.fixture
def sequential_aig_single_register() -> tuple[SequentialAig, AigSignal, AigSignal, AigSignal]:
    """Create a SequentialAig with one PI, one RO, one gate, one PO, and one RI.

    Returns:
        A tuple containing the network, PI signal, RO signal, and gate signal.
    """
    saig = SequentialAig()
    pi = saig.create_pi()
    ro = saig.create_ro()
    gate = saig.create_and(pi, ro)
    saig.create_po(gate)
    saig.create_ri(gate)
    return saig, pi, ro, gate


@pytest.fixture
def aig_with_and_or_outputs(
    aig_with_two_pis: tuple[Aig, AigSignal, AigSignal],
) -> tuple[Aig, AigSignal, AigSignal, AigSignal, AigSignal]:
    """Create an AIG with two PIs, AND/OR gates, and two POs.

    Args:
        aig_with_two_pis: A pre-built AIG with two primary inputs.

    Returns:
        A tuple containing the AIG, two PI signals, and the AND/OR gate signals.
    """
    base_aig, _x1, _x2 = aig_with_two_pis
    aig = base_aig.clone()
    x1 = aig.make_signal(aig.pi_at(0))
    x2 = aig.make_signal(aig.pi_at(1))
    and_gate = aig.create_and(x1, x2)
    or_gate = aig.create_or(x1, x2)
    aig.create_po(and_gate)
    aig.create_po(or_gate)
    return aig, x1, x2, and_gate, or_gate


@pytest.fixture
def has_and_reference_aig() -> tuple[Aig, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal]:
    """Create a reference AIG for has_and lookup behavior tests.

    Returns:
        A tuple containing the network, probe PI signals, and key internal AND signals.
    """
    aig = Aig()

    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()

    n4 = aig.create_and(~x1, x2)
    n5 = aig.create_and(x1, n4)
    n6 = aig.create_and(x3, n5)
    n7 = aig.create_and(n4, x2)
    n8 = aig.create_and(~n5, ~n7)
    n9 = aig.create_and(~n8, n4)

    aig.create_po(n6)
    aig.create_po(n9)

    return aig, x1, x2, x3, n4, n5, n7, n8


@pytest.fixture
def cleanup_dangling_reference_aig() -> Aig:
    """Create an AIG with dangling logic and one observable output.

    Returns:
        A network used for cleanup_dangling behavior tests.
    """
    aig = Aig()

    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()

    n4 = aig.create_and(x1, x2)
    n5 = aig.create_and(x2, x3)
    n6 = aig.create_and(x1, x3)
    aig.create_and(n4, n5)
    aig.create_po(n6)

    return aig


@pytest.fixture
def simple_xor_aig() -> Aig:
    """Create a simple AIG with two PIs, one XOR gate, and one PO.

    Returns:
        A 2-input XOR AIG network.
    """
    aig = Aig()
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    aig.create_po(aig.create_xor(x0, x1))
    return aig


@pytest.fixture
def sequential_two_registers_full() -> tuple[
    SequentialAig, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal
]:
    """Create a SequentialAig with two PI/RO cones and paired PO/RI signals.

    Returns:
        A tuple containing the network, two PI signals, two RO signals, and two gate signals.
    """
    saig = SequentialAig()

    pi1 = saig.create_pi()
    pi2 = saig.create_pi()

    ro1 = saig.create_ro()
    ro2 = saig.create_ro()

    f1 = saig.create_and(pi1, ro1)
    f2 = saig.create_and(pi2, ro2)

    saig.create_po(f1)
    saig.create_po(f2)
    saig.create_ri(f1)
    saig.create_ri(f2)

    return saig, pi1, pi2, ro1, ro2, f1, f2


@pytest.fixture
def complex_mixed_logic_aig() -> Aig:
    """Create a complex mixed-logic AIG with multiple outputs.

    Returns:
        A 4-PI AIG combining AND/MAJ/XOR and inverted signals, with 6 POs.
    """
    aig = Aig()

    a = aig.create_pi()
    b = aig.create_pi()
    c = aig.create_pi()
    d = aig.create_pi()

    f1 = aig.create_and(a, b)
    f2 = aig.create_and(c, d)
    f3 = aig.create_and(f1, f2)

    f4 = aig.create_maj(a, b, c)

    f5 = aig.create_xor(f3, f4)

    f6 = aig.create_and(~a, ~b)
    f7 = aig.create_maj(~c, d, ~f6)
    f8 = aig.create_xor(f5, ~f7)

    aig.create_po(f3)
    aig.create_po(f4)
    aig.create_po(f5)
    aig.create_po(f6)
    aig.create_po(f7)
    aig.create_po(f8)

    return aig


@pytest.fixture
def named_aig_test_circuit() -> tuple[NamedAig, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal]:
    """Create a named three-input circuit used by naming API tests.

    Returns:
        A tuple containing the network and key PI/internal signals.
    """
    aig = NamedAig()
    aig.set_network_name("test_circuit")

    x1 = aig.create_pi("input1")
    x2 = aig.create_pi("input2")
    x3 = aig.create_pi("input3")

    n4 = aig.create_and(~x1, x2)
    n5 = aig.create_and(x1, n4)
    n6 = aig.create_and(x3, n5)

    return aig, x1, x2, x3, n4, n5, n6


@pytest.fixture
def named_aig_no_names() -> NamedAig:
    """Create a minimal NamedAig without explicit signal/output names.

    Returns:
        A 2-PI, 1-gate, 1-PO NamedAig network.
    """
    aig = NamedAig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    aig.create_po(aig.create_and(x1, x2))
    return aig


@pytest.fixture
def named_aig_full_adder() -> tuple[
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
]:
    """Create a named full-adder network used by complex naming tests.

    Returns:
        A tuple containing network, key signals, and output indices.
    """
    aig = NamedAig()
    aig.set_network_name("full_adder")

    a = aig.create_pi("a")
    b = aig.create_pi("b")
    cin = aig.create_pi("cin")

    a_xor_b = aig.create_xor(a, b)
    aig.set_name(a_xor_b, "a_xor_b")

    sum_out = aig.create_xor(a_xor_b, cin)
    aig.set_name(sum_out, "sum")

    a_and_b = aig.create_and(a, b)
    aig.set_name(a_and_b, "a_and_b")

    cin_and_xor = aig.create_and(cin, a_xor_b)
    aig.set_name(cin_and_xor, "cin_and_xor")

    cout = aig.create_or(a_and_b, cin_and_xor)
    aig.set_name(cout, "cout")

    sum_idx = aig.create_po(sum_out, "sum")
    cout_idx = aig.create_po(cout, "carry_out")

    return aig, a, b, cin, a_xor_b, sum_out, a_and_b, cin_and_xor, cout, sum_idx, cout_idx


@pytest.fixture
def depth_aig_complex() -> tuple[
    DepthAig, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal
]:
    """Create a depth AIG with a non-trivial multi-level cone.

    Returns:
        A tuple containing network, PI signals, and internal gate signals.
    """
    aig = DepthAig()

    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()

    n4 = aig.create_and(~x1, x2)
    n5 = aig.create_and(x1, n4)
    n6 = aig.create_and(x3, n5)
    n7 = aig.create_and(n4, x2)
    n8 = aig.create_and(~n5, ~n7)
    n9 = aig.create_and(~n8, n4)

    aig.create_po(n6)
    aig.create_po(n9)

    return aig, x1, x2, x3, n4, n5, n6, n7, n8, n9


@pytest.fixture
def sequential_aig_register_usage() -> tuple[
    SequentialAig, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal
]:
    """Create a SequentialAig with three PIs, one RO, and mixed PO/RI usage.

    Returns:
        A tuple containing network and key signals used in register workflow tests.
    """
    saig = SequentialAig()

    x1 = saig.create_pi()
    x2 = saig.create_pi()
    x3 = saig.create_pi()

    f1 = saig.create_and(x1, x2)
    saig.create_po(f1)
    saig.create_po(~f1)

    f2 = saig.create_and(f1, x3)
    saig.create_ri(f2)

    ro = saig.create_ro()
    saig.create_po(ro)

    return saig, x1, x2, x3, f1, f2, ro


@pytest.fixture
def sequential_aig_ci_co_fixture() -> tuple[SequentialAig, AigSignal, AigSignal, AigSignal]:
    """Create a SequentialAig used to validate CI/CO classifications.

    Returns:
        A tuple containing network and the created PI/PI/RO signals.
    """
    saig = SequentialAig()
    pi1 = saig.create_pi()
    pi2 = saig.create_pi()
    ro1 = saig.create_ro()
    saig.create_po(pi1)
    saig.create_ri(pi2)
    return saig, pi1, pi2, ro1
