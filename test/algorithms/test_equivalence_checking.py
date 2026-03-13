from __future__ import annotations

import pytest

from aigverse.algorithms import equivalence_checking
from aigverse.networks import Aig


def test_empty_aigs() -> None:
    aig1 = Aig()
    aig2 = Aig()

    assert equivalence_checking(aig1, aig2)


def test_simple_aigs(equivalent_two_output_aigs: tuple[Aig, Aig]) -> None:
    aig1, aig2 = equivalent_two_output_aigs

    assert equivalence_checking(aig1, aig2)
    assert equivalence_checking(aig1, aig1.clone())

    extra = aig2.create_pi()
    aig2.create_po(extra)

    with pytest.raises(RuntimeError, match=r".*"):
        equivalence_checking(aig1, aig2)


def test_aig_and_its_negated_copy() -> None:
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

    assert not equivalence_checking(aig1, aig2)
