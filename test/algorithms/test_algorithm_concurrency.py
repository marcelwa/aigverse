from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any

import pytest

from aigverse.algorithms import (
    aig_cut_rewriting,
    aig_resubstitution,
    balancing,
    cleanup_dangling,
    equivalence_checking,
    simulate,
    simulate_nodes,
    sop_refactoring,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from aigverse.networks import Aig

# More repeats than the io and generators suites use: a single call is wrong in roughly
# one attempt in ten, so 16 of them would let a regression through too often.
REPEATS = 32
THREADS = 8


def shape(aig: Aig | None) -> tuple[int, int, int, int, list[int]]:
    assert aig is not None  # the transforms return None only for inplace=True
    return (aig.size, aig.num_pis, aig.num_pos, aig.num_gates, aig.to_index_list().raw())


# Every binding that takes a network. `spec` and `impl` are the same object here: a
# network is equivalent to itself, so any False is a race. `cleanup_dangling` is trivially
# correct while it keeps the GIL and is listed anyway, as the tripwire for a guard being
# put back without a clone; see src/aigverse/algorithms/transform_helpers.hpp.
CASES: list[tuple[str, Callable[[Aig], Any]]] = [
    ("equivalence_checking", lambda aig: equivalence_checking(aig, aig)),
    ("aig_cut_rewriting", lambda aig: shape(aig_cut_rewriting(aig))),
    ("cleanup_dangling", lambda aig: shape(cleanup_dangling(aig))),
    ("balancing", lambda aig: shape(balancing(aig))),
    ("sop_refactoring", lambda aig: shape(sop_refactoring(aig))),
    ("aig_resubstitution", lambda aig: shape(aig_resubstitution(aig))),
    ("simulate", lambda aig: [tt.to_binary() for tt in simulate(aig)]),
    ("simulate_nodes", lambda aig: sorted((n, tt.to_binary()) for n, tt in simulate_nodes(aig).items())),
]


@pytest.mark.parametrize("call", [c for _, c in CASES], ids=[name for name, _ in CASES])
def test_concurrent_calls_on_one_shared_network(call: Callable[[Aig], Any], race_prone_aig: Aig) -> None:
    expected = call(race_prone_aig)

    with ThreadPoolExecutor(THREADS) as pool:
        results = [f.result() for f in [pool.submit(call, race_prone_aig) for _ in range(REPEATS)]]

    assert results == [expected] * REPEATS
