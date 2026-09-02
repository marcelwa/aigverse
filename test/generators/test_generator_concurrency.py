from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import TYPE_CHECKING

import pytest

from aigverse.generators import (
    binary_decoder,
    carry_lookahead_adder,
    multiplexer,
    random_aig,
    ripple_carry_adder,
    ripple_carry_multiplier,
    sideways_sum_adder,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from aigverse.networks import Aig

REPEATS = 16
THREADS = 8

GENERATORS: list[Callable[[], Aig]] = [
    partial(random_aig, num_pis=8, num_gates=2000, seed=42),
    partial(ripple_carry_adder, 16),
    partial(carry_lookahead_adder, 16),
    partial(ripple_carry_multiplier, 8),
    partial(sideways_sum_adder, 16),
    partial(multiplexer, 16),
    partial(binary_decoder, 8),
]

IDS = [
    "random_aig",
    "ripple_carry_adder",
    "carry_lookahead_adder",
    "ripple_carry_multiplier",
    "sideways_sum_adder",
    "multiplexer",
    "binary_decoder",
]


def shape(aig: Aig) -> tuple[int, int, int, int, list[int]]:
    return (aig.size, aig.num_pis, aig.num_pos, aig.num_gates, aig.to_index_list().raw())


@pytest.mark.parametrize("generator", GENERATORS, ids=IDS)
def test_concurrent_generation(generator: Callable[[], Aig]) -> None:
    expected = shape(generator())

    with ThreadPoolExecutor(THREADS) as pool:
        aigs = [f.result() for f in [pool.submit(generator) for _ in range(REPEATS)]]

    assert [shape(aig) for aig in aigs] == [expected] * REPEATS
