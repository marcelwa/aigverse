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


def test_aig_and_its_negated_copy(aig_and_negated_copy_pair: tuple[Aig, Aig]) -> None:
    aig1, aig2 = aig_and_negated_copy_pair

    assert not equivalence_checking(aig1, aig2)
