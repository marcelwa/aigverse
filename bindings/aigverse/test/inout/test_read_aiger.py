import os
from pathlib import Path

import pytest

from aigverse import AigSignal, read_aiger_into_aig, read_ascii_aiger_into_aig

dir_path = Path(os.path.realpath(__file__)).parent


def test_read_aiger_into_aig():
    aig = read_aiger_into_aig(str(dir_path / "../resources/mux21.aig"))

    assert aig.size() == 7
    assert aig.nodes() == list(range(7))
    assert aig.num_gates() == 3
    assert aig.gates() == [4, 5, 6]
    assert aig.pis() == [1, 2, 3]

    assert aig.is_and(4)
    assert aig.is_and(5)
    assert aig.is_and(6)

    assert aig.is_constant(0)

    assert aig.num_pis() == 3
    assert aig.pis() == [1, 2, 3]
    assert aig.is_pi(2)
    assert aig.is_pi(3)

    assert aig.num_pos() == 1

    assert aig.fanins(0) == []
    assert aig.fanins(1) == []
    assert aig.fanins(2) == []
    assert aig.fanins(3) == []
    assert aig.fanins(5) == [aig.make_signal(2), aig.make_signal(3)]
    assert aig.fanins(5) == [AigSignal(2, 0), AigSignal(3, 0)]
    assert aig.fanins(6) == [~aig.make_signal(4), ~aig.make_signal(5)]
    assert aig.fanins(6) == [AigSignal(4, 1), AigSignal(5, 1)]

    with pytest.raises(RuntimeError):
        aig = read_aiger_into_aig(str(dir_path / "mux41.aig"))


def test_read_ascii_aiger_into_aig():
    aig = read_ascii_aiger_into_aig(str(dir_path / "../resources/or.aag"))

    assert aig.size() == 4
    assert aig.nodes() == list(range(4))
    assert aig.num_gates() == 1
    assert aig.gates() == [3]
    assert aig.pis() == [1, 2]

    with pytest.raises(RuntimeError):
        aig = read_ascii_aiger_into_aig(str(dir_path / "and.aag"))
