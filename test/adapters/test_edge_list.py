from __future__ import annotations

import pytest

from aigverse import Aig, AigEdge, AigEdgeList, SequentialAig, to_edge_list


def test_aig_edge() -> None:
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


def test_aig_edge_list() -> None:
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


def test_minimal_aig_to_edge_list() -> None:
    aig = Aig()

    aig.create_pi()  # 1
    aig.create_pi()  # 2

    edge_list = to_edge_list(aig)

    assert type(edge_list) is AigEdgeList
    assert len(edge_list) == 0  # No edges since there are no AND gates or POs


def test_no_and_aig_to_edge_list() -> None:
    aig = Aig()

    x1 = aig.create_pi()  # 1
    x2 = aig.create_pi()  # 2
    aig.create_po(x1)  # 3
    aig.create_po(~x2)  # 4

    edge_list = to_edge_list(aig)

    assert type(edge_list) is AigEdgeList
    assert len(edge_list) == 2
    assert AigEdge(1, 3, 0) in edge_list  # x1 to PO
    assert AigEdge(2, 4, 1) in edge_list  # ~x2 to PO


def test_constant_aig_to_edge_list() -> None:
    # AIG with all inverted inputs
    aig = Aig()

    x0 = aig.create_pi()  # 1
    x1 = aig.create_pi()  # 2
    n0 = aig.create_and(~x0, ~x1)  # 3
    aig.create_po(n0)  # 4

    # custom weights
    edge_list = to_edge_list(aig, regular_weight=5, inverted_weight=-5)

    assert type(edge_list) is AigEdgeList
    assert len(edge_list) == 3
    assert AigEdge(1, 3, -5) in edge_list  # ~x0 to AND gate
    assert AigEdge(2, 3, -5) in edge_list  # ~x1 to AND gate
    assert AigEdge(3, 4, 5) in edge_list  # AND gate to PO


def test_simple_aig_to_edge_list() -> None:
    aig = Aig()

    x1 = aig.create_pi()  # 1
    x2 = aig.create_pi()  # 2
    x3 = aig.create_pi()  # 3

    y1 = aig.create_and(x1, ~x2)  # 4
    y2 = aig.create_and(x2, x3)  # 5
    y3 = aig.create_and(~y1, y2)  # 6

    aig.create_po(y3)  # 7

    # default weights
    edge_list = to_edge_list(aig)

    assert type(edge_list) is AigEdgeList

    assert len(edge_list) == 7

    assert AigEdge(1, 4, 0) in edge_list
    assert AigEdge(2, 5, 0) in edge_list
    assert AigEdge(2, 4, 1) in edge_list
    assert AigEdge(3, 5, 0) in edge_list
    assert AigEdge(4, 6, 1) in edge_list
    assert AigEdge(5, 6, 0) in edge_list
    assert AigEdge(6, 7, 0) in edge_list


def test_constant_node_aig_to_edge_list() -> None:
    aig = Aig()

    x0 = aig.create_pi()  # 1
    x1 = aig.create_pi()  # 2
    n0 = aig.create_and(x0, x1)  # 3
    aig.create_po(x0)  # 4
    aig.create_po(n0)  # 5

    # custom weights
    edge_list = to_edge_list(aig, regular_weight=7, inverted_weight=-7)

    assert type(edge_list) is AigEdgeList
    assert len(edge_list) == 4
    assert AigEdge(1, 3, 7) in edge_list  # x0 to AND gate
    assert AigEdge(2, 3, 7) in edge_list  # x1 to AND gate
    assert AigEdge(1, 4, 7) in edge_list  # AND gate to PO
    assert AigEdge(3, 5, 7) in edge_list  # AND gate to PO


def test_medium_aig_to_edge_list() -> None:
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
    aig.create_po(n6)  # 13
    aig.create_po(n7)  # 14

    # custom weights
    edge_list = to_edge_list(aig, regular_weight=10, inverted_weight=-10)

    assert type(edge_list) is AigEdgeList

    assert len(edge_list) == 18

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
    assert AigEdge(11, 13, 10) in edge_list
    assert AigEdge(12, 14, 10) in edge_list


