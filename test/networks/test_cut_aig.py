from __future__ import annotations

import copy

import pytest

from aigverse.networks import Aig, CutAig


def test_cut_aig() -> None:
    """Test CutAig creation and basic properties."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    leaves = [x1, x2]
    root = f1
    cut_aig = CutAig(aig, leaves, root)

    assert hasattr(cut_aig, "size")
    assert hasattr(cut_aig, "num_gates")
    assert hasattr(cut_aig, "num_pis")
    assert hasattr(cut_aig, "num_pos")
    assert cut_aig.num_pis == 2
    assert cut_aig.num_pos == 1
    assert cut_aig.num_gates == 1


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

    leaves = [a, b, c, d]
    root = f3
    cut_aig = CutAig(aig, leaves, root)
    assert cut_aig.num_pis == 4
    assert cut_aig.num_gates == 5


def test_cut_aig_iteration() -> None:
    """Test iteration over nodes in CutAig."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    leaves = [x1, x2]
    root = f1
    cut_aig = CutAig(aig, leaves, root)
    nodes = cut_aig.nodes()
    assert len(nodes) == cut_aig.size
    assert 0 in nodes

    pis = cut_aig.pis()
    assert len(pis) == cut_aig.num_pis
    gates = cut_aig.gates()
    assert len(gates) == cut_aig.num_gates
    pos = cut_aig.pos()
    assert len(pos) == 1


def test_cut_aig_index_mapping() -> None:
    """Test node to index and index to node mapping in CutAig."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    cut_aig = CutAig(aig, [x1, x2], f1)

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
    assert cut_aig.is_pi(aig.get_node(x1))
    assert cut_aig.is_pi(aig.get_node(x2))
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


def test_cut_aig_with_nodes() -> None:
    """Test CutAig creation using nodes instead of signals."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)

    leaves = [aig.get_node(x1), aig.get_node(x2)]
    root = f1
    cut_aig = CutAig(aig, leaves, root)
    assert cut_aig.num_pis == 2
    assert cut_aig.num_pos == 1
    assert cut_aig.num_gates == 1
    assert cut_aig.size == 4


def test_cut_aig_immutability() -> None:
    """Test that network-modifying methods raise RuntimeError on CutAig."""
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    f1 = aig.create_and(x1, x2)
    aig.create_po(f1)
    cut_aig = CutAig(aig, [x1, x2], f1)
    with pytest.raises(RuntimeError, match="create_pi is not available on immutable view"):
        cut_aig.create_pi()
    with pytest.raises(RuntimeError, match="create_po is not available on immutable view"):
        cut_aig.create_po(f1)
    with pytest.raises(RuntimeError, match="create_and is not available on immutable view"):
        cut_aig.create_and(x1, x2)
    with pytest.raises(RuntimeError, match="create_or is not available on immutable view"):
        cut_aig.create_or(x1, x2)
    with pytest.raises(RuntimeError, match="create_xor is not available on immutable view"):
        cut_aig.create_xor(x1, x2)
    with pytest.raises(RuntimeError, match="create_not is not available on immutable view"):
        cut_aig.create_not(x1)
    with pytest.raises(RuntimeError, match="create_nand is not available on immutable view"):
        cut_aig.create_nand(x1, x2)
    with pytest.raises(RuntimeError, match="create_nor is not available on immutable view"):
        cut_aig.create_nor(x1, x2)
    with pytest.raises(RuntimeError, match="create_xnor is not available on immutable view"):
        cut_aig.create_xnor(x1, x2)
    with pytest.raises(RuntimeError, match="create_buf is not available on immutable view"):
        cut_aig.create_buf(x1)
    with pytest.raises(RuntimeError, match="create_maj is not available on immutable view"):
        cut_aig.create_maj(x1, x2, f1)
    with pytest.raises(RuntimeError, match="create_ite is not available on immutable view"):
        cut_aig.create_ite(x1, x2, f1)
    with pytest.raises(RuntimeError, match="create_xor3 is not available on immutable view"):
        cut_aig.create_xor3(x1, x2, f1)
    with pytest.raises(RuntimeError, match="create_lt is not available on immutable view"):
        cut_aig.create_lt(x1, x2)
    with pytest.raises(RuntimeError, match="create_le is not available on immutable view"):
        cut_aig.create_le(x1, x2)
    with pytest.raises(RuntimeError, match="clone_node is not available on immutable view"):
        cut_aig.clone_node(aig, aig.get_node(x1), [x1])
