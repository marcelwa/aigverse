from __future__ import annotations

from typing import Any

import pytest

from aigverse import Aig, AigSignal, equivalence_checking


def test_aig_constants() -> None:
    aig = Aig()
    assert aig.size() == 1
    assert aig.num_gates() == 0
    assert aig.num_pis() == 0
    assert aig.num_pos() == 0
    assert aig.is_combinational()

    assert aig.nodes() == [0]
    assert aig.gates() == []
    assert aig.pis() == []
    assert aig.pos() == []

    assert aig.is_constant(0)
    c0 = aig.get_constant(False)
    assert aig.is_constant(aig.get_node(c0))
    assert not aig.is_pi(aig.get_node(c0))
    assert aig.get_node(c0) == 0
    assert not aig.is_complemented(c0)

    c1 = aig.get_constant(True)
    assert aig.is_constant(aig.get_node(c1))
    assert not aig.is_pi(aig.get_node(c1))
    assert aig.get_node(c1) == 0
    assert aig.is_complemented(c1)

    assert c0 != c1
    assert aig.get_node(c0) == aig.get_node(c1)
    assert c0 == ~c1
    assert ~c0 == c1
    assert ~c0 != ~c1
    assert -c0 == c1
    assert -c1 == c1
    assert c0 == +c1
    assert c0 == +c0


def test_aig_primary_inputs() -> None:
    aig = Aig()

    # Ensure the create_pi function exists in AIG
    assert hasattr(aig, "create_pi")

    # Create primary inputs
    a = aig.create_pi()
    b = aig.create_pi()

    # Check the properties of the AIG after adding inputs
    assert aig.size() == 3  # constant + two primary inputs
    assert aig.num_pis() == 2
    assert aig.num_gates() == 0
    assert aig.is_pi(aig.get_node(a))
    assert aig.is_pi(aig.get_node(b))
    assert aig.pi_index(aig.get_node(a)) == 0
    assert aig.pi_index(aig.get_node(b)) == 1

    # Verify the type of signal
    assert isinstance(a, AigSignal)

    # Check initial properties of signal `a`
    assert a.get_index() == 1
    assert a.get_complement() == 0
    assert a.get_data() == 2

    # Test negation (~)
    a = ~a
    assert a.get_index() == 1
    assert a.get_complement() == 1
    assert a.get_data() == 3

    # Test positive sign (+)
    a = +a
    assert a.get_index() == 1
    assert a.get_complement() == 0
    assert a.get_data() == 2

    # Reapplying positive sign should not change anything
    a = +a
    assert a.get_index() == 1
    assert a.get_complement() == 0
    assert a.get_data() == 2

    # Test negation (-)
    a = -a
    assert a.get_index() == 1
    assert a.get_complement() == 1
    assert a.get_data() == 3

    # Reapplying negation should not change anything
    a = -a
    assert a.get_index() == 1
    assert a.get_complement() == 1
    assert a.get_data() == 3

    # XOR operation with True
    a ^= True
    assert a.get_index() == 1
    assert a.get_complement() == 0
    assert a.get_data() == 2

    # XOR operation with True again
    a ^= True
    assert a.get_index() == 1
    assert a.get_complement() == 1
    assert a.get_data() == 3


def test_aig_primary_outputs() -> None:
    aig = Aig()

    # Ensure the create_po function exists in AIG
    assert hasattr(aig, "create_po")

    # Create constant and primary input
    c0 = aig.get_constant(False)
    x1 = aig.create_pi()

    # Check initial size and input/output properties
    assert aig.size() == 2
    assert aig.num_pis() == 1
    assert aig.num_pos() == 0

    # Create primary outputs
    aig.create_po(c0)
    aig.create_po(x1)
    aig.create_po(~x1)

    # Check size and number of primary outputs after creation
    assert aig.size() == 2
    assert aig.num_pos() == 3

    # Retrieve the primary outputs and verify them
    pos = aig.pos()

    # Check that the outputs match the expected values
    assert pos[0] == c0
    assert pos[1] == x1
    assert pos[2] == ~x1


