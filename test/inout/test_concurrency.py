from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from aigverse.io import (
    read_aiger_into_aig,
    read_aiger_into_sequential_aig,
    read_ascii_aiger_into_aig,
    read_ascii_aiger_into_sequential_aig,
    read_pla_into_aig,
    read_verilog_into_aig,
    write_aiger,
    write_verilog,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from aigverse.networks import Aig

dir_path = Path(os.path.realpath(__file__)).parent

REPEATS = 16
THREADS = 8

READERS = [
    (read_aiger_into_aig, "mux21.aig"),
    (read_ascii_aiger_into_aig, "or.aag"),
    (read_aiger_into_sequential_aig, "lfsr.aig"),
    (read_ascii_aiger_into_sequential_aig, "seq.aag"),
    (read_pla_into_aig, "test.pla"),
    (read_verilog_into_aig, "test.v"),
]


def shape(aig: Aig) -> tuple[int, int, int, int, list[int], list[int]]:
    return (aig.size, aig.num_pis, aig.num_pos, aig.num_gates, aig.pis(), aig.gates())


@pytest.mark.parametrize(("reader", "resource"), READERS, ids=[r for _, r in READERS])
def test_concurrent_reads(reader: Callable[[str], Aig], resource: str):
    path = str(dir_path / "../resources" / resource)
    expected = shape(reader(path))

    with ThreadPoolExecutor(THREADS) as pool:
        aigs = list(pool.map(reader, [path] * REPEATS))

    assert [shape(aig) for aig in aigs] == [expected] * REPEATS


# write_dot is absent by design: its drawer mutates the network's shared storage, so
# its binding keeps the GIL. See the comment in src/aigverse/io/write_dot.cpp.
@pytest.mark.parametrize(("writer", "suffix"), [(write_aiger, "aig"), (write_verilog, "v")])
def test_concurrent_writes(
    writer: Callable[[Aig, str], None], suffix: str, three_input_and_chain_aig: Aig, tmp_path: Path
):
    paths = [tmp_path / f"{i}.{suffix}" for i in range(REPEATS)]

    with ThreadPoolExecutor(THREADS) as pool:
        list(pool.map(lambda p: writer(three_input_and_chain_aig, str(p)), paths))

    serial = tmp_path / f"serial.{suffix}"
    writer(three_input_and_chain_aig, str(serial))
    assert [p.read_bytes() for p in paths] == [serial.read_bytes()] * REPEATS
