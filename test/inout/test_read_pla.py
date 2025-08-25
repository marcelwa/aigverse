from __future__ import annotations

import os
from pathlib import Path

from aigverse import TruthTable, read_pla_into_aig, simulate

dir_path = Path(os.path.realpath(__file__)).parent


def test_read_pla_into_aig():
    aig = read_pla_into_aig(str(dir_path / "../resources/test.pla"))
    assert aig.num_pis() == 3
    assert aig.num_pos() == 2
    assert aig.num_gates() == 5
    sim = simulate(aig)
    tt_0 = TruthTable(3)
    tt_0.create_from_binary_string("10110001")
    tt_1 = TruthTable(3)
    tt_1.create_from_binary_string("11100000")
    assert len(sim) == 2
    assert sim[0] == tt_0
    assert sim[1] == tt_1
