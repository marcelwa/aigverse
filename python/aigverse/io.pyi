"""Provides file import and export functions for logic networks.

The module contains readers and writers for common file formats in the domain.
"""

import os

import aigverse.networks

def read_aiger_into_aig(filename: str | os.PathLike) -> aigverse.networks.NamedAig:
    """Reads a binary AIGER file into a logic network.

    Args:
        filename: Path to the AIGER file.

    Returns:
        The parsed network instance.

    Raises:
        RuntimeError: If parsing the AIGER file fails.
    """

def read_ascii_aiger_into_aig(filename: str | os.PathLike) -> aigverse.networks.NamedAig:
    """Reads an ASCII AIGER file into a logic network.

    Args:
        filename: Path to the ASCII AIGER file.

    Returns:
        The parsed network instance.

    Raises:
        RuntimeError: If parsing the ASCII AIGER file fails.
    """

def read_aiger_into_sequential_aig(filename: str | os.PathLike) -> aigverse.networks.SequentialAig:
    """Reads a binary AIGER file into a logic network.

    Args:
        filename: Path to the AIGER file.

    Returns:
        The parsed network instance.

    Raises:
        RuntimeError: If parsing the AIGER file fails.
    """

def read_ascii_aiger_into_sequential_aig(filename: str | os.PathLike) -> aigverse.networks.SequentialAig:
    """Reads an ASCII AIGER file into a logic network.

    Args:
        filename: Path to the ASCII AIGER file.

    Returns:
        The parsed network instance.

    Raises:
        RuntimeError: If parsing the ASCII AIGER file fails.
    """

def write_aiger(ntk: aigverse.networks.Aig, filename: str | os.PathLike) -> None:
    """Writes a logic network to a binary AIGER file.

    Args:
            ntk: The network to serialize.
            filename: Destination path for the AIGER file.
    """

def read_pla_into_aig(filename: str | os.PathLike) -> aigverse.networks.Aig:
    """Reads a PLA file into a logic network.

    Args:
        filename: Path to the PLA file.

    Returns:
        The parsed network instance.

    Raises:
        RuntimeError: If parsing the PLA file fails.
    """

def read_verilog_into_aig(filename: str | os.PathLike) -> aigverse.networks.NamedAig:
    """Reads a synthesized gate-level Verilog netlist into a logic network.

    Args:
        filename: Path to the Verilog file.

    Returns:
        The parsed network instance.

    Raises:
        RuntimeError: If parsing the Verilog file fails.
    """

def write_verilog(ntk: aigverse.networks.Aig, filename: str | os.PathLike) -> None:
    """Writes a logic network to a Verilog netlist.

    Args:
            ntk: The network to serialize.
            filename: Destination path for the Verilog file.
    """

def write_dot(ntk: aigverse.networks.Aig, filename: str | os.PathLike) -> None:
    """Writes a logic network to a Graphviz DOT file for visualization.

    Args:
            ntk: The network to serialize.
            filename: Destination path for the DOT file.
    """
