from __future__ import annotations

from aigverse import Aig, AigSignal, DepthAig, FanoutAig, SequentialAig, equivalence_checking


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


def test_depth_aig() -> None:
    aig = DepthAig()

    assert hasattr(aig, "num_levels")
    assert hasattr(aig, "level")
    assert hasattr(aig, "is_on_critical_path")
    assert hasattr(aig, "update_levels")
    assert hasattr(aig, "create_po")

    # Create primary inputs
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()

    assert aig.num_levels() == 0

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

    # Check the depth of the AIG
    assert aig.num_levels() == 4

    assert aig.level(aig.get_node(x1)) == 0
    assert aig.level(aig.get_node(x2)) == 0
    assert aig.level(aig.get_node(x3)) == 0
    assert aig.level(aig.get_node(n4)) == 1
    assert aig.level(aig.get_node(n5)) == 2
    assert aig.level(aig.get_node(n6)) == 3
    assert aig.level(aig.get_node(n7)) == 2
    assert aig.level(aig.get_node(n8)) == 3
    assert aig.level(aig.get_node(n9)) == 4

    # Copy constructor
    aig2 = DepthAig(aig)

    assert aig2.num_levels() == 4


def test_fanout_aig() -> None:
    aig = FanoutAig()

    assert hasattr(aig, "update_fanout")
    assert hasattr(aig, "fanout")
    assert hasattr(aig, "substitute_node")
    assert hasattr(aig, "substitute_node_no_restrash")

    # Create primary inputs
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()

    # Create AND gates
    n4 = aig.create_and(x1, x2)
    n5 = aig.create_and(n4, x3)
    n6 = aig.create_and(n4, n5)
    # Create primary outputs
    aig.create_po(n6)
    aig_comp = FanoutAig(aig.clone())
    # Check the fanout of n4
    fanout_list = aig.fanout(aig.get_node(n4))
    assert len(fanout_list) == 2
    assert (fanout_list[0] == aig.get_node(n6)) & (fanout_list[1] == aig.get_node(n5)) | (
        fanout_list[0] == aig.get_node(n5)
    ) & (fanout_list[1] == aig.get_node(n6))

    assert aig.num_gates() == 3
    aig.substitute_node(aig.get_node(n5), n6)
    assert aig.num_gates() == 2

    # Resub with complemented value and without strash
    aig_comp.substitute_node_no_restrash(aig_comp.get_node(n6), aig_comp.create_not(n6))
    # Everything remains the same
    assert aig_comp.num_gates() == 3
    fanout_list_comp = aig_comp.fanout(aig_comp.get_node(n4))
    assert len(fanout_list_comp) == 2


def test_sequential_aig_initialization() -> None:
    """Test basic initialization and properties of SequentialAig."""
    saig = SequentialAig()
    assert saig.size() == 1
    assert saig.num_gates() == 0
    assert saig.num_pis() == 0
    assert saig.num_pos() == 0
    assert saig.num_registers() == 0
    assert saig.num_cis() == 0
    assert saig.num_cos() == 0
    assert saig.is_combinational()


def test_create_and_use_register_in_aig() -> None:
    """Test creating and using a register in an AIG.

    Raises:
        AssertionError: If the expected properties do not match.
    """
    # Create a sequential AIG
    saig = SequentialAig()

    # Create primary inputs
    x1 = saig.create_pi()
    x2 = saig.create_pi()
    x3 = saig.create_pi()

    # Check initial network properties
    assert saig.size() == 4
    assert saig.num_registers() == 0
    assert saig.num_pis() == 3
    assert saig.num_pos() == 0

    # Create gates and outputs
    f1 = saig.create_and(x1, x2)
    saig.create_po(f1)
    saig.create_po(~f1)

    # Create a register input
    f2 = saig.create_and(f1, x3)
    saig.create_ri(f2)

    # Create a register output and connect to PO
    ro = saig.create_ro()
    saig.create_po(ro)

    # Check final network properties
    assert saig.num_pos() == 3
    assert saig.num_registers() == 1

    # Check each primary output
    assert saig.po_at(0) == f1
    assert saig.po_at(1) == ~f1

    for i, s in enumerate(saig.pos()):
        if i == 0:
            assert s == f1
        elif i == 1:
            assert s == ~f1
        elif i == 2:
            assert f2.get_data() == saig.po_at(i).get_data()
        else:
            raise AssertionError


