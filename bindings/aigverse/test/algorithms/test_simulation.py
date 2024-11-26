from aigverse import Aig, DepthAig, TruthTable, simulate


def test_empty_aig():
    aig = Aig()

    sim = simulate(aig)

    assert len(sim) == 0


def test_const0_aig():
    aig = Aig()

    aig.create_po(aig.make_signal(0))

    sim = simulate(aig)

    const0 = TruthTable(0)
    const0.create_from_binary_string("0")

    assert len(sim) == 1
    assert sim[0] == const0


def test_const1_aig():
    aig = Aig()

    aig.create_po(~aig.make_signal(0))

    sim = simulate(aig)

    const1 = TruthTable(0)
    const1.create_from_binary_string("1")

    assert len(sim) == 1
    assert sim[0] == const1


def test_and_aig():
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


def test_or_aig():
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


def test_maj_aig():
    aig = Aig()

    a = aig.create_pi()
    b = aig.create_pi()
    c = aig.create_pi()

    maj1 = aig.create_maj(a, b, c)

    aig.create_po(maj1)

    sim = simulate(aig)

    majority = TruthTable(3)
    majority.create_from_hex_string("e8")

    assert len(sim) == 1
    assert sim[0] == majority


def test_multi_output_aig():
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