def test_aig_unary_operations() -> None:
    aig = Aig()

    # Ensure the create_buf and create_not functions exist in AIG
    assert hasattr(aig, "create_buf")
    assert hasattr(aig, "create_not")

    # Create a primary input
    x1 = aig.create_pi()

    # Check the initial size after creating the primary input
    assert aig.size() == 2

    # Create buffer and NOT operations
    f1 = aig.create_buf(x1)
    f2 = aig.create_not(x1)

    # Ensure the size remains the same since both operations are unary
    assert aig.size() == 2

    # Check if the buffer is equal to the input and NOT is the negation
    assert f1 == x1
    assert f2 == ~x1


def test_aig_binary_operations() -> None:
    aig = Aig()

    # Ensure the binary operation functions exist in AIG
    assert hasattr(aig, "create_and")
    assert hasattr(aig, "create_nand")
    assert hasattr(aig, "create_or")
    assert hasattr(aig, "create_nor")
    assert hasattr(aig, "create_xor")
    assert hasattr(aig, "create_xnor")

    # Create two primary inputs
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    # Check the initial size after creating the inputs
    assert aig.size() == 3

    # Create AND operation
    f1 = aig.create_and(x1, x2)
    assert aig.size() == 4

    # Create NAND operation
    f2 = aig.create_nand(x1, x2)
    assert aig.size() == 4
    assert f1 == ~f2

    # Create OR operation
    f3 = aig.create_or(x1, x2)
    assert aig.size() == 5

    # Create NOR operation
    f4 = aig.create_nor(x1, x2)
    assert aig.size() == 5
    assert f3 == ~f4

    # Create XOR operation
    f5 = aig.create_xor(x1, x2)
    assert aig.size() == 8

    # Create XNOR operation
    f6 = aig.create_xnor(x1, x2)
    assert aig.size() == 8
    assert f5 == ~f6


def test_aig_hash_nodes() -> None:
    aig = Aig()

    # Create two primary inputs
    a = aig.create_pi()
    b = aig.create_pi()

    # Create two identical AND gates
    f = aig.create_and(a, b)
    g = aig.create_and(a, b)

    # Check the size and number of gates
    assert aig.size() == 4
    assert aig.num_gates() == 1

    # Ensure that the two AND gates correspond to the same node
    assert aig.get_node(f) == aig.get_node(g)


def test_aig_clone_network() -> None:
    # Ensure the clone method exists in AIG
    assert hasattr(Aig, "clone")

    # Create an initial AIG network and add nodes
    aig0 = Aig()
    a = aig0.create_pi()
    b = aig0.create_pi()
    f0 = aig0.create_and(a, b)

    # Check initial size and gate count
    assert aig0.size() == 4
    assert aig0.num_gates() == 1

    # Clone the AIG network
    aig1 = aig0  # Shallow copy
    aig_clone = aig0.clone()  # Deep clone

    # Modify the cloned network
    c = aig1.create_pi()
    aig1.create_and(f0, c)

    # Check the sizes and gate counts
    assert aig0.size() == 6  # aig0 has grown with aig1
    assert aig0.num_gates() == 2

    # Ensure the deep clone remains unchanged
    assert aig_clone.size() == 4
    assert aig_clone.num_gates() == 1


def test_aig_clone_node() -> None:
    # Ensure the clone_node method exists in AIG
    assert hasattr(Aig, "clone_node")

    # Create two AIG networks
    aig1 = Aig()
    aig2 = Aig()

    # Create nodes in aig1
    a1 = aig1.create_pi()
    b1 = aig1.create_pi()
    f1 = aig1.create_and(a1, b1)

    # Check the size of aig1
    assert aig1.size() == 4

    # Create nodes in aig2
    a2 = aig2.create_pi()
    b2 = aig2.create_pi()

    # Check the size of aig2 before cloning
    assert aig2.size() == 3

    # Clone a node from aig1 to aig2
    f2 = aig2.clone_node(aig1, aig1.get_node(f1), [a2, b2])

    # Check the size of aig2 after cloning
    assert aig2.size() == 4

    # Verify the fanin nodes are not complemented
    for fanin in aig2.fanins(aig2.get_node(f2)):
        assert not aig2.is_complemented(fanin)


