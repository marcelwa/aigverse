from __future__ import annotations

from aigverse.algorithms import simulate
from aigverse.generators import binary_decoder, multiplexer
from aigverse.networks import Aig


def test_mux_selects_then_or_else_word() -> None:
    generated = multiplexer(1)

    reference = Aig()
    cond = reference.create_pi()
    t0 = reference.create_pi()
    e0 = reference.create_pi()
    reference.create_po(reference.create_ite(cond, t0, e0))

    assert simulate(generated)[0].to_binary() == simulate(reference)[0].to_binary()


def test_binary_decoder_two_selects() -> None:
    aig = binary_decoder(2)

    sim = simulate(aig)
    assert aig.num_pis == 2
    assert aig.num_pos == 4
    for tt in sim:
        assert tt.count_ones() == 1
