"""aigverse adapters for ML tasks."""

from __future__ import annotations

from typing import Any, Final

import networkx as nx
import numpy as np

from .. import Aig, DepthAig, TruthTable, simulate, simulate_nodes, to_edge_list


def to_networkx(
    self: Aig, *, const_nodes: bool = False, levels: bool = False, node_tts: bool = False, graph_tts: bool = False
) -> nx.DiGraph:
    """Converts an AIG to a networkx.DiGraph.

    This function transforms the AIG into a directed graph representation
    using the networkx library. It allows for the inclusion of various
    attributes for the graph, its nodes, and edges, making it suitable
    for graph-based machine learning tasks.

    Args:
        self: The AIG object to convert.
        const_nodes: If True, includes constant nodes in the graph.
            Defaults to False.
        levels: If True, computes and adds level information for each node
            and the total number of levels to the graph. Defaults to False.
        node_tts: If True, computes and adds a truth table for each node
            as a 'function' attribute. Defaults to False.
        graph_tts: If True, computes and adds the graph's overall truth
            table as a 'function' attribute to the graph. Defaults to False.

    Returns:
        A networkx.DiGraph representing the AIG.

    Graph Attributes:
        - type (str): "AIG".
        - num_pis (int): Number of primary inputs.
        - num_pos (int): Number of primary outputs.
        - num_gates (int): Number of AND gates.
        - levels (int, optional): Total number of levels in the AIG.
        - function (list[TruthTable], optional): Graph's truth table.

    Node Attributes:
        - index (int): The node's identifier.
        - level (int, optional): The level of the node in the AIG.
        - function (TruthTable, optional): The node's truth table.
        - type (np.ndarray): A one-hot encoded vector representing the node
          type ([const, pi, gate, po]).

    Edge Attributes:
        - type (np.ndarray): A one-hot encoded vector representing the edge
          type ([regular, inverted]).
    """
    # one-hot encodings for node types: [const, pi, gate, po]
    node_type_const: Final[np.ndarray[Any, np.dtype[np.float32]]] = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    node_type_pi: Final[np.ndarray[Any, np.dtype[np.float32]]] = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
    node_type_gate: Final[np.ndarray[Any, np.dtype[np.float32]]] = np.array([0.0, 0.0, 1.0, 0.0], dtype=np.float32)
    node_type_po: Final[np.ndarray[Any, np.dtype[np.float32]]] = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)

    # one-hot encodings for edge types: [regular, inverted]
    edge_type_regular: Final[np.ndarray[Any, np.dtype[np.float32]]] = np.array([1.0, 0.0], dtype=np.float32)
    edge_type_inverted: Final[np.ndarray[Any, np.dtype[np.float32]]] = np.array([0.0, 1.0], dtype=np.float32)

    # Conditionally compute levels if requested
    if levels:
        depth_aig = DepthAig(self)

    # Conditionally compute node truth tables if requested
    if node_tts:
        node_funcs: dict[int, TruthTable] = simulate_nodes(self)

    # Conditionally compute graph output truth tables if requested
    if graph_tts:
        graph_func: list[TruthTable] = simulate(self)

    # Initialize the networkx graph
    g = nx.DiGraph()

    # Add global graph attributes
    g.graph["type"] = "AIG"
    g.graph["num_pis"] = self.num_pis()
    g.graph["num_pos"] = self.num_pos()
    g.graph["num_gates"] = self.num_gates()
    if levels:
        g.graph["levels"] = depth_aig.num_levels()
    if graph_tts:
        g.graph["function"] = graph_func

    # Iterate over all nodes in the AIG, plus synthetic PO nodes
    for node in self.nodes() + [self.po_index(po) + self.size() for po in self.pos()]:
        # Skip constant nodes if const_nodes is False
        if self.is_constant(node) and not const_nodes:
            continue

        # Prepare node attributes dictionary
        attrs: dict[str, Any] = {"index": node}
        if levels:
            attrs["level"] = depth_aig.level(node)
        if node_tts and node in node_funcs:
            attrs["function"] = node_funcs[node]  # type: ignore[index]

        # Determine and assign one-hot encoded node type
        if self.is_constant(node):
            type_vec = node_type_const
        elif self.is_pi(node):
            type_vec = node_type_pi
        elif self.is_and(node):
            type_vec = node_type_gate
        else:  # is PO
            type_vec = node_type_po
        attrs["type"] = type_vec

        # Add the node to the graph with its attributes
        g.add_node(node, **attrs)

    # Export the AIG as an edge list
    edges = to_edge_list(self)

    # Iterate over all edges and add them to the graph
    for src, tgt, weight in [(e.source, e.target, e.weight) for e in edges]:
        # Assign one-hot encoded edge type based on inversion
        edge_type = edge_type_inverted if weight else edge_type_regular
        g.add_edge(src, tgt, type=edge_type)

    return g


Aig.to_networkx = to_networkx  # type: ignore[attr-defined]

del to_networkx
