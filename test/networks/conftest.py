from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aigverse.networks import Aig, DepthAig, NamedAig

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
