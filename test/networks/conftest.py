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
def aig_with_single_and(aig_with_two_pis: tuple[Aig, AigSignal, AigSignal]) -> tuple[Aig, AigSignal]:
    """Create an AIG with two PIs and one AND gate.

    Args:
        aig_with_two_pis: A pre-built AIG with two primary inputs.

    Returns:
        A tuple with the AIG and the AND gate signal.
    """
    aig, x1, x2 = aig_with_two_pis
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
