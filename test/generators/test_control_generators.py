from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aigverse.algorithms import equivalence_checking, simulate
from aigverse.generators import binary_decoder, multiplexer

if TYPE_CHECKING:
    from aigverse.networks import Aig


def test_mux_selects_then_or_else_word(mux1_reference: Aig) -> None:
    generated = multiplexer(1)

    assert equivalence_checking(mux1_reference, generated)


def test_binary_decoder_two_selects() -> None:
    aig = binary_decoder(2)

    sim = simulate(aig)
    assert aig.num_pis == 2
    assert aig.num_pos == 4
    observed_minterms: set[int] = set()
    for tt in sim:
        assert tt.count_ones() == 1
        one_positions = [i for i in range(tt.num_bits()) if tt.get_bit(i) == 1]
        assert len(one_positions) == 1
        observed_minterms.add(one_positions[0])

    assert observed_minterms == set(range(aig.num_pos))


def test_binary_decoder_one_select_matches_not_and_identity(decoder1_reference: Aig) -> None:
    generated = binary_decoder(1)

    assert equivalence_checking(decoder1_reference, generated)


@pytest.mark.parametrize("bitwidth", [0])
def test_multiplexer_rejects_zero_bitwidth(bitwidth: int) -> None:
    with pytest.raises(ValueError, match="greater than 0"):
        multiplexer(bitwidth)


@pytest.mark.parametrize("num_select_bits", [0])
def test_binary_decoder_rejects_zero_select_bits(num_select_bits: int) -> None:
    with pytest.raises(ValueError, match="greater than 0"):
        binary_decoder(num_select_bits)
