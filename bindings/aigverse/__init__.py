"""Bindings for aigverse."""

from __future__ import annotations

from ._version import version as __version__
from .pyaigverse import (
    Aig,
    AigEdge,
    AigEdgeList,
    AigNode,
    AigSignal,
    DepthAig,
    TruthTable,
    aig_cut_rewriting,
    aig_resubstitution,
    cofactor0,
    cofactor1,
    equivalence_checking,
    read_aiger_into_aig,
    read_ascii_aiger_into_aig,
    simulate,
    simulate_nodes,
    sop_refactoring,
    ternary_majority,
    to_edge_list,
    write_aiger,
)

__all__ = [
    "Aig",
    "AigEdge",
    "AigEdgeList",
    "AigNode",
    "AigSignal",
    "DepthAig",
    "TruthTable",
    "__version__",
    "aig_cut_rewriting",
    "aig_resubstitution",
    "cofactor0",
    "cofactor1",
    "equivalence_checking",
    "read_aiger_into_aig",
    "read_ascii_aiger_into_aig",
    "simulate",
    "simulate_nodes",
    "sop_refactoring",
    "ternary_majority",
    "to_edge_list",
    "write_aiger",
]
