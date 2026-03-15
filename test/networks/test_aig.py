from __future__ import annotations

import copy
from typing import Any

import pytest

from aigverse.algorithms import cleanup_dangling, equivalence_checking
from aigverse.networks import Aig, AigSignal


def test_aig_constants() -> None:
    aig = Aig()
    assert aig.size == 1
    assert aig.num_gates == 0
    assert aig.num_pis == 0
    assert aig.num_pos == 0
    assert aig.is_combinational

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
    assert aig.size == 3  # constant + two primary inputs
    assert aig.num_pis == 2
    assert aig.num_gates == 0
    assert aig.is_pi(aig.get_node(a))
    assert aig.is_pi(aig.get_node(b))
    assert aig.pi_index(aig.get_node(a)) == 0
    assert aig.pi_index(aig.get_node(b)) == 1

    # Verify the type of signal
    assert isinstance(a, AigSignal)

    # Check initial properties of signal `a`
    assert a.index == 1
    assert a.complement is False
    assert a.data == 2

    # Test negation (~)
    a = ~a
    assert a.index == 1
    assert a.complement is True
    assert a.data == 3

    # Test positive sign (+)
    a = +a
    assert a.index == 1
    assert a.complement == 0
    assert a.data == 2

    # Reapplying positive sign should not change anything
    a = +a
    assert a.index == 1
    assert a.complement == 0
    assert a.data == 2

    # Test negation (-)
    a = -a
    assert a.index == 1
    assert a.complement == 1
    assert a.data == 3

    # Reapplying negation should not change anything
    a = -a
    assert a.index == 1
    assert a.complement == 1
    assert a.data == 3

    # XOR operation with True
    a ^= True
    assert a.index == 1
    assert a.complement == 0
    assert a.data == 2

    # XOR operation with True again
    a ^= True
    assert a.index == 1
    assert a.complement == 1
    assert a.data == 3


def test_aig_primary_outputs(aig_with_single_pi: tuple[Aig, AigSignal]) -> None:
    aig, x1 = aig_with_single_pi

    # Ensure the create_po function exists in AIG
    assert hasattr(aig, "create_po")

    # Create constant
    c0 = aig.get_constant(False)

    # Check initial size and input/output properties
    assert aig.size == 2
    assert aig.num_pis == 1
    assert aig.num_pos == 0

    # Create primary outputs
    aig.create_po(c0)
    aig.create_po(x1)
    aig.create_po(~x1)

    # Check size and number of primary outputs after creation
    assert aig.size == 2
    assert aig.num_pos == 3

    # Retrieve the primary outputs and verify them
    pos = aig.pos()

    # Check that the outputs match the expected values
    assert pos[0] == c0
    assert pos[1] == x1
    assert pos[2] == ~x1


def test_aig_unary_operations(aig_with_single_pi: tuple[Aig, AigSignal]) -> None:
    aig, x1 = aig_with_single_pi

    # Ensure the create_buf and create_not functions exist in AIG
    assert hasattr(aig, "create_buf")
    assert hasattr(aig, "create_not")

    # Check the initial size after creating the primary input
    assert aig.size == 2

    # Create buffer and NOT operations
    f1 = aig.create_buf(x1)
    f2 = aig.create_not(x1)

    # Ensure the size remains the same since both operations are unary
    assert aig.size == 2

    # Check if the buffer is equal to the input and NOT is the negation
    assert f1 == x1
    assert f2 == ~x1


def test_aig_binary_operations(aig_with_two_pis: tuple[Aig, AigSignal, AigSignal]) -> None:
    aig, x1, x2 = aig_with_two_pis

    # Ensure the binary operation functions exist in AIG
    assert hasattr(aig, "create_and")
    assert hasattr(aig, "create_nand")
    assert hasattr(aig, "create_or")
    assert hasattr(aig, "create_nor")
    assert hasattr(aig, "create_xor")
    assert hasattr(aig, "create_xnor")

    # Check the initial size after creating the inputs
    assert aig.size == 3

    # Create AND operation
    f1 = aig.create_and(x1, x2)
    assert aig.size == 4

    # Create NAND operation
    f2 = aig.create_nand(x1, x2)
    assert aig.size == 4
    assert f1 == ~f2

    # Create OR operation
    f3 = aig.create_or(x1, x2)
    assert aig.size == 5

    # Create NOR operation
    f4 = aig.create_nor(x1, x2)
    assert aig.size == 5
    assert f3 == ~f4

    # Create XOR operation
    f5 = aig.create_xor(x1, x2)
    assert aig.size == 8

    # Create XNOR operation
    f6 = aig.create_xnor(x1, x2)
    assert aig.size == 8
    assert f5 == ~f6


def test_aig_hash_nodes(aig_with_two_pis: tuple[Aig, AigSignal, AigSignal]) -> None:
    aig, a, b = aig_with_two_pis

    # Create two identical AND gates
    f = aig.create_and(a, b)
    g = aig.create_and(a, b)

    # Check the size and number of gates
    assert aig.size == 4
    assert aig.num_gates == 1

    # Ensure that the two AND gates correspond to the same node
    assert aig.get_node(f) == aig.get_node(g)


