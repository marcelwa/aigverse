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
    read_blif_into_klut,
    read_pla_into_aig,
    read_verilog_into_aig,
    write_aiger,
    write_blif,
    write_dot,
    write_verilog,
)
from aigverse.networks import Klut, NamedKlut

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


def shape(aig: Aig | Klut) -> tuple[int, int, int, int, list[int], list[int]]:
    return (aig.size, aig.num_pis, aig.num_pos, aig.num_gates, aig.pis(), aig.gates())


@pytest.mark.parametrize(("reader", "resource"), READERS, ids=[r for _, r in READERS])
def test_concurrent_reads(reader: Callable[[str], Aig], resource: str):
    path = str(dir_path / "../resources" / resource)
    expected = shape(reader(path))

    with ThreadPoolExecutor(THREADS) as pool:
        aigs = list(pool.map(reader, [path] * REPEATS))

    assert [shape(aig) for aig in aigs] == [expected] * REPEATS


@pytest.mark.parametrize(("writer", "suffix"), [(write_aiger, "aig"), (write_dot, "dot"), (write_verilog, "v")])
def test_concurrent_writes(writer: Callable[[Aig, str], None], suffix: str, race_prone_aig: Aig, tmp_path: Path):
    paths = [tmp_path / f"{i}.{suffix}" for i in range(REPEATS)]
    serial = tmp_path / f"serial.{suffix}"
    writer(race_prone_aig, str(serial))
    expected = serial.read_bytes()

    with ThreadPoolExecutor(THREADS) as pool:
        list(pool.map(lambda p: writer(race_prone_aig, str(p)), paths))

    assert [p.read_bytes() for p in paths] == [expected] * REPEATS


@pytest.mark.parametrize("named", [True, False])
def test_concurrent_blif_writes(tmp_path: Path, *, named: bool) -> None:
    source = NamedKlut()
    nodes = [source.create_pi(f"input{i}") for i in range(10)]
    for _ in range(600):
        nodes.append(source.create_xor(nodes[-10], nodes[-7]))
    for index, node in enumerate(nodes[-10:]):
        source.create_po(node, f"output{index}")
    source.set_name(nodes[-1], "internal")
    ntk = source if named else Klut(source)
    before = (shape(ntk), ntk.pos(), [ntk.fanins(n) for n in ntk.gates()])
    functions = [ntk.node_function(n) for n in ntk.gates()]
    paths = [tmp_path / f"{i}.blif" for i in range(REPEATS)]
    serial = tmp_path / "serial.blif"
    write_blif(ntk, serial)
    expected = serial.read_bytes()

    with ThreadPoolExecutor(THREADS) as pool:
        list(pool.map(lambda path: write_blif(ntk, path), paths))

    assert [path.read_bytes() for path in paths] == [expected] * REPEATS
    assert (shape(ntk), ntk.pos(), [ntk.fanins(n) for n in ntk.gates()]) == before
    assert [ntk.node_function(n) for n in ntk.gates()] == functions
    assert [source.get_name(n) for n in source.pis()] == [f"input{i}" for i in range(10)]
    assert [source.get_output_name(i) for i in range(source.num_pos)] == [f"output{i}" for i in range(10)]
    assert source.get_name(nodes[-1]) == "internal"
    if named:
        restored = read_blif_into_klut(serial)
        assert [restored.get_name(n) for n in restored.pis()] == [f"input{i}" for i in range(10)]
        assert [restored.get_output_name(i) for i in range(restored.num_pos)] == [f"output{i}" for i in range(10)]