def test_aig_structural_properties() -> None:
    aig = Aig()

    # Ensure the structural property methods exist in AIG
    assert hasattr(aig, "size")
    assert hasattr(aig, "num_pis")
    assert hasattr(aig, "num_pos")
    assert hasattr(aig, "num_gates")
    assert hasattr(aig, "fanin_size")
    assert hasattr(aig, "fanout_size")

    # Create two primary inputs
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    # Create AND and OR gates
    f1 = aig.create_and(x1, x2)
    f2 = aig.create_or(x1, x2)

    # Create primary outputs
    aig.create_po(f1)
    aig.create_po(f2)

    # Check structural properties
    assert aig.size() == 5
    assert aig.num_pis() == 2
    assert aig.num_pos() == 2
    assert aig.num_gates() == 2

    # Check fanin sizes
    assert aig.fanin_size(aig.get_node(x1)) == 0
    assert aig.fanin_size(aig.get_node(x2)) == 0
    assert aig.fanin_size(aig.get_node(f1)) == 2
    assert aig.fanin_size(aig.get_node(f2)) == 2

    # Check fanout sizes
    assert aig.fanout_size(aig.get_node(x1)) == 2
    assert aig.fanout_size(aig.get_node(x2)) == 2
    assert aig.fanout_size(aig.get_node(f1)) == 1
    assert aig.fanout_size(aig.get_node(f2)) == 1


def test_aig_has_and() -> None:
    aig = Aig()

    # Create primary inputs
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()

    # Create AND gates
    n4 = aig.create_and(~x1, x2)
    n5 = aig.create_and(x1, n4)
    n6 = aig.create_and(x3, n5)
    n7 = aig.create_and(n4, x2)
    n8 = aig.create_and(~n5, ~n7)
    n9 = aig.create_and(~n8, n4)

    # Create primary outputs
    aig.create_po(n6)
    aig.create_po(n9)

    # Check for existing and non-existing AND gates using has_and
    assert aig.has_and(~x1, x2) is not None
    assert aig.has_and(~x1, x2) == n4

    assert aig.has_and(~x1, x3) is None

    assert aig.has_and(~n7, ~n5) is not None
    assert aig.has_and(~n7, ~n5) == n8


