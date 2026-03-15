from __future__ import annotations

from aigverse.algorithms import aig_resubstitution, cleanup_dangling, equivalence_checking
from aigverse.networks import Aig


def test_empty_aigs() -> None:
    aig1 = Aig()
    aig2 = aig1.clone()

    result = aig_resubstitution(aig1, inplace=True)

    assert result is None
    assert equivalence_checking(aig1, aig2)


def test_simple_aigs(equivalent_two_output_aigs: tuple[Aig, Aig]) -> None:
    aig1, aig2 = equivalent_two_output_aigs

    aig_resubstitution(aig1, inplace=True)

    assert equivalence_checking(aig1, aig2)
    assert equivalence_checking(aig1, aig1.clone())


def test_aig_and_its_negated_copy(aig_and_negated_copy_pair: tuple[Aig, Aig]) -> None:
    aig1, aig2 = aig_and_negated_copy_pair

    aig_resubstitution(aig1, inplace=True)

    assert not equivalence_checking(aig1, aig2)

    aig_resubstitution(aig2, inplace=True)

    assert not equivalence_checking(aig1, aig2)


def test_equivalent_node_merger(implicant_reduction_aig: Aig) -> None:
    # x0 * !(!x0 * !x1) == > x0 (reduction of 2 nodes)
    aig1 = implicant_reduction_aig

    aig_before = aig1.clone()

    result = aig_resubstitution(aig1, inplace=True)

    assert result is None
    aig1 = cleanup_dangling(aig1)

    assert aig1.size == aig_before.size - 2

    assert equivalence_checking(aig1, aig_before)


def test_positive_divisor_substitution(positive_divisor_substitution_aig: Aig) -> None:
    # x1 * ( x0 * x1 ) ==> x0 * x1 (reduction of 1 node)
    aig2 = positive_divisor_substitution_aig

    aig_before = aig2.clone()

    aig_resubstitution(aig2, inplace=True)
    aig2 = cleanup_dangling(aig2)

    assert aig2.size == aig_before.size - 1

    assert equivalence_checking(aig2, aig_before)


def test_negative_divisor_substitution(implicant_reduction_aig: Aig) -> None:
    # x0 * !(!x0 * !x1) == > x0 (reduction of 2 nodes)
    aig = implicant_reduction_aig

    aig_before = aig.clone()

    aig_resubstitution(aig, inplace=True)
    aig = cleanup_dangling(aig)

    assert aig.size == aig_before.size - 2

    assert equivalence_checking(aig, aig_before)


def test_parameters(implicant_reduction_aig: Aig) -> None:
    aig = implicant_reduction_aig

    aig2 = aig.clone()

    aig_resubstitution(
        aig,
        max_pis=2,
        max_divisors=10,
        max_inserts=3,
        skip_fanout_limit_for_roots=10,
        skip_fanout_limit_for_divisors=10,
        verbose=True,
        use_dont_cares=True,
        window_size=6,
        preserve_depth=True,
        inplace=True,
    )

    assert equivalence_checking(aig, aig2)


def test_return_new_does_not_mutate_input(implicant_reduction_aig: Aig) -> None:
    aig = implicant_reduction_aig

    aig_before = aig.clone()
    aig_before_index_list = aig_before.to_index_list().raw()
    result = aig_resubstitution(aig)

    assert result is not None
    assert aig.to_index_list().raw() == aig_before_index_list
    assert result.size < aig_before.size
    assert equivalence_checking(aig, aig_before)
    assert equivalence_checking(result, aig_before)
