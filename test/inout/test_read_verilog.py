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


@pytest.mark.parametrize("helper_position", ["before", "after"])
def test_read_verilog_with_helper_module(helper_position: str, tmp_path: Path) -> None:
    verilog_path = tmp_path / "modules.v"
    top = """module top(b, a, y, z);
input b, a;
output y, z;
assign y = a & b;
assign z = a;
endmodule
"""
    helper = """module helper(x, q);
input x;
output q;
assign q = ~x;
endmodule
"""
    verilog_path.write_text(helper + top if helper_position == "before" else top + helper)

    aig = read_verilog_into_aig(verilog_path)

    assert aig.get_network_name() == "top"
    assert [aig.get_name(AigSignal(pi, False)) for pi in aig.pis()] == ["b", "a"]
    assert [aig.get_output_name(po) for po in range(aig.num_pos)] == ["y", "z"]
    assert [tt.to_binary() for tt in simulate(aig)] == ["1000", "1100"]


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("module top(a); input a; endmodule\nmodule top(b); input b; endmodule", "duplicate Verilog module"),
        ("module top(y); output y; endmodule", "undriven Verilog output"),
    ],
    ids=["duplicate-top", "undriven-output"],
)
def test_read_verilog_preserves_invalid_definition_errors(source: str, message: str, tmp_path: Path) -> None:
    verilog_path = tmp_path / "invalid.v"
    verilog_path.write_text(source)

    with pytest.raises(ValueError, match=message):
        read_verilog_into_aig(verilog_path)


@pytest.mark.parametrize("literal", ["18446744073709551616", "18446744073709551616'h1"], ids=["decimal", "hex-width"])
def test_read_verilog_preserves_overflow_errors(literal: str, tmp_path: Path) -> None:
    verilog_path = tmp_path / "overflow.v"
    verilog_path.write_text(
        f"""module ripple_carry_adder(a,b,s);
input a,b;
output s;
endmodule
module top(a,b,y);
input a,b;
output y;
ripple_carry_adder #({literal}) adder(.a(a),.b(b),.s(y));
endmodule
"""
    )

    with pytest.raises(IndexError):
        read_verilog_into_aig(verilog_path)
