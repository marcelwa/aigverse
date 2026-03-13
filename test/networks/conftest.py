from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aigverse.networks import Aig

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
