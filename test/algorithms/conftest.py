from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aigverse.networks import Aig

if TYPE_CHECKING:
    from collections.abc import Callable


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


@pytest.fixture
def and_gate_aig() -> Aig:
    """Create a 2-input AIG with a single AND output.

    Returns:
        A simple AIG network for AND simulation tests.
    """
    aig = Aig()
    a = aig.create_pi()
    b = aig.create_pi()
    aig.create_po(aig.create_and(a, b))
    return aig


@pytest.fixture
def or_gate_aig() -> Aig:
    """Create a 2-input AIG with a single OR output.

    Returns:
        A simple AIG network for OR simulation tests.
    """
    aig = Aig()
    a = aig.create_pi()
    b = aig.create_pi()
    aig.create_po(aig.create_or(a, b))
    return aig


@pytest.fixture
def maj3_aig() -> Aig:
    """Create a 3-input AIG with a majority output.

    Returns:
        A simple AIG network for MAJ simulation tests.
    """
    aig = Aig()
    a = aig.create_pi()
    b = aig.create_pi()
    c = aig.create_pi()
    aig.create_po(aig.create_maj(a, b, c))
    return aig


@pytest.fixture
def and_or_two_output_aig() -> Aig:
    """Create a 2-input AIG with AND and OR outputs.

    Returns:
        A simple AIG network for multi-output simulation tests.
    """
    aig = Aig()
    a = aig.create_pi()
    b = aig.create_pi()
    aig.create_po(aig.create_and(a, b))
    aig.create_po(aig.create_or(a, b))
    return aig


@pytest.fixture
def make_and_chain_aig() -> Callable[[int], Aig]:
    """Create right-associative AND-chain AIG builders.

    Returns:
        A function that creates an AIG with ``num_pis`` PIs and one PO.
    """

    def _builder(num_pis: int) -> Aig:
        aig = Aig()
        pis = [aig.create_pi() for _ in range(num_pis)]

        if num_pis == 0:
            aig.create_po(aig.get_constant(False))
            return aig
        if num_pis == 1:
            aig.create_po(pis[0])
            return aig

        node = aig.create_and(pis[-2], pis[-1])
        for index in range(num_pis - 3, -1, -1):
            node = aig.create_and(pis[index], node)
        aig.create_po(node)
        return aig

    return _builder


@pytest.fixture
def make_xor_chain_aig() -> Callable[[int], Aig]:
    """Create XOR-chain AIG builders.

    Returns:
        A function that creates an AIG with ``num_pis`` PIs and one PO.
    """

    def _builder(num_pis: int) -> Aig:
        if num_pis < 1:
            msg = "num_pis must be at least 1"
            raise ValueError(msg)

        aig = Aig()
        pis = [aig.create_pi() for _ in range(num_pis)]
        node = pis[0]
        for signal in pis[1:]:
            node = aig.create_xor(node, signal)
        aig.create_po(node)
        return aig

    return _builder


@pytest.fixture
def mixed_xor_and_balancing_aig() -> Aig:
    """Create a mixed XOR/AND network used by ESOP balancing tests.

    Returns:
        A mixed-operator AIG with one primary output.
    """
    aig = Aig()
    pis = [aig.create_pi() for _ in range(8)]
    n0 = aig.create_xor(pis[0], pis[1])
    n1 = aig.create_xor(pis[2], pis[3])
    n2 = aig.create_and(n0, n1)
    n3 = aig.create_and(pis[4], pis[5])
    n4 = aig.create_and(pis[6], pis[7])
    n5 = aig.create_xor(n3, n4)
    aig.create_po(aig.create_xor(n2, n5))
    return aig


@pytest.fixture
def complex_unbalanced_balancing_aig() -> Aig:
    """Create a 7-gate unbalanced 8-input AND network.

    Returns:
        An AIG shaped as (x0 & x1) & (x2 & (x3 & (x4 & (x5 & (x6 & x7))))).
    """
    aig = Aig()
    x0, x1, x2, x3, x4, x5, x6, x7 = [aig.create_pi() for _ in range(8)]

    n_chain_0 = aig.create_and(x6, x7)
    n_chain_1 = aig.create_and(x5, n_chain_0)
    n_chain_2 = aig.create_and(x4, n_chain_1)
    n_chain_3 = aig.create_and(x3, n_chain_2)
    n_chain_4 = aig.create_and(x2, n_chain_3)
    n_branch_0 = aig.create_and(x0, x1)
    aig.create_po(aig.create_and(n_branch_0, n_chain_4))
    return aig


@pytest.fixture
def positive_divisor_substitution_aig() -> Aig:
    """Create x1 * (x0 * x1), used by substitution-focused tests.

    Returns:
        A 2-PI AIG network with one output.
    """
    aig = Aig()
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    n0 = aig.create_and(x0, x1)
    aig.create_po(aig.create_and(x1, n0))
    return aig