def test_aig_clone_network(aig_with_single_and: tuple[Aig, AigSignal]) -> None:
    # Ensure the clone method exists in AIG
    assert hasattr(Aig, "clone")

    # Create an initial AIG network and add nodes
    aig0, f0 = aig_with_single_and

    # Check initial size and gate count
    assert aig0.size == 4
    assert aig0.num_gates == 1

    # Clone the AIG network
    aig1 = aig0  # Shallow copy
    aig_clone = aig0.clone()  # Deep clone

    # Modify the cloned network
    c = aig1.create_pi()
    aig1.create_and(f0, c)

    # Check the sizes and gate counts
    assert aig0.size == 6  # aig0 has grown with aig1
    assert aig0.num_gates == 2

    # Ensure the deep clone remains unchanged
    assert aig_clone.size == 4
    assert aig_clone.num_gates == 1


def test_aig_clone_node(
    aig_with_single_and: tuple[Aig, AigSignal],
    aig_with_two_pis: tuple[Aig, AigSignal, AigSignal],
) -> None:
    # Ensure the clone_node method exists in AIG
    assert hasattr(Aig, "clone_node")

    # Create two AIG networks
    aig1, f1 = aig_with_single_and
    base_aig, _a2, _b2 = aig_with_two_pis
    aig2 = base_aig.clone()
    a2 = aig2.make_signal(aig2.pi_at(0))
    b2 = aig2.make_signal(aig2.pi_at(1))

    # Check the size of aig1
    assert aig1.size == 4

    # Check the size of aig2 before cloning
    assert aig2.size == 3

    # Clone a node from aig1 to aig2
    f2 = aig2.clone_node(aig1, aig1.get_node(f1), [a2, b2])

    # Check the size of aig2 after cloning
    assert aig2.size == 4

    # Verify the fanin nodes are not complemented
    for fanin in aig2.fanins(aig2.get_node(f2)):
        assert not aig2.is_complemented(fanin)


def test_aig_structural_properties(
    aig_with_and_or_outputs: tuple[Aig, AigSignal, AigSignal, AigSignal, AigSignal],
) -> None:
    aig, x1, x2, f1, f2 = aig_with_and_or_outputs

    # Ensure the structural property methods exist in AIG
    assert hasattr(aig, "size")
    assert hasattr(aig, "num_pis")
    assert hasattr(aig, "num_pos")
    assert hasattr(aig, "num_gates")
    assert hasattr(aig, "fanin_size")
    assert hasattr(aig, "fanout_size")

    # Check structural properties
    assert aig.size == 5
    assert aig.num_pis == 2
    assert aig.num_pos == 2
    assert aig.num_gates == 2

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


def test_aig_len(aig_with_single_and: tuple[Aig, AigSignal]) -> None:
    aig, _ = aig_with_single_and

    assert len(aig) == aig.size


def test_aig_repr(simple_and_aig: Aig) -> None:
    aig = simple_and_aig

    assert repr(aig) == "Aig(pis=2, pos=1, gates=1, size=4)"


def test_aig_iter(aig_with_single_and: tuple[Aig, AigSignal]) -> None:
    aig, _ = aig_with_single_and

    assert list(aig) == aig.nodes()


def test_aig_contains(aig_with_single_and: tuple[Aig, AigSignal]) -> None:
    aig, and_signal = aig_with_single_and
    and_node = aig.get_node(and_signal)

    assert 0 in aig
    assert and_node in aig
    assert -1 not in aig
    assert aig.size not in aig
    assert 1.5 not in aig


def test_aig_bool(aig_with_single_pi: tuple[Aig, AigSignal]) -> None:
    assert not Aig()

    aig, _ = aig_with_single_pi

    assert aig


def test_aig_copy_deepcopy(simple_and_aig: Aig) -> None:
    aig = simple_and_aig

    shallow_clone = copy.copy(aig)
    deep_clone = copy.deepcopy(aig)

    assert isinstance(shallow_clone, Aig)
    assert isinstance(deep_clone, Aig)
    assert shallow_clone is not aig
    assert deep_clone is not aig
    assert equivalence_checking(aig, shallow_clone)
    assert equivalence_checking(aig, deep_clone)

    aig.create_pi()

    assert aig.size == 5
    assert shallow_clone.size == 4
    assert deep_clone.size == 4


def test_aig_has_and(
    has_and_reference_aig: tuple[Aig, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal],
) -> None:
    aig, x1, x2, x3, n4, n5, n7, n8 = has_and_reference_aig

    # Check for existing and non-existing AND gates using has_and
    assert aig.has_and(~x1, x2) is not None
    assert aig.has_and(~x1, x2) == n4

    assert aig.has_and(~x1, x3) is None

    assert aig.has_and(~n7, ~n5) is not None
    assert aig.has_and(~n7, ~n5) == n8


