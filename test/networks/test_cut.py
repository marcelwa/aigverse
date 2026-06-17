from __future__ import annotations

import copy

from aigverse.networks import Aig, Cut


def test_cut() -> None:
    """Test Cut creation and basic properties."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    # Create a cut view
    leaves = [x1, x2]
    root = f1
    cut = Cut(aig, leaves, root)

    # Check basic properties
    assert hasattr(cut, "size")
    assert hasattr(cut, "num_gates")
    assert hasattr(cut, "num_pis")
    assert hasattr(cut, "num_pos")

    # The cut should have 2 leaves (PIs) and 1 gate
    assert cut.num_pis == 2
    assert cut.num_pos == 1
    assert cut.num_gates == 1


def test_cut_with_signals() -> None:
    """Test Cut creation using signals."""
    aig = Aig()
    a = aig.create_pi()
    b = aig.create_pi()
    c = aig.create_pi()
    d = aig.create_pi()

    f1 = aig.create_and(a, b)
    f2 = aig.create_and(c, d)
    f3 = aig.create_xor(f1, f2)
    aig.create_po(f3)

    # Create a cut view with all PIs as leaves
    leaves = [a, b, c, d]
    root = f3
    cut = Cut(aig, leaves, root)

    # Should contain all 4 PIs as leaves
    assert cut.num_pis == 4
    assert cut.num_gates == 5


def test_cut_iteration() -> None:
    """Test iteration over nodes in Cut."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    # Create cut for the output
    leaves = [x1, x2]
    root = f1
    cut = Cut(aig, leaves, root)

    # Iterate over all nodes
    nodes = cut.nodes()
    assert len(nodes) == cut.size
    assert 0 in nodes  # constant node

    # Iterate over PIs
    pis = cut.pis()
    assert len(pis) == cut.num_pis

    # Iterate over gates
    gates = cut.gates()
    assert len(gates) == cut.num_gates

    # Iterate over POs
    pos = cut.pos()
    assert len(pos) == 1


def test_cut_index_mapping() -> None:
    """Test node to index and index to node mapping in Cut."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    cut = Cut(aig, [x1, x2], f1)

    # Test node_to_index and index_to_node
    for node in cut.nodes():
        index = cut.node_to_index(node)
        recovered_node = cut.index_to_node(index)
        assert recovered_node == node


def test_cut_is_pi() -> None:
    """Test is_pi method in Cut."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    cut = Cut(aig, [x1, x2], f1)

    # Check that leaf nodes are PIs in the cut
    assert cut.is_pi(aig.get_node(x1))
    assert cut.is_pi(aig.get_node(x2))

    # Check that gate node is not a PI
    assert not cut.is_pi(aig.get_node(f1))


def test_cut_repr() -> None:
    """Test __repr__ method in Cut."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    cut = Cut(aig, [x1, x2], f1)
    repr_str = repr(cut)
    assert "Cut" in repr_str
    assert "leaves=2" in repr_str
    assert "gates=1" in repr_str


def test_cut_clone_and_copy() -> None:
    """Test clone, __copy__, and __deepcopy__ in Cut."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    cut = Cut(aig, [x1, x2], f1)

    cloned = cut.clone()
    shallow = copy.copy(cut)
    deep = copy.deepcopy(cut)
    for candidate in (cloned, shallow, deep):
        assert isinstance(candidate, Cut)
        assert candidate.num_pis == 2
        assert candidate.num_pos == 1
        assert candidate.num_gates == 1


def test_cut_with_nodes() -> None:
    """Test Cut creation using nodes instead of signals."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    leaves = [aig.get_node(x1), aig.get_node(x2)]
    root = f1
    cut = Cut(aig, leaves, root)
    assert cut.num_pis == 2
    assert cut.num_pos == 1
    assert cut.num_gates == 1
    assert cut.size == 4