def test_sequential_aig_to_edge_list_basic() -> None:
    """Test edge list generation with a simple sequential AIG containing one register."""
    # Create a sequential AIG
    aig = SequentialAig()

    # Create primary inputs
    x1 = aig.create_pi()  # 1
    x2 = aig.create_pi()  # 2

    # Create a register output (RO) - paired with the RI by index
    aig.create_ro()  # 3 - RO node

    # Create some combinational logic
    f1 = aig.create_and(x1, x2)  # 4

    # Create a register input (RI)
    aig.create_ri(f1)  # 5

    # Generate edge list
    edge_list = to_edge_list(aig)

    assert len(edge_list) == 3  # x1->AND, x2->AND, AND->RI

    # Check the sequential edge from RI to RO
    # The ri_to_ro function maps an RI signal to its corresponding RO node
    ro_node = aig.node_to_index(aig.ri_to_ro(f1))
    assert AigEdge(aig.node_to_index(aig.get_node(f1)), ro_node, 0) in edge_list


def test_sequential_aig_to_edge_list_multiple_registers() -> None:
    """Test edge list generation with multiple registers."""
    # Create a sequential AIG
    aig = SequentialAig()

    # Create primary inputs
    x1 = aig.create_pi()  # 1
    x2 = aig.create_pi()  # 2

    # Create register outputs (ROs) - paired with RIs by index
    ro1 = aig.create_ro()  # 3
    ro2 = aig.create_ro()  # 4

    # Create some more logic using register outputs
    f1 = aig.create_and(ro1, ro2)  # 5

    # Create combinational logic
    f2 = aig.create_and(x1, x2)  # 6
    f3 = aig.create_and(x1, ~x2)  # 7

    # Create a primary output
    aig.create_po(f3)  # 8

    # Create register inputs (RIs)
    aig.create_ri(f1)  # 9
    aig.create_ri(f2)  # 10

    print()
    print(f"cis: {aig.cis()}")
    print(f"cos: {aig.cos()}")
    print(f"ros: {aig.ros()}")
    print(f"ris: {aig.ris()}")
    print(f"registers: {aig.registers()}")
    print(f"f1: {f1}")

    # Generate edge list
    edge_list = to_edge_list(aig, regular_weight=5, inverted_weight=-5)

    # Check total number of edges
    assert len(edge_list) == 9
    print(edge_list)

    assert AigEdge(1, 6, 5) in edge_list  # x1 to AND gate
    assert AigEdge(2, 6, 5) in edge_list  # x2 to AND gate
    assert AigEdge(1, 7, 5) in edge_list  # x1 to AND gate
    assert AigEdge(2, 7, -5) in edge_list  # ~x2 to AND gate
    assert AigEdge(3, 5, 5) in edge_list  # ro1 to AND gate
    assert AigEdge(4, 5, 5) in edge_list  # ro2 to AND gate
    assert AigEdge(5, 3, 5) in edge_list  # AND gate to RI
    assert AigEdge(6, 4, 5) in edge_list  # AND gate to RI
    assert AigEdge(7, 8, 5) in edge_list  # AND gate to PO


def test_sequential_aig_feedback_loop() -> None:
    """Test edge list generation with registers forming a feedback loop."""
    # Create a sequential AIG
    saig = SequentialAig()

    # Create primary input
    x1 = saig.create_pi()  # 1

    # Create register output first (feedback loops start with RO)
    ro = saig.create_ro()  # 2

    # Create logic that uses both primary input and register output
    f1 = saig.create_and(x1, ro)  # 3

    # Create register input that feeds back to the register output
    saig.create_ri(f1)  # 4

    # Generate edge list
    edge_list = to_edge_list(saig)

    # Check for feedback loop edge (RI->RO)
    ro_node = saig.node_to_index(saig.ri_to_ro(f1))
    assert AigEdge(saig.node_to_index(saig.get_node(f1)), ro_node, 0) in edge_list

    # Check total number of edges
    assert len(edge_list) == 3  # x1->AND, RO->AND, AND->RI(->RO)
