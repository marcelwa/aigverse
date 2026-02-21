from __future__ import annotations

from aigverse.networks import NamedAig


def test_named_aig() -> None:
    aig = NamedAig()

    # Check that NamedAig has the specific naming methods
    assert hasattr(aig, "set_network_name")
    assert hasattr(aig, "get_network_name")
    assert hasattr(aig, "has_name")
    assert hasattr(aig, "set_name")
    assert hasattr(aig, "get_name")
    assert hasattr(aig, "has_output_name")
    assert hasattr(aig, "set_output_name")
    assert hasattr(aig, "get_output_name")

    # Test network name
    aig.set_network_name("test_circuit")
    assert aig.get_network_name() == "test_circuit"

    # Create primary inputs with names
    x1 = aig.create_pi("input1")
    x2 = aig.create_pi("input2")
    x3 = aig.create_pi("input3")

    # Test that inputs have names
    assert aig.has_name(x1)
    assert aig.has_name(x2)
    assert aig.has_name(x3)
    assert aig.get_name(x1) == "input1"
    assert aig.get_name(x2) == "input2"
    assert aig.get_name(x3) == "input3"

    # Create gates
    n4 = aig.create_and(~x1, x2)
    n5 = aig.create_and(x1, n4)
    n6 = aig.create_and(x3, n5)

    # Test setting names on internal signals
    aig.set_name(n4, "and_gate1")
    aig.set_name(n5, "and_gate2")
    assert aig.has_name(n4)
    assert aig.has_name(n5)
    assert aig.get_name(n4) == "and_gate1"
    assert aig.get_name(n5) == "and_gate2"

    # Create primary outputs with names
    po1_idx = aig.create_po(n6, "output1")
    po2_idx = aig.create_po(n5, "output2")

    # Test output names
    assert aig.has_output_name(po1_idx)
    assert aig.has_output_name(po2_idx)
    assert aig.get_output_name(po1_idx) == "output1"
    assert aig.get_output_name(po2_idx) == "output2"

    # Test setting output names after creation
    aig.set_output_name(po1_idx, "renamed_output1")
    assert aig.get_output_name(po1_idx) == "renamed_output1"


def test_named_aig_without_names() -> None:
    """Test that NamedAig still works when names are not provided."""
    aig = NamedAig()

    # Create inputs without names (using default empty string)
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    # Create gate
    n3 = aig.create_and(x1, x2)

    # Create output without name
    aig.create_po(n3)

    # Basic functionality should still work
    assert aig.num_pis() == 2
    assert aig.num_pos() == 1
    assert aig.num_gates() == 1


def test_named_aig_copy_constructor() -> None:
    """Test that NamedAig copy constructor preserves names."""
    aig1 = NamedAig()
    aig1.set_network_name("original")

    x1 = aig1.create_pi("a")
    x2 = aig1.create_pi("b")
    n3 = aig1.create_and(x1, x2)
    aig1.set_name(n3, "and_gate")
    aig1.create_po(n3, "out")

    # Copy constructor
    aig2 = NamedAig(aig1)

    # Check that names are preserved
    assert aig2.get_network_name() == "original"
    assert aig2.num_pis() == 2
    assert aig2.num_pos() == 1

    # Get the signals in the new AIG
    x1_copy = aig2.make_signal(aig2.pi_at(0))
    x2_copy = aig2.make_signal(aig2.pi_at(1))

    assert aig2.has_name(x1_copy)
    assert aig2.has_name(x2_copy)
    assert aig2.get_name(x1_copy) == "a"
    assert aig2.get_name(x2_copy) == "b"
    assert aig2.has_output_name(0)
    assert aig2.get_output_name(0) == "out"


def test_named_aig_complex_circuit() -> None:
    """Test a more complex circuit with multiple levels and names."""
    aig = NamedAig()
    aig.set_network_name("full_adder")

    # Create inputs
    a = aig.create_pi("a")
    b = aig.create_pi("b")
    cin = aig.create_pi("cin")

    # Build full adder logic
    # with sum = a ^ b ^ cin
    # and  cout = (a & b) | (cin & (a ^ b))

    a_xor_b = aig.create_xor(a, b)
    aig.set_name(a_xor_b, "a_xor_b")

    sum_out = aig.create_xor(a_xor_b, cin)
    aig.set_name(sum_out, "sum")

    a_and_b = aig.create_and(a, b)
    aig.set_name(a_and_b, "a_and_b")

    cin_and_xor = aig.create_and(cin, a_xor_b)
    aig.set_name(cin_and_xor, "cin_and_xor")

    cout = aig.create_or(a_and_b, cin_and_xor)
    aig.set_name(cout, "cout")

    # Create outputs
    sum_idx = aig.create_po(sum_out, "sum")
    cout_idx = aig.create_po(cout, "carry_out")

    # Verify structure
    assert aig.num_pis() == 3
    assert aig.num_pos() == 2
    assert aig.get_network_name() == "full_adder"

    # Verify all names
    assert aig.get_name(a) == "a"
    assert aig.get_name(b) == "b"
    assert aig.get_name(cin) == "cin"
    assert aig.get_name(a_xor_b) == "a_xor_b"
    assert aig.get_name(sum_out) == "sum"
    assert aig.get_name(a_and_b) == "a_and_b"
    assert aig.get_name(cin_and_xor) == "cin_and_xor"
    assert aig.get_name(cout) == "cout"
    assert aig.get_output_name(sum_idx) == "sum"
    assert aig.get_output_name(cout_idx) == "carry_out"