def test_aig_node_signal_iteration() -> None:
    aig = Aig()

    # Ensure the structural iteration methods exist in AIG
    assert hasattr(aig, "nodes")
    assert hasattr(aig, "pis")
    assert hasattr(aig, "pos")
    assert hasattr(aig, "gates")
    assert hasattr(aig, "fanins")

    # Create two primary inputs and two gates
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    f1 = aig.create_and(x1, x2)
    f2 = aig.create_or(x1, x2)

    # Create primary outputs
    aig.create_po(f1)
    aig.create_po(f2)

    assert aig.size() == 5

    # Iterate over nodes
    mask = 0
    counter = 0
    for i, n in enumerate(aig.nodes()):
        mask |= 1 << aig.node_to_index(n)
        counter += i
    assert mask == 31
    assert counter == 10

    mask = 0
    for n in aig.nodes():
        mask |= 1 << aig.node_to_index(n)
    assert mask == 31

    mask = 0
    counter = 0
    for i, n in enumerate(aig.nodes()):
        mask |= 1 << aig.node_to_index(n)
        counter += i
        break  # Stop after first iteration
    assert mask == 1
    assert counter == 0

    mask = 0
    for n in aig.nodes():
        mask |= 1 << aig.node_to_index(n)
        break  # Stop after first iteration
    assert mask == 1

    # Iterate over PIs
    mask = 0
    counter = 0
    for i, n in enumerate(aig.pis()):
        mask |= 1 << aig.node_to_index(n)
        counter += i
    assert mask == 6
    assert counter == 1

    mask = 0
    for n in aig.pis():
        mask |= 1 << aig.node_to_index(n)
    assert mask == 6

    mask = 0
    counter = 0
    for i, n in enumerate(aig.pis()):
        mask |= 1 << aig.node_to_index(n)
        counter += i
        break  # Stop after first iteration
    assert mask == 2
    assert counter == 0

    mask = 0
    for n in aig.pis():
        mask |= 1 << aig.node_to_index(n)
        break  # Stop after first iteration
    assert mask == 2

    # Iterate over POs
    mask = 0
    counter = 0
    for i, s in enumerate(aig.pos()):
        mask |= 1 << aig.node_to_index(aig.get_node(s))
        counter += i
    assert mask == 24
    assert counter == 1

    mask = 0
    for s in aig.pos():
        mask |= 1 << aig.node_to_index(aig.get_node(s))
    assert mask == 24

    mask = 0
    counter = 0
    for i, s in enumerate(aig.pos()):
        mask |= 1 << aig.node_to_index(aig.get_node(s))
        counter += i
        break  # Stop after first iteration
    assert mask == 8
    assert counter == 0

    mask = 0
    for s in aig.pos():
        mask |= 1 << aig.node_to_index(aig.get_node(s))
        break  # Stop after first iteration
    assert mask == 8

    # Iterate over gates
    mask = 0
    counter = 0
    for i, n in enumerate(aig.gates()):
        mask |= 1 << aig.node_to_index(n)
        counter += i
    assert mask == 24
    assert counter == 1

    mask = 0
    for n in aig.gates():
        mask |= 1 << aig.node_to_index(n)
    assert mask == 24

    mask = 0
    counter = 0
    for i, n in enumerate(aig.gates()):
        mask |= 1 << aig.node_to_index(n)
        counter += i
        break  # Stop after first iteration
    assert mask == 8
    assert counter == 0

    mask = 0
    for n in aig.gates():
        mask |= 1 << aig.node_to_index(n)
        break  # Stop after first iteration
    assert mask == 8

    # Iterate over fanins of a gate
    mask = 0
    counter = 0
    for i, s in enumerate(aig.fanins(aig.get_node(f1))):
        mask |= 1 << aig.node_to_index(aig.get_node(s))
        counter += i
    assert mask == 6
    assert counter == 1

    mask = 0
    for s in aig.fanins(aig.get_node(f1)):
        mask |= 1 << aig.node_to_index(aig.get_node(s))
    assert mask == 6

    mask = 0
    counter = 0
    for i, s in enumerate(aig.fanins(aig.get_node(f1))):
        mask |= 1 << aig.node_to_index(aig.get_node(s))
        counter += i
        break  # Stop after first iteration
    assert mask == 2
    assert counter == 0

    mask = 0
    for s in aig.fanins(aig.get_node(f1)):
        mask |= 1 << aig.node_to_index(aig.get_node(s))
        break  # Stop after first iteration
    assert mask == 2


def test_cleanup_dangling() -> None:
    aig = Aig()

    # Create primary inputs
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()

    # Create AND gates
    n4 = aig.create_and(x1, x2)
    n5 = aig.create_and(x2, x3)
    n6 = aig.create_and(x1, x3)
    aig.create_and(n4, n5)

    # Create primary outputs
    aig.create_po(n6)

    # Check the size of the AIG
    assert aig.size() == 8

    # Copy the AIG
    aig_copy = aig.clone()

    aig.cleanup_dangling()

    # Check the size of the AIG after cleanup
    assert aig.size() == 5

    # Check equivalence of the original and cleaned up AIG
    assert equivalence_checking(aig, aig_copy)


def test_pickle_empty_aig() -> None:
    import pickle

    # Ensure the pickling methods exist in AIG
    assert hasattr(Aig, "__getstate__")
    assert hasattr(Aig, "__setstate__")

    # Create an empty AIG network
    aig = Aig()

    # Check initial size and gate count
    assert aig.size() == 1
    assert aig.num_gates() == 0

    # Pickle and unpickle the AIG network using the pickle module
    pickled_data = pickle.dumps(aig)
    unpickled_aig = pickle.loads(pickled_data)

    # Check the size and gate count of the unpickled AIG
    assert unpickled_aig.size() == 1
    assert unpickled_aig.num_gates() == 0

    # Check if the original and unpickled networks are equivalent
    assert equivalence_checking(aig, unpickled_aig)


