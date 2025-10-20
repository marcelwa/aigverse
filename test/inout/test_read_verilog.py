from __future__ import annotations

import os
from pathlib import Path

from aigverse import AigSignal, read_verilog_into_aig

dir_path = Path(os.path.realpath(__file__)).parent


def test_read_verilog() -> None:
    aig = read_verilog_into_aig(str(dir_path / "../resources/test.v"))
    assert aig.size() == 6
    assert aig.nodes() == list(range(6))
    assert aig.num_gates() == 2
    assert aig.gates() == [4, 5]
    assert aig.pis() == [1, 2, 3]


def test_read_verilog_with_names() -> None:
    """Test that Verilog files preserve signal names in NamedAig."""
    aig = read_verilog_into_aig(str(dir_path / "../resources/test.v"))

    # Test network name (module name)
    assert aig.get_network_name() == "top"

    # Test PI names (inputs: a, b, c)
    pi_nodes = aig.pis()
    assert len(pi_nodes) == 3

    # Check that at least one PI has a name
    pi_names = [aig.get_name(AigSignal(pi, False)) for pi in pi_nodes if aig.has_name(AigSignal(pi, False))]

    # The inputs should be named a, b, c
    assert set(pi_names) == {"a", "b", "c"}

    # Test PO names (output: y1)
    assert aig.num_pos() == 1
    assert aig.has_output_name(0)
    assert aig.get_output_name(0) == "y1"
