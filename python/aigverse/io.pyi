"""Provides file import and export functions for logic networks.

The module contains readers and writers for common file formats in the domain.
"""

import os
from typing import overload

import aigverse.networks

def read_aiger_into_aig(filename: str | os.PathLike) -> aigverse.networks.NamedAig:
    """Reads a binary AIGER file into a logic network.

    Args:
        filename: Path to the AIGER file.

    Returns:
        The parsed network instance.

    Raises:
        RuntimeError: If parsing the AIGER file fails, or if the file has latches, which this
            network type cannot represent. Read a sequential design with `read_aiger_into_sequential_aig`
            or `read_ascii_aiger_into_sequential_aig` instead.
    """

def read_ascii_aiger_into_aig(filename: str | os.PathLike) -> aigverse.networks.NamedAig:
    """Reads an ASCII AIGER file into a logic network.

    Args:
        filename: Path to the ASCII AIGER file.

    Returns:
        The parsed network instance.

    Raises:
        RuntimeError: If parsing the ASCII AIGER file fails, or if the file has latches, which this
            network type cannot represent. Read a sequential design with `read_aiger_into_sequential_aig`
            or `read_ascii_aiger_into_sequential_aig` instead.
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

@overload
def write_aiger(ntk: aigverse.networks.SequentialAig, filename: str | os.PathLike) -> None: ...
@overload
def write_aiger(ntk: aigverse.networks.NamedAig, filename: str | os.PathLike) -> None: ...
@overload
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

    The file must contain a module named ``top``.

    Args:
        filename: Path to the Verilog file.

    Returns:
        The parsed network instance.

    Raises:
        RuntimeError: If parsing fails or the file has no module named ``top``.
        ValueError: If the netlist has invalid signal or module definitions.
        IndexError: If an arithmetic literal or its width is out of range.
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

def read_blif_into_klut(filename: str | os.PathLike) -> aigverse.networks.NamedKlut:
    """Reads a flat combinational BLIF model into a NamedKlut.

    Args:
        filename: Source path. Only .model, .inputs, .outputs, .names, and .end are supported.

    Returns:
        The parsed network with primary-input and primary-output names and order preserved.

    Raises:
        RuntimeError: If the file is malformed, has missing drivers, or uses unsupported
            directives such as latches or hierarchy.
    """

@overload
def write_blif(ntk: aigverse.networks.NamedKlut, filename: str | os.PathLike) -> None: ...
@overload
def write_blif(ntk: aigverse.networks.Klut, filename: str | os.PathLike) -> None:
    """Writes a combinational k-LUT network as BLIF.

    Very deep chains can overflow the native stack and terminate the process.
    The limit depends on the platform and thread stack.

    Args:
        ntk: Network to serialize. NamedKlut preserves PI/PO names and order; internal names are regenerated.
        filename: Destination path.

    Raises:
        ValueError: If interface names are invalid or assign one name to different drivers.
        RuntimeError: If the destination cannot be opened or written.
    """
