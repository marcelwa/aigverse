from __future__ import annotations

import os
from pathlib import Path

from aigverse import Aig, read_aiger_into_aig, write_aiger

dir_path = Path(os.path.realpath(__file__)).parent


def test_write_aiger() -> None:
    aig = Aig()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()

    a1 = aig.create_and(x1, x2)
    a2 = aig.create_and(x1, x3)
    a3 = aig.create_and(a1, a2)

    aig.create_po(a3)

    write_aiger(aig, str(dir_path / "../resources/test.aig"))

    aig2 = read_aiger_into_aig(str(dir_path / "../resources/test.aig"))

    assert aig2.size() == 7
    assert aig2.nodes() == list(range(7))
    assert aig2.num_gates() == 3
    assert aig2.gates() == [4, 5, 6]
    assert aig2.pis() == [1, 2, 3]
