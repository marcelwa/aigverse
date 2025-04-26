from __future__ import annotations

import os
from pathlib import Path

from aigverse import Aig, read_verilog_into_aig, write_verilog

dir_path = Path(os.path.realpath(__file__)).parent


def test_write_verilog() -> None:
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    a1 = aig.create_or(x1, x2)
    aig.create_po(a1)

    write_verilog(aig, str(dir_path / "../resources/test.v"))

    aig2 = read_verilog_into_aig(str(dir_path / "../resources/test.v"))

    assert aig2.size() == 4
    assert aig2.nodes() == list(range(4))
    assert aig2.num_gates() == 1
    assert aig2.gates() == [3]
    assert aig2.pis() == [1, 2]
