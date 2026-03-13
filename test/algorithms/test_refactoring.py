from __future__ import annotations

from aigverse.algorithms import cleanup_dangling, equivalence_checking, sop_refactoring
from aigverse.networks import Aig


def test_empty_aigs() -> None:
    aig1 = Aig()
    aig2 = aig1.clone()

    sop_refactoring(aig1, inplace=True)
    aig1 = cleanup_dangling(aig1)

    assert equivalence_checking(aig1, aig2)


def test_simple_aigs(equivalent_two_output_aigs: tuple[Aig, Aig]) -> None:
    aig1, aig2 = equivalent_two_output_aigs

    empty = sop_refactoring(aig1, inplace=True)

    assert empty is None

    aig1 = cleanup_dangling(aig1)

    assert equivalence_checking(aig1, aig2)
    assert equivalence_checking(aig1, aig1.clone())


def test_aig_and_its_negated_copy(aig_and_negated_copy_pair: tuple[Aig, Aig]) -> None:
    aig1, aig2 = aig_and_negated_copy_pair

    sop_refactoring(aig1, inplace=True)
    aig1 = cleanup_dangling(aig1)

    assert not equivalence_checking(aig1, aig2)

    sop_refactoring(aig2, inplace=True)
    aig2 = cleanup_dangling(aig2)

    assert not equivalence_checking(aig1, aig2)


def test_equivalent_node_merger(implicant_reduction_aig: Aig) -> None:
    # x0 * !(!x0 * !x1) == > x0 (reduction of 2 nodes)
    aig1 = implicant_reduction_aig

    aig_before = aig1.clone()

    sop_refactoring(aig1, inplace=True)
    aig1 = cleanup_dangling(aig1)

    assert aig1.size == aig_before.size - 2

    assert equivalence_checking(aig1, aig_before)


def test_positive_divisor_substitution() -> None:
    # x1 * ( x0 * x1 ) ==> x0 * x1 (reduction of 1 node)
    aig2 = Aig()
    x0 = aig2.create_pi()
    x1 = aig2.create_pi()
    n0 = aig2.create_and(x0, x1)
    n1 = aig2.create_and(x1, n0)
    aig2.create_po(n1)

    aig_before = aig2.clone()

    sop_refactoring(aig2, inplace=True)
    aig2 = cleanup_dangling(aig2)

    assert aig2.size == aig_before.size - 1

    assert equivalence_checking(aig2, aig_before)


def test_negative_divisor_substitution(implicant_reduction_aig: Aig) -> None:
    # !x0 * !(!x0 * !x1) == > !x0 * x1 (reduction of 2 nodes)
    aig = implicant_reduction_aig

    aig_before = aig.clone()

    sop_refactoring(aig, inplace=True)
    aig = cleanup_dangling(aig)

    assert aig.size == aig_before.size - 2

    assert equivalence_checking(aig, aig_before)


def test_parameters(implicant_reduction_aig: Aig) -> None:
    aig = implicant_reduction_aig

    aig2 = aig.clone()

    sop_refactoring(
        aig,
        max_pis=2,
        allow_zero_gain=True,
        use_reconvergence_cut=False,
        use_dont_cares=True,
        verbose=True,
        use_quick_factoring=False,
        try_both_polarities=False,
        consider_inverter_cost=True,
        inplace=True,
    )

    aig = cleanup_dangling(aig)

    assert equivalence_checking(aig, aig2)


def test_sop_factoring_parameters(implicant_reduction_aig: Aig) -> None:
    aig = implicant_reduction_aig

    aig_before = aig.clone()

    sop_refactoring(
        aig,
        use_quick_factoring=True,
        try_both_polarities=True,
        consider_inverter_cost=False,
        inplace=True,
    )

    aig = cleanup_dangling(aig)

    assert equivalence_checking(aig, aig_before)


def test_return_new_does_not_mutate_input(implicant_reduction_aig: Aig) -> None:
    aig = implicant_reduction_aig

    aig_before = aig.clone()
    result = sop_refactoring(aig)

    assert result is not None

    assert aig.size == aig_before.size
    assert aig.to_index_list().raw() == aig_before.to_index_list().raw()
    assert result.size < aig_before.size

    assert equivalence_checking(aig, aig_before)
    assert equivalence_checking(result, aig_before)
