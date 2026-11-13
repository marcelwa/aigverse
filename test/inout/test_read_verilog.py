from __future__ import annotations

import os
from pathlib import Path

import pytest

from aigverse.algorithms import simulate
from aigverse.io import read_verilog_into_aig
from aigverse.networks import AigSignal

dir_path = Path(os.path.realpath(__file__)).parent


def test_read_verilog() -> None:
    aig = read_verilog_into_aig(str(dir_path / "../resources/test.v"))
    assert aig.size == 6
    assert aig.nodes() == list(range(6))
    assert aig.num_gates == 2
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

    # The inputs should be named a, b, c
    pi_names = [aig.get_name(AigSignal(pi, False)) for pi in pi_nodes if aig.has_name(AigSignal(pi, False))]
    assert set(pi_names) == {"a", "b", "c"}

    # Test PO names (output: y1)
    assert aig.num_pos == 1
    assert aig.has_output_name(0)
    assert aig.get_output_name(0) == "y1"


@pytest.mark.parametrize(
    "source",
    ["", "module helper(x, q); input x; output q; assign q = x; endmodule"],
    ids=["empty", "helper-only"],
)
def test_read_verilog_requires_top(source: str, tmp_path: Path) -> None:
    verilog_path = tmp_path / "missing_top.v"
    verilog_path.write_text(source)

    with pytest.raises(RuntimeError, match="Error reading Verilog file"):
        read_verilog_into_aig(verilog_path)


def test_read_verilog_empty_top(tmp_path: Path) -> None:
    verilog_path = tmp_path / "empty_top.v"
    # Lorina requires at least one name in the module header.
    verilog_path.write_text("module top(unused); endmodule")

    aig = read_verilog_into_aig(verilog_path)

    assert aig.get_network_name() == "top"
    assert aig.num_pis == 0
    assert aig.num_pos == 0
    assert aig.num_gates == 0


def test_read_verilog_top_followed_by_helper(tmp_path: Path) -> None:
    verilog_path = tmp_path / "modules.v"
    verilog_path.write_text(
        """module top(b, a, y, z);
input b, a;
output y, z;
assign y = a & b;
assign z = a;
endmodule
module helper(x, q);
input x;
output q;
assign q = ~x;
endmodule
"""
    )

    aig = read_verilog_into_aig(verilog_path)

    assert aig.get_network_name() == "top"
    assert [aig.get_name(AigSignal(pi, False)) for pi in aig.pis()] == ["b", "a"]
    assert [aig.get_output_name(po) for po in range(aig.num_pos)] == ["y", "z"]
    assert [tt.to_binary() for tt in simulate(aig)] == ["1000", "1100"]
