from __future__ import annotations

import copy

from aigverse.networks import Aig, CutAig


def test_cut_aig() -> None:
    """Test CutAig creation and basic properties."""
    # Create a sample AIG
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    # Create a cut view
    leaves = [x1, x2]
    root = f1
    cut_aig = CutAig(aig, leaves, root)

    # Check basic properties
    assert hasattr(cut_aig, "size")
    assert hasattr(cut_aig, "num_gates")
    assert hasattr(cut_aig, "num_pis")
    assert hasattr(cut_aig, "num_pos")

    # The cut should have 2 leaves (PIs) and 1 gate
    assert cut_aig.num_pis == 2
    assert cut_aig.num_pos == 1
    assert cut_aig.num_gates == 1
    assert cut_aig.size == 4  # constant + 2 PIs + 1 gate


def test_cut_aig_with_signals() -> None:
    """Test CutAig creation using signals instead of nodes."""
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
    cut_aig = CutAig(aig, leaves, root)

    # Should contain all 4 PIs as leaves
    assert cut_aig.num_pis == 4
    assert cut_aig.num_pos == 1
    # Should have the XOR gate (decomposed to AND gates internally)
    assert cut_aig.num_gates == 5


def test_cut_aig_iteration() -> None:
    """Test iteration over nodes in CutAig."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    # Create cut for the output
    leaves = [x1, x2]
    root = f1
    cut_aig = CutAig(aig, leaves, root)

    # Iterate over all nodes
    nodes = list(cut_aig.nodes())
    assert len(nodes) == cut_aig.size
    assert 0 in nodes  # constant node

    # Iterate over PIs
    pis = list(cut_aig.pis())
    assert len(pis) == cut_aig.num_pis

    # Iterate over gates
    gates = list(cut_aig.gates())
    assert len(gates) == cut_aig.num_gates

    # Iterate over POs
    pos = list(cut_aig.pos())
    assert len(pos) == 1


def test_cut_aig_index_mapping() -> None:
    """Test node to index and index to node mapping in CutAig."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    cut_aig = CutAig(aig, [x1, x2], f1)

    # Test node_to_index and index_to_node
    for node in cut_aig.nodes():
        index = cut_aig.node_to_index(node)
        recovered_node = cut_aig.index_to_node(index)
        assert recovered_node == node


def test_cut_aig_is_pi() -> None:
    """Test is_pi method in CutAig."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    cut_aig = CutAig(aig, [x1, x2], f1)

    # Check that leaf nodes are PIs in the cut
    assert cut_aig.is_pi(aig.get_node(x1))
    assert cut_aig.is_pi(aig.get_node(x2))

    # Check that gate node is not a PI
    assert not cut_aig.is_pi(aig.get_node(f1))


def test_cut_aig_repr() -> None:
    """Test __repr__ method in CutAig."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    cut_aig = CutAig(aig, [x1, x2], f1)

    repr_str = repr(cut_aig)
    assert "CutAig" in repr_str
    assert "leaves=2" in repr_str
    assert "gates=1" in repr_str


def test_cut_aig_clone_and_copy() -> None:
    """Test clone, __copy__, and __deepcopy__ in CutAig."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    cut_aig = CutAig(aig, [x1, x2], f1)

    cloned = cut_aig.clone()
    shallow = copy.copy(cut_aig)
    deep = copy.deepcopy(cut_aig)

    for candidate in (cloned, shallow, deep):
        assert isinstance(candidate, CutAig)
        assert candidate.num_pis == 2
        assert candidate.num_pos == 1
        assert candidate.num_gates == 1