def test_sequential_aig_ci_co_nodes() -> None:
    """Test combinational interface (CI) and combinational output (CO) nodes."""
    saig = SequentialAig()

    # Create primary inputs and register outputs
    pi1 = saig.create_pi()
    pi2 = saig.create_pi()
    ro1 = saig.create_ro()

    # Both PIs and ROs are CIs
    assert saig.is_ci(saig.get_node(pi1))
    assert saig.is_ci(saig.get_node(pi2))
    assert saig.is_ci(saig.get_node(ro1))

    # Only ROs are ROs
    assert not saig.is_ro(saig.get_node(pi1))
    assert not saig.is_ro(saig.get_node(pi2))
    assert saig.is_ro(saig.get_node(ro1))

    # Create primary outputs and register inputs
    saig.create_po(pi1)
    saig.create_ri(pi2)

    # Check CI and CO counts
    assert saig.num_cis() == 3  # 2 PIs + 1 RO
    assert saig.num_cos() == 2  # 1 PO + 1 RI


def test_sequential_aig_combinational_check() -> None:
    """Test checking if a sequential AIG is combinational."""
    saig = SequentialAig()

    # Initially it's combinational (no registers)
    assert saig.is_combinational()

    # Add a register, making it sequential
    saig.create_ro()
    assert not saig.is_combinational()

    # Create a new sequential AIG
    saig2 = SequentialAig()

    # Only add PIs and POs (still combinational)
    pi = saig2.create_pi()
    saig2.create_po(pi)
    assert saig2.is_combinational()


def test_sequential_aig_register_operations():
    """Test register operations in a sequential AIG."""
    saig = SequentialAig()

    # Create a register
    ro1 = saig.create_ro()
    pi1 = saig.create_pi()
    f1 = saig.create_and(ro1, pi1)
    saig.create_ri(f1)

    # Create another register
    ro2 = saig.create_ro()
    pi2 = saig.create_pi()
    f2 = saig.create_and(ro2, pi2)
    saig.create_ri(f2)

    # Test register_at (should return default empty register)
    reg = saig.register_at(0)
    assert not reg.control
    assert reg.init == 3
    assert not reg.type

    # Test set_register
    new_reg = saig.register_at(0)
    new_reg.control = "clock"
    new_reg.init = 0
    new_reg.type = "rising_edge"
    saig.set_register(0, new_reg)

    # Verify register was set properly
    updated_reg = saig.register_at(0)
    assert updated_reg.control == "clock"
    assert updated_reg.init == 0
    assert updated_reg.type == "rising_edge"

    # Make sure the second register is unaffected
    reg2 = saig.register_at(1)
    assert not reg2.control
    assert reg2.init == 3
    assert not reg2.type


def test_sequential_aig_index_methods():
    """Test index methods in a sequential AIG."""
    saig = SequentialAig()

    # Create primary inputs
    pi1 = saig.create_pi()
    pi2 = saig.create_pi()

    # Create register outputs
    ro1 = saig.create_ro()
    ro2 = saig.create_ro()

    # Create some gates
    f1 = saig.create_and(pi1, ro1)
    f2 = saig.create_and(pi2, ro2)

    # Create primary outputs and register inputs
    saig.create_po(f1)
    saig.create_po(f2)
    saig.create_ri(f1)
    saig.create_ri(f2)

    # Test pi_index
    assert saig.pi_index(saig.get_node(pi1)) == 0
    assert saig.pi_index(saig.get_node(pi2)) == 1

    # Test ci_index (includes PIs and ROs)
    assert saig.ci_index(saig.get_node(pi1)) == 0
    assert saig.ci_index(saig.get_node(pi2)) == 1
    assert saig.ci_index(saig.get_node(ro1)) == 2
    assert saig.ci_index(saig.get_node(ro2)) == 3

    # Test ro_index
    assert saig.ro_index(saig.get_node(ro1)) == 0
    assert saig.ro_index(saig.get_node(ro2)) == 1

    # Test co_index and ri_index
    assert saig.co_index(f1) == 0  # First PO
    assert saig.co_index(f2) == 1  # Second PO
    assert saig.ri_index(f1) == 0  # First RI
    assert saig.ri_index(f2) == 1  # Second RI


