from __future__ import annotations

import pytest

from aigverse.networks import Aig


@pytest.fixture
def equivalent_two_output_aigs() -> tuple[Aig, Aig]:
    """Create two equivalent AIGs with two POs for equivalence-based tests.

    Returns:
        A tuple containing two equivalent AIG networks.
    """
    aig1 = Aig()
    aig2 = Aig()

    a1 = aig1.create_pi()
    b1 = aig1.create_pi()
    and1 = aig1.create_and(a1, b1)
    aig1.create_po(and1)
    aig1.create_po(b1)

    a2 = aig2.create_pi()
    b2 = aig2.create_pi()
    and2 = aig2.create_and(a2, b2)
    aig2.create_po(and2)
    aig2.create_po(b2)

    return aig1, aig2


@pytest.fixture
def implicant_reduction_aig() -> Aig:
    """Create x0 * !(!x0 * !x1), which SOP refactoring can reduce.

    Returns:
        An AIG network for SOP refactoring reduction tests.
    """
    aig = Aig()
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    n0 = aig.create_and(~x0, ~x1)
    n1 = aig.create_and(x0, ~n0)
    aig.create_po(n1)
    return aig


@pytest.fixture
def aig_and_negated_copy_pair() -> tuple[Aig, Aig]:
    """Create an AIG and a clone with inverted primary output.

    Returns:
        A tuple containing the original-output and negated-output networks.
    """
    aig1 = Aig()

    a1 = aig1.create_pi()
    b1 = aig1.create_pi()
    c1 = aig1.create_pi()

    and1 = aig1.create_and(a1, b1)
    and2 = aig1.create_and(~a1, c1)
    and3 = aig1.create_and(and1, and2)

    aig2 = aig1.clone()

    aig1.create_po(and3)
    aig2.create_po(~and3)

    return aig1, aig2
