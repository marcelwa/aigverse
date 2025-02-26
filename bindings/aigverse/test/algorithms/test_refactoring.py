import gc

from aigverse import Aig, equivalence_checking, sop_refactoring


def test_empty_aigs() -> None:
    print("Starting test_empty_aigs")
    aig1 = Aig()
    aig2 = aig1.clone()

    print(f"Before refactoring: aig1 size = {aig1.size()}")
    sop_refactoring(aig1)
    print(f"After refactoring: aig1 size = {aig1.size()}")

    assert equivalence_checking(aig1, aig2)
    print("Finished test_empty_aigs")


def test_simple_aigs() -> None:
    print("Starting test_simple_aigs")
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

    print(f"Before refactoring: aig1 size = {aig1.size()}")
    try:
        sop_refactoring(aig1)
        print(f"After refactoring: aig1 size = {aig1.size()}")
    except Exception as e:
        print(f"Exception during refactoring: {e}")
        raise

    assert equivalence_checking(aig1, aig2)
    assert equivalence_checking(aig1, aig1.clone())
    print("Finished test_simple_aigs")


def test_aig_and_its_negated_copy() -> None:
    print("Starting test_aig_and_its_negated_copy")
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

    # Force garbage collection before refactoring
    gc.collect()

    print(f"Before refactoring aig1: size = {aig1.size()}")
    sop_refactoring(aig1)
    print(f"After refactoring aig1: size = {aig1.size()}")

    assert not equivalence_checking(aig1, aig2)

    print(f"Before refactoring aig2: size = {aig2.size()}")
    sop_refactoring(aig2)
    print(f"After refactoring aig2: size = {aig2.size()}")

    assert not equivalence_checking(aig1, aig2)
    print("Finished test_aig_and_its_negated_copy")


def test_equivalent_node_merger() -> None:
    print("Starting test_equivalent_node_merger")
    # x0 * !(!x0 * !x1) == > x0 (reduction of 2 nodes)
    aig1 = Aig()
    x0 = aig1.create_pi()
    x1 = aig1.create_pi()
    n0 = aig1.create_and(~x0, ~x1)
    n1 = aig1.create_and(x0, ~n0)
    aig1.create_po(n1)

    aig_before = aig1.clone()

    print(f"Before refactoring: aig1 size = {aig1.size()}")
    sop_refactoring(aig1)
    print(f"After refactoring: aig1 size = {aig1.size()}")

    assert aig1.size() == aig_before.size() - 2

    assert equivalence_checking(aig1, aig_before)
    print("Finished test_equivalent_node_merger")


def test_positive_divisor_substitution() -> None:
    print("Starting test_positive_divisor_substitution")
    # x1 * ( x0 * x1 ) ==> x0 * x1 (reduction of 1 node)
    aig2 = Aig()
    x0 = aig2.create_pi()
    x1 = aig2.create_pi()
    n0 = aig2.create_and(x0, x1)
    n1 = aig2.create_and(x1, n0)
    aig2.create_po(n1)

    aig_before = aig2.clone()

    print(f"Before refactoring: aig2 size = {aig2.size()}")
    sop_refactoring(aig2)
    print(f"After refactoring: aig2 size = {aig2.size()}")

    assert aig2.size() == aig_before.size() - 1

    assert equivalence_checking(aig2, aig_before)
    print("Finished test_positive_divisor_substitution")


def test_negative_divisor_substitution() -> None:
    print("Starting test_negative_divisor_substitution")
    # !x0 * !(!x0 * !x1) == > !x0 * x1 (reduction of 2 nodes)
    aig = Aig()
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    n0 = aig.create_and(~x0, ~x1)
    n1 = aig.create_and(x0, ~n0)
    aig.create_po(n1)

    aig_before = aig.clone()

    print(f"Before refactoring: aig size = {aig.size()}")
    sop_refactoring(aig)
    print(f"After refactoring: aig size = {aig.size()}")

    assert aig.size() == aig_before.size() - 2

    assert equivalence_checking(aig, aig_before)
    print("Finished test_negative_divisor_substitution")


def test_parameters() -> None:
    print("Starting test_parameters")
    aig = Aig()

    a = aig.create_pi()
    b = aig.create_pi()

    and1 = aig.create_and(~a, ~b)
    and2 = aig.create_and(a, ~and1)

    aig.create_po(and2)

    aig2 = aig.clone()

    print(f"Before refactoring: aig size = {aig.size()}")
    sop_refactoring(
        aig,
        max_pis=2,
        allow_zero_gain=True,
        use_reconvergence_cut=False,
        use_dont_cares=True,
        verbose=True,
    )
    print(f"After refactoring: aig size = {aig.size()}")

    assert equivalence_checking(aig, aig2)
    print("Finished test_parameters")
