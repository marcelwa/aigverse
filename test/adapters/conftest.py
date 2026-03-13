from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aigverse.networks import Aig, SequentialAig

if TYPE_CHECKING:
    from aigverse.networks import AigSignal


@pytest.fixture
def _import_adapters() -> None:
    """Ensure adapter monkey patches are applied before adapter tests run."""
    import aigverse.adapters  # noqa: F401


@pytest.fixture
def simple_aig() -> Aig:
    """Create a simple AIG with 2 PIs, 1 AND gate, and 3 POs.

    Returns:
        A simple AIG used by adapter conversion tests.
    """
    aig = Aig()
    a = aig.create_pi()
    b = aig.create_pi()
    g = aig.create_and(a, b)
    aig.create_po(a)
    aig.create_po(b)
    aig.create_po(g)

    return aig


@pytest.fixture
def sequential_single_register_aig() -> tuple[SequentialAig, AigSignal]:
    """Create a simple SequentialAig with one RI/RO pair and one AND gate.

    Returns:
        A tuple containing the network and the register input signal.
    """
    aig = SequentialAig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    aig.create_ro()
    f1 = aig.create_and(x1, x2)
    aig.create_ri(f1)
    return aig, f1


@pytest.fixture
def sequential_two_registers_aig() -> tuple[SequentialAig, AigSignal, AigSignal, AigSignal]:
    """Create a SequentialAig with two register pairs and mixed logic.

    Returns:
        A tuple containing the network and the three key gate signals.
    """
    aig = SequentialAig()

    x1 = aig.create_pi()
    x2 = aig.create_pi()

    ro1 = aig.create_ro()
    ro2 = aig.create_ro()

    f1 = aig.create_and(ro1, ro2)
    f2 = aig.create_and(x1, x2)
    f3 = aig.create_and(x1, ~x2)

    aig.create_po(f3)
    aig.create_ri(f1)
    aig.create_ri(f2)

    return aig, f1, f2, f3


@pytest.fixture
def sequential_feedback_aig() -> tuple[SequentialAig, AigSignal]:
    """Create a SequentialAig with a single feedback loop register.

    Returns:
        A tuple containing the network and the feedback-driving signal.
    """
    saig = SequentialAig()
    x1 = saig.create_pi()
    ro = saig.create_ro()
    f1 = saig.create_and(x1, ro)
    saig.create_ri(f1)
    return saig, f1


@pytest.fixture
def sample_aig_index_list_raw() -> list[int]:
    """Create a representative raw AIG index-list payload.

    Returns:
        A compact raw index-list encoding for a small 4-PI circuit.
    """
    return [4, 1, 3, 2, 4, 6, 8, 12, 10, 14]


@pytest.fixture
def pi_only_aig() -> Aig:
    """Create an AIG with four primary inputs and no outputs.

    Returns:
        A PI-only AIG network.
    """
    aig = Aig()
    for _ in range(4):
        aig.create_pi()
    return aig


@pytest.fixture
def xor_of_two_and_aig() -> Aig:
    """Create a 4-input AIG computing XOR(AND(a,b), AND(c,d)).

    Returns:
        A 4-PI, 1-PO AIG network.
    """
    aig = Aig()
    a = aig.create_pi()
    b = aig.create_pi()
    c = aig.create_pi()
    d = aig.create_pi()
    t0 = aig.create_and(a, b)
    t1 = aig.create_and(c, d)
    aig.create_po(aig.create_xor(t0, t1))
    return aig


@pytest.fixture
def inverted_signals_aig() -> Aig:
    """Create a 3-input AIG with complemented intermediate/output signals.

    Returns:
        A 3-PI, 2-PO AIG network with inverted signals.
    """
    aig = Aig()
    a = aig.create_pi()
    b = aig.create_pi()
    c = aig.create_pi()

    t0 = aig.create_and(a, b)
    t1 = aig.create_and(b, ~c)
    t2 = aig.create_and(~t0, ~t1)

    aig.create_po(~t1)
    aig.create_po(t2)
    return aig


@pytest.fixture
def two_pi_no_po_aig() -> Aig:
    """Create an AIG with two primary inputs and no primary outputs.

    Returns:
        A 2-PI, 0-PO AIG network.
    """
    aig = Aig()
    aig.create_pi()
    aig.create_pi()
    return aig


@pytest.fixture
def two_pi_direct_po_aig() -> Aig:
    """Create an AIG with two PIs connected directly to two POs.

    Returns:
        A 2-PI, 2-PO AIG network without gates.
    """
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    aig.create_po(x1)
    aig.create_po(~x2)
    return aig


@pytest.fixture
def two_pi_inverted_and_po_aig() -> Aig:
    """Create an AIG with one AND gate driven by two inverted PIs.

    Returns:
        A 2-PI, 1-gate, 1-PO AIG network.
    """
    aig = Aig()
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    n0 = aig.create_and(~x0, ~x1)
    aig.create_po(n0)
    return aig


@pytest.fixture
def three_pi_three_and_po_aig() -> Aig:
    """Create a 3-PI AIG with three AND gates and one PO.

    Returns:
        A compact 3-PI network used by edge-list conversion tests.
    """
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()

    y1 = aig.create_and(x1, ~x2)
    y2 = aig.create_and(x2, x3)
    y3 = aig.create_and(~y1, y2)
    aig.create_po(y3)
    return aig


@pytest.fixture
def two_pi_and_two_po_aig() -> Aig:
    """Create a 2-PI AIG with one AND gate and two POs.

    Returns:
        A 2-PI AIG where one PO is a PI and one PO is the AND gate.
    """
    aig = Aig()
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    n0 = aig.create_and(x0, x1)
    aig.create_po(x0)
    aig.create_po(n0)
    return aig


@pytest.fixture
def medium_structured_aig() -> Aig:
    """Create a medium-size 4-PI combinational AIG with two outputs.

    Returns:
        A 4-PI, 8-gate, 2-PO AIG network used for edge-list checks.
    """
    aig = Aig()

    x0 = aig.create_pi()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()
    n0 = aig.create_and(~x2, x3)
    n1 = aig.create_and(~x2, n0)
    n2 = aig.create_and(x3, ~n1)
    n3 = aig.create_and(x0, ~x1)
    n4 = aig.create_and(~n2, n3)
    n5 = aig.create_and(x1, ~n2)
    n6 = aig.create_and(~n4, ~n5)
    n7 = aig.create_and(n1, n3)
    aig.create_po(n6)
    aig.create_po(n7)

    return aig
