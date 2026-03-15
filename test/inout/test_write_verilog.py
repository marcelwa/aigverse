from __future__ import annotations

from typing import TYPE_CHECKING

from aigverse.io import read_verilog_into_aig, write_verilog

if TYPE_CHECKING:
    from pathlib import Path

    from aigverse.networks import Aig


def test_write_verilog(simple_or_aig: Aig, tmp_path: Path) -> None:
    verilog_path = tmp_path / "test.v"
    write_verilog(simple_or_aig, str(verilog_path))

    aig2 = read_verilog_into_aig(str(verilog_path))

    assert aig2.size == 4
    assert aig2.nodes() == list(range(4))
    assert aig2.num_gates == 1
    assert aig2.gates() == [3]
    assert aig2.pis() == [1, 2]
