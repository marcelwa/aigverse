from __future__ import annotations

from aigverse.generators import random_aig


def test_random_aig_respects_requested_size() -> None:
    aig = random_aig(num_pis=4, num_gates=10, seed=123)

    assert aig.num_pis == 4
    assert aig.num_gates == 10
    assert aig.num_pos > 0


def test_random_aig_reproducible_with_same_seed() -> None:
    aig0 = random_aig(num_pis=5, num_gates=12, seed=7)
    aig1 = random_aig(num_pis=5, num_gates=12, seed=7)

    assert aig0.to_index_list().raw() == aig1.to_index_list().raw()
