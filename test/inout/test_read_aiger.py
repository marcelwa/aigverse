from __future__ import annotations

import os
from pathlib import Path

import pytest

from aigverse.io import (
    read_aiger_into_aig,
    read_aiger_into_sequential_aig,
    read_ascii_aiger_into_aig,
    read_ascii_aiger_into_sequential_aig,
)
from aigverse.networks import AigSignal

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
    assert aig.is_pi(2)
    assert aig.is_pi(3)
    assert aig.num_pos() == 1
    assert aig.fanins(0) == []
    assert aig.fanins(1) == []
    assert aig.fanins(2) == []
    assert aig.fanins(3) == []
    assert aig.fanins(5) == [AigSignal(2, False), AigSignal(3, False)]
    assert aig.fanins(6) == [AigSignal(4, True), AigSignal(5, True)]

    with pytest.raises(RuntimeError):
        read_aiger_into_aig(str(dir_path / "mux41.aig"))


def test_read_ascii_aiger_into_aig():
    aig = read_ascii_aiger_into_aig(str(dir_path / "../resources/or.aag"))

    assert aig.size() == 4
    assert aig.nodes() == list(range(4))
    assert aig.num_gates() == 1
    assert aig.gates() == [3]
    assert aig.pis() == [1, 2]

    with pytest.raises(RuntimeError):
        read_ascii_aiger_into_aig(str(dir_path / "and.aag"))


def test_read_aiger_with_names():
    """Test that AIGER files with names are properly read into NamedAig."""
    aig = read_ascii_aiger_into_aig(str(dir_path / "../resources/and_with_names.aag"))

    # Test basic network properties
    assert aig.num_pis() == 2
    assert aig.num_pos() == 1
    assert aig.num_gates() == 1

    # Test PI names (i0 input_a, i1 input_b)
    pi_nodes = aig.pis()
    assert len(pi_nodes) == 2
    assert aig.has_name(AigSignal(pi_nodes[0], False))
    assert aig.get_name(AigSignal(pi_nodes[0], False)) == "input_a"
    assert aig.has_name(AigSignal(pi_nodes[1], False))
    assert aig.get_name(AigSignal(pi_nodes[1], False)) == "input_b"

    # Test PO names (o0 output_and)
    assert aig.has_output_name(0)
    assert aig.get_output_name(0) == "output_and"


def test_read_aiger_into_sequential_aig():
    saig = read_aiger_into_sequential_aig(str(dir_path / "../resources/mux21.aig"))

    assert saig.size() == 7
    assert saig.nodes() == list(range(7))
    assert saig.num_gates() == 3
    assert saig.gates() == [4, 5, 6]
    assert saig.pis() == [1, 2, 3]
    assert saig.is_and(4)
    assert saig.is_and(5)
    assert saig.is_and(6)
    assert saig.is_constant(0)
    assert saig.num_pis() == 3
    assert saig.is_pi(2)
    assert saig.is_pi(3)
    assert saig.num_pos() == 1
    assert saig.fanins(0) == []
    assert saig.fanins(1) == []
    assert saig.fanins(2) == []
    assert saig.fanins(3) == []
    assert saig.fanins(5) == [AigSignal(2, False), AigSignal(3, False)]
    assert saig.fanins(6) == [AigSignal(4, True), AigSignal(5, True)]

    with pytest.raises(RuntimeError):
        read_aiger_into_sequential_aig(str(dir_path / "mux41.aig"))


def test_read_ascii_aiger_into_sequential_aig():
    saig = read_ascii_aiger_into_sequential_aig(str(dir_path / "../resources/or.aag"))

    assert saig.size() == 4
    assert saig.nodes() == list(range(4))
    assert saig.num_gates() == 1
    assert saig.gates() == [3]
    assert saig.pis() == [1, 2]

    with pytest.raises(RuntimeError):
        read_ascii_aiger_into_sequential_aig(str(dir_path / "and.aag"))


def test_read_sequential_aiger():
    """Test reading a sequential AIGER file with registers."""
    saig = read_ascii_aiger_into_sequential_aig(str(dir_path / "../resources/seq.aag"))

    # Test basic network properties
    assert saig.size() == 8  # 0 (constant), 2 PIs, 1 RO, 4 gates
    assert saig.num_pis() == 2
    assert saig.num_pos() == 2
    assert saig.num_gates() == 4

    # Test combinational I/O counts
    assert saig.num_cis() == 3  # 2 PIs + 1 RO
    assert saig.num_cos() == 3  # 2 POs + 1 RI

    # Test register counts
    assert len(saig.ros()) == 1  # 1 register output
    assert len(saig.ris()) == 1  # 1 register input
    assert saig.num_registers() == 1

    # Get register signals
    ro_nodes = saig.ros()
    assert len(ro_nodes) == 1
    ro_node = ro_nodes[0]

    ri_signals = saig.ris()
    assert len(ri_signals) == 1
    ri_signal = ri_signals[0]

    # Test register iteration - returns pairs of (ri_signal, ro_node)
    registers = saig.registers()
    assert len(registers) == 1
    ri, ro = registers[0]

    # The ri_signal should match what we got from ris()
    assert ri == ri_signal

    # The ro node should match what we got from ros()
    assert ro == ro_node

    # Test register access methods
    assert saig.ro_at(0) == ro_node
    assert saig.ri_at(0) == ri_signal
    assert saig.ri_to_ro(ri_signal) == ro_node
