import pytest

from aigverse import Aig, AigEdge, AigEdgeList, to_edge_list


def test_aig_edge():
    null_edge = AigEdge()

    assert type(null_edge) is AigEdge

    assert null_edge.source == 0
    assert null_edge.target == 0
    assert null_edge.weight == 0

    assert null_edge == AigEdge(0, 0, 0)
    assert null_edge != AigEdge(1, 0, 0)
    assert null_edge != AigEdge(1, 1, 0)
    assert null_edge != AigEdge(1, 1, 1)

    assert (repr(null_edge)) == "Edge(s:0,t:0,w:0)"

    edge = AigEdge(1, 2, 3)

    assert type(edge) is AigEdge

    assert edge.source == 1
    assert edge.target == 2
    assert edge.weight == 3

    assert edge == AigEdge(1, 2, 3)
    assert edge != AigEdge(1, 2, 4)
    assert edge != AigEdge(1, 3, 3)
    assert edge != AigEdge(2, 2, 3)

    assert (repr(edge)) == "Edge(s:1,t:2,w:3)"


def test_aig_edge_list():
    edge_list = AigEdgeList(Aig())

    assert type(edge_list) is AigEdgeList

    assert len(edge_list) == 0

    edge_list.append(AigEdge(1, 2, 3))
    edge_list.append(AigEdge(2, 3, 4))
    edge_list.append(AigEdge(3, 4, 5))

    assert len(edge_list) == 3

    assert edge_list[0] == AigEdge(1, 2, 3)
    assert edge_list[1] == AigEdge(2, 3, 4)
    assert edge_list[2] == AigEdge(3, 4, 5)

    edge_list[0] = AigEdge(4, 5, 6)
    edge_list[1] = AigEdge(5, 6, 7)
    edge_list[2] = AigEdge(6, 7, 8)

    assert edge_list[0] == AigEdge(4, 5, 6)
    assert edge_list[1] == AigEdge(5, 6, 7)
    assert edge_list[2] == AigEdge(6, 7, 8)

    with pytest.raises(IndexError):
        edge_list[3]

    with pytest.raises(IndexError):
        edge_list[3] = AigEdge(7, 8, 9)

    assert (repr(edge_list)) == "EdgeList([Edge(s:4,t:5,w:6), Edge(s:5,t:6,w:7), Edge(s:6,t:7,w:8)])"

    edge_list.clear()

    assert len(edge_list) == 0

    assert (repr(edge_list)) == "EdgeList([])"


def test_minimal_aig_to_edge_list():
    aig = Aig()

    x1 = aig.create_pi()  # 1
    x2 = aig.create_pi()  # 2
    aig.create_po(x1)
    aig.create_po(~x2)

    edge_list = to_edge_list(aig)

    assert type(edge_list) is AigEdgeList
    assert len(edge_list) == 0  # No edges since there are no AND gates


def test_constant_aig_to_edge_list():
    # AIG with all inverted inputs
    aig = Aig()

    x0 = aig.create_pi()  # 1
    x1 = aig.create_pi()  # 2
    n0 = aig.create_and(~x0, ~x1)  # 3
    aig.create_po(n0)

    # custom weights
    edge_list = to_edge_list(aig, regular_weight=5, inverted_weight=-5)

    assert type(edge_list) is AigEdgeList
    assert len(edge_list) == 2
    assert AigEdge(1, 3, -5) in edge_list  # ~x0 to AND gate
    assert AigEdge(2, 3, -5) in edge_list  # ~x1 to AND gate


def test_simple_aig_to_edge_list():
    aig = Aig()

    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()

    y1 = aig.create_and(x1, ~x2)
    y2 = aig.create_and(x2, x3)
    y3 = aig.create_and(~y1, y2)

    aig.create_po(y3)

    # default weights
    edge_list = to_edge_list(aig)

    assert type(edge_list) is AigEdgeList

    assert len(edge_list) == 6

    assert AigEdge(1, 4, 0) in edge_list
    assert AigEdge(2, 5, 0) in edge_list
    assert AigEdge(2, 4, 1) in edge_list
    assert AigEdge(3, 5, 0) in edge_list
    assert AigEdge(4, 6, 1) in edge_list
    assert AigEdge(5, 6, 0) in edge_list


def test_constant_node_aig_to_edge_list():
    aig = Aig()

    x0 = aig.create_pi()  # 1
    x1 = aig.create_pi()  # 2
    n0 = aig.create_and(x0, x1)  # 3
    aig.create_po(x0)  # Direct PO from PI
    aig.create_po(n0)

    # custom weights
    edge_list = to_edge_list(aig, regular_weight=7, inverted_weight=-7)

    assert type(edge_list) is AigEdgeList
    assert len(edge_list) == 2
    assert AigEdge(1, 3, 7) in edge_list  # x0 to AND gate
    assert AigEdge(2, 3, 7) in edge_list  # x1 to AND gate


def test_medium_aig_to_edge_list():
    aig = Aig()

    x0 = aig.create_pi()  # 1
    x1 = aig.create_pi()  # 2
    x2 = aig.create_pi()  # 3
    x3 = aig.create_pi()  # 4
    n0 = aig.create_and(~x2, x3)  # 5
    n1 = aig.create_and(~x2, n0)  # 6
    n2 = aig.create_and(x3, ~n1)  # 7
    n3 = aig.create_and(x0, ~x1)  # 8
    n4 = aig.create_and(~n2, n3)  # 9
    n5 = aig.create_and(x1, ~n2)  # 10
    n6 = aig.create_and(~n4, ~n5)  # 11
    n7 = aig.create_and(n1, n3)  # 12
    aig.create_po(n6)
    aig.create_po(n7)

    # custom weights
    edge_list = to_edge_list(aig, regular_weight=10, inverted_weight=-10)

    assert type(edge_list) is AigEdgeList

    assert len(edge_list) == 16

    assert AigEdge(3, 5, -10) in edge_list
    assert AigEdge(4, 5, 10) in edge_list
    assert AigEdge(3, 6, -10) in edge_list
    assert AigEdge(5, 6, 10) in edge_list
    assert AigEdge(4, 7, 10) in edge_list
    assert AigEdge(6, 7, -10) in edge_list
    assert AigEdge(1, 8, 10) in edge_list
    assert AigEdge(2, 8, -10) in edge_list
    assert AigEdge(7, 9, -10) in edge_list
    assert AigEdge(8, 9, 10) in edge_list
    assert AigEdge(2, 10, 10) in edge_list
    assert AigEdge(7, 10, -10) in edge_list
    assert AigEdge(9, 11, -10) in edge_list
    assert AigEdge(10, 11, -10) in edge_list
    assert AigEdge(6, 12, 10) in edge_list
    assert AigEdge(8, 12, 10) in edge_list
