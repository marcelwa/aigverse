from __future__ import annotations

from aigverse.algorithms import simulate, simulate_nodes
from aigverse.networks import Aig, DepthAig
from aigverse.utils import TruthTable


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


def test_and_aig(and_gate_aig: Aig) -> None:
    aig = and_gate_aig

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


def test_or_aig(or_gate_aig: Aig) -> None:
    aig = or_gate_aig

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


def test_maj_aig(maj3_aig: Aig) -> None:
    aig = maj3_aig

    sim = simulate(aig)

    majority = TruthTable(3)
    majority.create_majority()

    assert len(sim) == 1
    assert sim[0] == majority

    n_map = simulate_nodes(aig)

    id_tt_a = TruthTable(3)
    id_tt_a.create_from_binary_string("10101010")
    id_tt_b = TruthTable(3)
    id_tt_b.create_from_binary_string("11001100")
    id_tt_c = TruthTable(3)
    id_tt_c.create_from_binary_string("11110000")

    assert len(n_map) == 8
    assert n_map[0].is_const0()
    assert n_map[1] == id_tt_a
    assert n_map[2] == id_tt_b
    assert n_map[3] == id_tt_c
    # we're expecting a negated MAJ at the node because the PO's inverted signal is not taken into account
    assert n_map[7] == ~majority


def test_multi_output_aig(and_or_two_output_aig: Aig) -> None:
    # also test DepthAig
    for ntk in [Aig, DepthAig]:
        aig = and_or_two_output_aig if ntk is Aig else ntk(and_or_two_output_aig)

        sim = simulate(aig)

        conjunction = TruthTable(2)
        conjunction.create_from_binary_string("1000")

        disjunction = TruthTable(2)
        disjunction.create_from_binary_string("1110")

        assert len(sim) == 2
        assert sim[0] == conjunction
        assert sim[1] == disjunction
