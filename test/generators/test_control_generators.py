from __future__ import annotations

import pytest

from aigverse.algorithms import equivalence_checking, simulate
from aigverse.generators import binary_decoder, multiplexer
from aigverse.networks import Aig


def test_mux_selects_then_or_else_word() -> None:
    generated = multiplexer(1)

    reference = Aig()
    cond = reference.create_pi()
    t0 = reference.create_pi()
    e0 = reference.create_pi()
    reference.create_po(reference.create_ite(cond, t0, e0))

    assert equivalence_checking(reference, generated)


def test_binary_decoder_two_selects() -> None:
    aig = binary_decoder(2)

    sim = simulate(aig)
    assert aig.num_pis == 2
    assert aig.num_pos == 4
    for tt in sim:
        assert tt.count_ones() == 1


def test_binary_decoder_one_select_matches_not_and_identity() -> None:
    generated = binary_decoder(1)

    reference = Aig()
    x = reference.create_pi()
    reference.create_po(~x)
    reference.create_po(x)

    assert equivalence_checking(reference, generated)


@pytest.mark.parametrize("bitwidth", [0])
def test_multiplexer_rejects_zero_bitwidth(bitwidth: int) -> None:
    with pytest.raises(ValueError, match="greater than 0"):
        multiplexer(bitwidth)


@pytest.mark.parametrize("num_select_bits", [0])
def test_binary_decoder_rejects_zero_select_bits(num_select_bits: int) -> None:
    with pytest.raises(ValueError, match="greater than 0"):
        binary_decoder(num_select_bits)
