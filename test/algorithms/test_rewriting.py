from __future__ import annotations

from aigverse.algorithms import aig_cut_rewriting, equivalence_checking
from aigverse.networks import Aig


def test_empty_aigs() -> None:
    aig1 = Aig()
    aig2 = aig1.clone()

    aig_cut_rewriting(aig1)

    assert equivalence_checking(aig1, aig2)


def test_simple_aigs() -> None:
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

    aig_cut_rewriting(aig1)

    assert equivalence_checking(aig1, aig2)
    assert equivalence_checking(aig1, aig1.clone())


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

    aig_cut_rewriting(aig1)

    assert not equivalence_checking(aig1, aig2)

    aig_cut_rewriting(aig2)

    assert not equivalence_checking(aig1, aig2)


def test_equivalent_node_merger() -> None:
    # x0 * !(!x0 * !x1) == > x0
    aig1 = Aig()
    x0 = aig1.create_pi()
    x1 = aig1.create_pi()
    n0 = aig1.create_and(~x0, ~x1)
    n1 = aig1.create_and(x0, ~n0)
    aig1.create_po(n1)

    aig_before = aig1.clone()

    aig_cut_rewriting(aig1)

    assert equivalence_checking(aig1, aig_before)


def test_positive_divisor_substitution() -> None:
    # x1 * ( x0 * x1 ) ==> x0 * x1
    aig2 = Aig()
    x0 = aig2.create_pi()
    x1 = aig2.create_pi()
    n0 = aig2.create_and(x0, x1)
    n1 = aig2.create_and(x1, n0)
    aig2.create_po(n1)

    aig_before = aig2.clone()

    aig_cut_rewriting(aig2)

    assert equivalence_checking(aig2, aig_before)


def test_negative_divisor_substitution() -> None:
    # !x0 * !(!x0 * !x1) == > !x0 * x1
    aig = Aig()
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    n0 = aig.create_and(~x0, ~x1)
    n1 = aig.create_and(x0, ~n0)
    aig.create_po(n1)

    aig_before = aig.clone()

    aig_cut_rewriting(aig)

    assert equivalence_checking(aig, aig_before)


def test_parameters() -> None:
    aig = Aig()

    a = aig.create_pi()
    b = aig.create_pi()

    and1 = aig.create_and(~a, ~b)
    and2 = aig.create_and(a, ~and1)

    aig.create_po(and2)

    aig2 = aig.clone()

    aig_cut_rewriting(
        aig,
        cut_size=8,
        cut_limit=12,
        minimize_truth_table=False,
        allow_zero_gain=True,
        use_dont_cares=True,
        min_cand_cut_size=4,
        min_cand_cut_size_override=5,
        preserve_depth=True,
        verbose=True,
        very_verbose=True,
    )

    assert equivalence_checking(aig, aig2)
