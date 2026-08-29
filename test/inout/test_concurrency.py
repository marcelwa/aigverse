from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING

from aigverse.io import read_aiger_into_aig, read_ascii_aiger_into_aig, write_aiger

if TYPE_CHECKING:
    from aigverse.networks import Aig

dir_path = Path(os.path.realpath(__file__)).parent

# enough work per pool that the reads genuinely overlap rather than finishing
# before the second thread starts
REPEATS = 32
THREADS = 8


def shape(aig: Aig) -> tuple[int, int, int, int, list[int], list[int]]:
    return (aig.size, aig.num_pis, aig.num_pos, aig.num_gates, aig.pis(), aig.gates())


def test_concurrent_binary_reads():
    path = str(dir_path / "../resources/mux21.aig")
    expected = shape(read_aiger_into_aig(path))

    with ThreadPoolExecutor(THREADS) as pool:
        aigs = list(pool.map(read_aiger_into_aig, [path] * REPEATS))

    assert [shape(aig) for aig in aigs] == [expected] * REPEATS


def test_concurrent_ascii_reads():
    path = str(dir_path / "../resources/or.aag")
    expected = shape(read_ascii_aiger_into_aig(path))

    with ThreadPoolExecutor(THREADS) as pool:
        aigs = list(pool.map(read_ascii_aiger_into_aig, [path] * REPEATS))

    assert [shape(aig) for aig in aigs] == [expected] * REPEATS


def test_concurrent_writes(three_input_and_chain_aig: Aig, tmp_path: Path):
    paths = [str(tmp_path / f"{i}.aig") for i in range(REPEATS)]

    with ThreadPoolExecutor(THREADS) as pool:
        list(pool.map(lambda p: write_aiger(three_input_and_chain_aig, p), paths))

    expected = shape(three_input_and_chain_aig)
    assert [shape(read_aiger_into_aig(p)) for p in paths] == [expected] * REPEATS
