from aigverse import Aig, DepthAig, TruthTable, simulate, simulate_nodes


def test_empty_aig() -> None:
    aig = Aig()

    tt = simulate(aig)

    assert len(tt) == 0

    n_map = simulate_nodes(aig)

    assert len(n_map) == 1
    assert n_map[0].is_const0()


def test_const0_aig() -> None:
    aig = Aig()

    aig.create_po(aig.make_signal(0))

    sim = simulate(aig)

    assert len(sim) == 1
    assert sim[0].is_const0()

    n_map = simulate_nodes(aig)

    assert len(n_map) == 1
    assert n_map[0].is_const0()


def test_const1_aig() -> None:
    aig = Aig()

    aig.create_po(~aig.make_signal(0))

    sim = simulate(aig)

    assert len(sim) == 1
    assert sim[0].is_const1()

    n_map = simulate_nodes(aig)

    assert len(n_map) == 1
    assert n_map[0].is_const0()  # node tt is still const0


def test_and_aig() -> None:
    aig = Aig()

    a = aig.create_pi()
    b = aig.create_pi()

    and1 = aig.create_and(a, b)

    aig.create_po(and1)

    sim = simulate(aig)

    conjunction = TruthTable(2)
    conjunction.create_from_binary_string("1000")

    assert len(sim) == 1
    assert sim[0] == conjunction

    n_map = simulate_nodes(aig)

    id_tt_a = TruthTable(2)
    id_tt_a.create_from_binary_string("1010")
    id_tt_b = TruthTable(2)
    id_tt_b.create_from_binary_string("1100")

    assert len(n_map) == 4
    assert n_map[0].is_const0()
    assert n_map[1] == id_tt_a
    assert n_map[2] == id_tt_b
    assert n_map[3] == conjunction


def test_or_aig() -> None:
    aig = Aig()

    a = aig.create_pi()
    b = aig.create_pi()

    or1 = aig.create_or(a, b)

    aig.create_po(or1)

    sim = simulate(aig)

    disjunction = TruthTable(2)
    disjunction.create_from_binary_string("1110")

    assert len(sim) == 1
    assert sim[0] == disjunction

    n_map = simulate_nodes(aig)

    id_tt_a = TruthTable(2)
    id_tt_a.create_nth_var(0)
    id_tt_b = TruthTable(2)
    id_tt_b.create_nth_var(1)

    assert len(n_map) == 4
    assert n_map[0].is_const0()
    assert n_map[1] == id_tt_a
    assert n_map[2] == id_tt_b
    # we're expecting a disjunction at the PO but the last node is a negated disjunction (NAND)
    # because the PO's inverted signal is not taken into account in the node simulation
    assert n_map[3] == ~disjunction


def test_maj_aig() -> None:
    aig = Aig()

    a = aig.create_pi()
    b = aig.create_pi()
    c = aig.create_pi()

    maj1 = aig.create_maj(a, b, c)

    aig.create_po(maj1)

    sim = simulate(aig)

    majority = TruthTable(3)
    majority.create_majority()

    print(f"MAJ: {majority.to_binary()}")

    assert len(sim) == 1
    assert sim[0] == majority

    n_map = simulate_nodes(aig)

    id_tt_a = TruthTable(3)
    id_tt_a.create_from_binary_string("10101010")
    id_tt_b = TruthTable(3)
    id_tt_b.create_from_binary_string("11001100")
    id_tt_c = TruthTable(3)
    id_tt_c.create_from_binary_string("11110000")

    for i in range(len(n_map)):
        print(f"Node {i}: {n_map[i].to_binary()}")

    assert len(n_map) == 8
    assert n_map[0].is_const0()
    assert n_map[1] == id_tt_a
    assert n_map[2] == id_tt_b
    assert n_map[3] == id_tt_c
    # we're expecting a negated MAJ at the node because the PO's inverted signal is not taken into account
    assert n_map[7] == ~majority


def test_multi_output_aig() -> None:
    # also test DepthAig
    for ntk in [Aig, DepthAig]:
        aig = ntk()

        a = aig.create_pi()
        b = aig.create_pi()

        and1 = aig.create_and(a, b)
        or1 = aig.create_or(a, b)

        aig.create_po(and1)
        aig.create_po(or1)

        sim = simulate(aig)

        conjunction = TruthTable(2)
        conjunction.create_from_binary_string("1000")

        disjunction = TruthTable(2)
        disjunction.create_from_binary_string("1110")

        assert len(sim) == 2
        assert sim[0] == conjunction
        assert sim[1] == disjunction
