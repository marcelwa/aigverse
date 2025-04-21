from __future__ import annotations

import os
from pathlib import Path

from aigverse import read_verilog_into_aig

dir_path = Path(os.path.realpath(__file__)).parent


def test_read_verilog() -> None:
    aig = read_verilog_into_aig(str(dir_path / "../resources/case_verilog.v"))
    assert aig.size() == 6
    assert aig.nodes() == list(range(6))
    assert aig.num_gates() == 2
    assert aig.gates() == [4, 5]
    assert aig.pis() == [1, 2, 3]
