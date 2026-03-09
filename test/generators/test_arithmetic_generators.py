from __future__ import annotations

from aigverse.algorithms import simulate
from aigverse.generators import (
    carry_lookahead_adder,
    ripple_carry_adder,
    ripple_carry_multiplier,
    sideways_sum_adder,
)


def test_rca_and_cla_implement_same_function() -> None:
    aig_ripple = ripple_carry_adder(2)
    aig_cla = carry_lookahead_adder(2)

    assert [tt.to_binary() for tt in simulate(aig_ripple)] == [tt.to_binary() for tt in simulate(aig_cla)]


def test_sideways_sum_adder_counts_ones_for_two_bits() -> None:
    aig = sideways_sum_adder(2)

    sim = simulate(aig)
    # sum value for popcount([a,b]) in little-endian output bits
    assert sim[0].to_binary() == "0110"
    assert sim[1].to_binary() == "1000"


def test_ripple_carry_multiplier_two_bit_truth_tables() -> None:
    aig = ripple_carry_multiplier(2)

    sim = simulate(aig)
    assert len(sim) == 4


def test_high_level_network_builders_have_expected_io_sizes() -> None:
    adder = ripple_carry_adder(3)
    assert adder.num_pis == 6
    assert adder.num_pos == 4

    mult = ripple_carry_multiplier(3)
    assert mult.num_pis == 6
    assert mult.num_pos == 6

    cla = carry_lookahead_adder(3)
    assert cla.num_pis == 6
    assert cla.num_pos == 4

    pop = sideways_sum_adder(5)
    assert pop.num_pis == 5
    assert pop.num_pos == 3