def test_aig_node_signal_iteration(
    aig_with_and_or_outputs: tuple[Aig, AigSignal, AigSignal, AigSignal, AigSignal],
) -> None:
    aig, _x1, _x2, f1, _f2 = aig_with_and_or_outputs

    # Ensure the structural iteration methods exist in AIG
    assert hasattr(aig, "nodes")
    assert hasattr(aig, "pis")
    assert hasattr(aig, "pos")
    assert hasattr(aig, "gates")
    assert hasattr(aig, "fanins")

    assert aig.size == 5

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


def test_cleanup_dangling(cleanup_dangling_reference_aig: Aig) -> None:
    aig = cleanup_dangling_reference_aig

    # Check the size of the AIG
    assert aig.size == 8

    # Copy the AIG
    aig_copy = aig.clone()

    cleaned = cleanup_dangling(aig)
    assert cleaned is not None

    # Check the size of the AIG after cleanup
    assert cleaned.size == 5

    # Default mode must not mutate input.
    assert aig.size == 8

    # Check equivalence of the original and cleaned up AIG
    assert equivalence_checking(cleaned, aig_copy)

    aig = cleanup_dangling(aig)
    assert aig.size == 5


def test_pickle_empty_aig() -> None:
    import pickle

    # Ensure the pickling methods exist in AIG
    assert hasattr(Aig, "__getstate__")
    assert hasattr(Aig, "__setstate__")

    # Create an empty AIG network
    aig = Aig()

    # Check initial size and gate count
    assert aig.size == 1
    assert aig.num_gates == 0

    # Pickle and unpickle the AIG network using the pickle module
    pickled_data = pickle.dumps(aig)
    unpickled_aig = pickle.loads(pickled_data)

    # Check the size and gate count of the unpickled AIG
    assert unpickled_aig.size == 1
    assert unpickled_aig.num_gates == 0

    # Check if the original and unpickled networks are equivalent
    assert equivalence_checking(aig, unpickled_aig)


def test_pickle_simple_aig(simple_and_aig: Aig) -> None:
    import pickle

    aig = simple_and_aig

    # Check initial size and gate count
    assert aig.size == 4
    assert aig.num_gates == 1

    # Pickle and unpickle the AIG network using the pickle module
    pickled_data = pickle.dumps(aig)
    unpickled_aig = pickle.loads(pickled_data)

    # Check the size and gate count of the unpickled AIG
    assert unpickled_aig.size == 4
    assert unpickled_aig.num_gates == 1

    # Check if the original and unpickled networks are equivalent
    assert equivalence_checking(aig, unpickled_aig)


def test_pickle_complex_aig(complex_mixed_logic_aig: Aig) -> None:
    import pickle

    aig = complex_mixed_logic_aig

    # Pickle and unpickle the AIG network using the pickle module
    pickled_data = pickle.dumps(aig)
    unpickled_aig = pickle.loads(pickled_data)

    # Check the size and gate count of the unpickled AIG
    assert unpickled_aig.size == aig.size
    assert unpickled_aig.num_gates == aig.num_gates

    # Check if the original and unpickled networks are equivalent
    assert equivalence_checking(aig, unpickled_aig)


def test_pickle_multiple_aigs(simple_and_aig: Aig, simple_or_aig: Aig, simple_xor_aig: Aig) -> None:
    import pickle

    aig1 = simple_and_aig
    aig2 = simple_or_aig
    aig3 = simple_xor_aig

    # Pickle all three AIGs together as a tuple
    pickled = pickle.dumps((aig1, aig2, aig3))
    unpickled_aig1, unpickled_aig2, unpickled_aig3 = pickle.loads(pickled)

    assert equivalence_checking(aig1, unpickled_aig1)
    assert equivalence_checking(aig2, unpickled_aig2)
    assert equivalence_checking(aig3, unpickled_aig3)


def test_aig_setstate_exceptions():
    import copyreg
    import pickle

    # Helper to create a pickle with a custom state that reconstructs via __new__.
    # This ensures nanobind routes through __setstate__ on an uninitialized instance.
    def make_bad_pickle(state_tuple: tuple[Any, ...]) -> bytes:
        class Dummy:
            pass

        copyreg.pickle(Dummy, lambda _: (Aig.__new__, (Aig,), state_tuple))  # type: ignore[arg-type, return-value]
        return pickle.dumps(Dummy())

    # Tuple of wrong size (triggers ValueError)
    with pytest.raises(ValueError, match="Invalid state: expected a tuple of size 1 containing an index list"):
        pickle.loads(make_bad_pickle(([], 42)))

    # Tuple with wrong type inside (triggers ValueError)
    with pytest.raises(ValueError, match="Invalid state: expected an index list"):
        pickle.loads(make_bad_pickle(("not a list",)))

    # Tuple with wrong element type in list (triggers ValueError)
    bad_state: tuple[Any, ...] = ([1, 2, "bad"],)
    with pytest.raises(ValueError, match="Invalid state: expected an index list"):
        pickle.loads(make_bad_pickle(bad_state))