def test_sequential_aig_ro_ri_conversion():
    """Test conversion between register outputs and register inputs."""
    saig = SequentialAig()

    # Create a simple circuit with a register
    pi = saig.create_pi()
    ro = saig.create_ro()
    f = saig.create_and(pi, ro)
    saig.create_ri(f)

    # Test ro_to_ri
    ri_signal = saig.ro_to_ri(ro)
    assert ri_signal == f

    # Test ri_to_ro
    ro_node = saig.ri_to_ro(f)
    assert ro_node == saig.get_node(ro)


def test_sequential_aig_ro_at_ri_at():
    """Test accessing register outputs and inputs by index."""
    saig = SequentialAig()

    # Create primary inputs
    pi1 = saig.create_pi()
    pi2 = saig.create_pi()

    # Create register outputs
    ro1 = saig.create_ro()
    ro2 = saig.create_ro()

    # Create register inputs
    f1 = saig.create_and(pi1, ro1)
    f2 = saig.create_and(pi2, ro2)
    saig.create_ri(f1)
    saig.create_ri(f2)

    # Test ro_at and ri_at
    assert saig.ro_at(0) == saig.get_node(ro1)
    assert saig.ro_at(1) == saig.get_node(ro2)
    assert saig.ri_at(0) == f1
    assert saig.ri_at(1) == f2


def test_sequential_aig_iteration():
    """Test iteration methods in a sequential AIG."""
    saig = SequentialAig()

    # Create primary inputs
    pi1 = saig.create_pi()
    pi2 = saig.create_pi()

    # Create register outputs
    ro1 = saig.create_ro()
    ro2 = saig.create_ro()

    # Create some gates
    f1 = saig.create_and(pi1, ro1)
    f2 = saig.create_and(pi2, ro2)

    # Create primary outputs and register inputs
    saig.create_po(f1)
    saig.create_po(f2)
    saig.create_ri(f1)
    saig.create_ri(f2)

    # Test CI iteration
    cis = saig.cis()
    assert len(cis) == 4  # 2 PIs + 2 ROs
    assert saig.get_node(pi1) in cis
    assert saig.get_node(pi2) in cis
    assert saig.get_node(ro1) in cis
    assert saig.get_node(ro2) in cis

    # Test CO iteration
    cos = saig.cos()
    assert len(cos) == 4  # 2 POs + 2 RIs
    assert f1 in cos
    assert f2 in cos

    # Test RO iteration
    ros = saig.ros()
    assert len(ros) == 2
    assert saig.get_node(ro1) in ros
    assert saig.get_node(ro2) in ros

    # Test RI iteration
    ris = saig.ris()
    assert len(ris) == 2
    assert f1 in ris
    assert f2 in ris

    # Test registers iteration
    registers = saig.registers()
    assert len(registers) == 2

    # The register pairs are (ri, ro_node) where ro_node is the actual node ID
    # of the register output
    register_dict = dict(registers)
    assert f1 in register_dict
    assert f2 in register_dict

    # Check that register values match correctly
    assert register_dict[f1] == saig.get_node(ro1)  # First register maps to ro1 node
    assert register_dict[f2] == saig.get_node(ro2)  # Second register maps to ro2 node

    # Alternative way to verify the relationship between ri and ro
    assert saig.ri_to_ro(f1) == saig.get_node(ro1)
    assert saig.ri_to_ro(f2) == saig.get_node(ro2)
