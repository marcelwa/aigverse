from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, Literal

import pytest

from aigverse.algorithms import (
    aig_cut_rewriting,
    aig_resubstitution,
    balancing,
    cleanup_dangling,
    convert_klut_to_aig,
    equivalence_checking,
    lut_mapping,
    simulate,
    simulate_nodes,
    sop_refactoring,
)
from aigverse.networks import Aig, Klut, NamedAig, NamedKlut

if TYPE_CHECKING:
    from collections.abc import Callable

# More repeats than the io and generators suites use: a single call is wrong in roughly
# one attempt in ten, so 16 of them would let a regression through too often.
REPEATS = 32
THREADS = 8


def shape(aig: Aig | None) -> tuple[int, int, int, int, list[int]]:
    assert aig is not None  # the transforms return None only for inplace=True
    return (aig.size, aig.num_pis, aig.num_pos, aig.num_gates, aig.to_index_list().raw())


# Every binding that takes a network. `spec` and `impl` are the same object here: a
# network is equivalent to itself, so any False is a race. View-building calls must
# isolate traversal state when the GIL is absent; see src/aigverse/algorithms/transform_helpers.hpp.
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
    networks = [race_prone_aig, NamedAig(race_prone_aig)] * (REPEATS // 2)

    with ThreadPoolExecutor(THREADS) as pool:
        results = [f.result() for f in [pool.submit(call, network) for network in networks]]

    assert results == [expected] * REPEATS


def interface_names(ntk: NamedAig | NamedKlut) -> tuple[str, list[str], list[str]]:
    if isinstance(ntk, NamedAig):
        inputs = [ntk.get_name(ntk.make_signal(node)) for node in ntk.pis()]
    else:
        inputs = [ntk.get_name(node) for node in ntk.pis()]
    return ntk.get_network_name(), inputs, [ntk.get_output_name(i) for i in range(ntk.num_pos)]


@pytest.mark.parametrize("algorithm", ["heuristic", "classic", "sat", "sat_windowed"])
def test_concurrent_lut_mapping(
    race_prone_aig: Aig, algorithm: Literal["heuristic", "classic", "sat", "sat_windowed"]
) -> None:
    named = NamedAig(race_prone_aig)
    named.set_network_name("shared")
    for i, node in enumerate(named.pis()):
        named.set_name(named.make_signal(node), f"input{i}")
    for i in range(named.num_pos):
        named.set_output_name(i, f"output{i}")
    before = shape(race_prone_aig)
    expected = simulate(race_prone_aig)
    expected_names = interface_names(named)
    networks = [race_prone_aig, named] * (REPEATS // 2)
    conflict_limit = 100 if algorithm in {"sat", "sat_windowed"} else None

    with ThreadPoolExecutor(THREADS) as pool:
        results = [
            f.result()
            for f in [
                pool.submit(lut_mapping, ntk, algorithm=algorithm, conflict_limit=conflict_limit) for ntk in networks
            ]
        ]

    for i, result in enumerate(results):
        assert simulate(result) == expected
        if i % 2:
            assert isinstance(result, NamedKlut)
            assert interface_names(result) == expected_names
        else:
            assert type(result) is Klut
    assert shape(race_prone_aig) == before
    assert simulate(race_prone_aig) == expected
    assert interface_names(named) == expected_names


KLUT_CASES: list[tuple[str, Callable[[Klut], Any]]] = [
    ("convert_klut_to_aig", convert_klut_to_aig),
    ("cleanup_dangling", cleanup_dangling),
    ("equivalence_checking", lambda ntk: equivalence_checking(ntk, ntk)),
    ("simulate", simulate),
    ("simulate_nodes", simulate_nodes),
]


@pytest.mark.parametrize(("name", "call"), KLUT_CASES, ids=[name for name, _ in KLUT_CASES])
def test_concurrent_klut_calls(name: str, call: Callable[[Klut], Any], race_prone_aig: Aig) -> None:
    source = lut_mapping(race_prone_aig, algorithm="classic", cut_size=3)
    unused = source.create_pi()
    source.create_and(unused, source.pi_at(0))
    named = NamedKlut(source)
    named.set_network_name("shared")
    for i, node in enumerate(named.pis()):
        named.set_name(node, f"input{i}")
    for i in range(named.num_pos):
        named.set_output_name(i, f"output{i}")
    before = source.size, source.pis(), source.pos()
    functions = [(n, source.fanins(n), source.node_function(n).to_hex()) for n in source.gates()]
    expected_names = interface_names(named)
    expected_outputs = simulate(source)
    expected = call(source)
    if name == "equivalence_checking":
        assert expected is True
    networks = [source, named] * (REPEATS // 2)

    with ThreadPoolExecutor(THREADS) as pool:
        results = [f.result() for f in [pool.submit(call, ntk) for ntk in networks]]

    for i, result in enumerate(results):
        if isinstance(result, (Aig, Klut)):
            assert simulate(result) == expected_outputs
            if i % 2:
                assert isinstance(result, (NamedAig, NamedKlut))
                assert interface_names(result) == expected_names
            else:
                assert type(result) is type(expected)
        else:
            assert result == expected
    assert (source.size, source.pis(), source.pos()) == before
    assert [(n, source.fanins(n), source.node_function(n).to_hex()) for n in source.gates()] == functions
    assert simulate(source) == expected_outputs
    assert interface_names(named) == expected_names