def test_pickle_simple_aig() -> None:
    import pickle

    aig = Aig()

    a = aig.create_pi()
    b = aig.create_pi()
    f = aig.create_and(a, b)

    aig.create_po(f)

    # Check initial size and gate count
    assert aig.size() == 4
    assert aig.num_gates() == 1

    # Pickle and unpickle the AIG network using the pickle module
    pickled_data = pickle.dumps(aig)
    unpickled_aig = pickle.loads(pickled_data)

    # Check the size and gate count of the unpickled AIG
    assert unpickled_aig.size() == 4
    assert unpickled_aig.num_gates() == 1

    # Check if the original and unpickled networks are equivalent
    assert equivalence_checking(aig, unpickled_aig)


def test_pickle_complex_aig() -> None:
    import pickle

    aig = Aig()

    a = aig.create_pi()
    b = aig.create_pi()
    c = aig.create_pi()
    d = aig.create_pi()

    # Create AND gates
    f1 = aig.create_and(a, b)
    f2 = aig.create_and(c, d)
    f3 = aig.create_and(f1, f2)

    # Create a MAJ gate (majority of a, b, c)
    f4 = aig.create_maj(a, b, c)

    # Create an XOR gate (between f3 and f4)
    f5 = aig.create_xor(f3, f4)

    # Use signal inversions
    f6 = aig.create_and(~a, ~b)
    f7 = aig.create_maj(~c, d, ~f6)
    f8 = aig.create_xor(f5, ~f7)

    # Create primary outputs
    aig.create_po(f3)
    aig.create_po(f4)
    aig.create_po(f5)
    aig.create_po(f6)
    aig.create_po(f7)
    aig.create_po(f8)

    # Pickle and unpickle the AIG network using the pickle module
    pickled_data = pickle.dumps(aig)
    unpickled_aig = pickle.loads(pickled_data)

    # Check the size and gate count of the unpickled AIG
    assert unpickled_aig.size() == aig.size()
    assert unpickled_aig.num_gates() == aig.num_gates()

    # Check if the original and unpickled networks are equivalent
    assert equivalence_checking(aig, unpickled_aig)


def test_pickle_multiple_aigs() -> None:
    import pickle

    aig1 = Aig()
    a1 = aig1.create_pi()
    b1 = aig1.create_pi()
    f1 = aig1.create_and(a1, b1)
    aig1.create_po(f1)

    aig2 = Aig()
    a2 = aig2.create_pi()
    b2 = aig2.create_pi()
    f2 = aig2.create_or(a2, b2)
    aig2.create_po(f2)

    aig3 = Aig()
    a3 = aig3.create_pi()
    b3 = aig3.create_pi()
    f3 = aig3.create_xor(a3, b3)
    aig3.create_po(f3)

    # Pickle all three AIGs together as a tuple
    pickled = pickle.dumps((aig1, aig2, aig3))
    unpickled_aig1, unpickled_aig2, unpickled_aig3 = pickle.loads(pickled)

    assert equivalence_checking(aig1, unpickled_aig1)
    assert equivalence_checking(aig2, unpickled_aig2)
    assert equivalence_checking(aig3, unpickled_aig3)


def test_aig_setstate_exceptions():
    import copyreg
    import pickle

    # Helper to create a pickle with a custom state (always a tuple for pickle protocol)
    def make_bad_pickle(state_tuple: tuple[Any, ...]) -> bytes:
        class Dummy:
            pass

        copyreg.pickle(Dummy, lambda _: (Aig, state_tuple))  # type: ignore[arg-type, return-value]
        return pickle.dumps(Dummy())

    # Tuple of wrong size (triggers TypeError)
    bad_pickle = make_bad_pickle(([], 42))
    with pytest.raises(TypeError, match="incompatible constructor arguments"):
        pickle.loads(bad_pickle)

    # Tuple with wrong type inside (triggers TypeError)
    bad_pickle = make_bad_pickle(("not a list",))
    with pytest.raises(TypeError, match="incompatible constructor arguments"):
        pickle.loads(bad_pickle)

    # Tuple with wrong element type in list (triggers TypeError)
    bad_pickle = make_bad_pickle(([1, 2, "bad"],))
    with pytest.raises(TypeError, match="incompatible constructor arguments"):
        pickle.loads(bad_pickle)
