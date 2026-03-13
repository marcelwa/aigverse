from __future__ import annotations

from typing import TYPE_CHECKING

from aigverse.io import read_aiger_into_aig, write_aiger

if TYPE_CHECKING:
    from pathlib import Path

    from aigverse.networks import Aig


def test_write_aiger(three_input_and_chain_aig: Aig, tmp_path: Path) -> None:
    aig_path = tmp_path / "test.aig"
    write_aiger(three_input_and_chain_aig, str(aig_path))

    aig2 = read_aiger_into_aig(str(aig_path))

    assert aig2.size == 7
    assert aig2.nodes() == list(range(7))
    assert aig2.num_gates == 3
    assert aig2.gates() == [4, 5, 6]
    assert aig2.pis() == [1, 2, 3]
