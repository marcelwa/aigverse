"""AIG to NetworkX adapter."""

from __future__ import annotations

from typing import Any, Final

import networkx as nx
import numpy as np

from .. import Aig, DepthAig, simulate, simulate_nodes, to_edge_list


def to_networkx(
    self: Aig,
    *,
    levels: bool = False,
    fanouts: bool = False,
    node_tts: bool = False,
    graph_tts: bool = False,
    dtype: type[np.generic] = np.int8,
) -> nx.DiGraph:
    """Converts an :class:`~aigverse.Aig` to a :class:`~networkx.DiGraph`.

    This function transforms the AIG into a directed graph representation
    using the NetworkX library. It allows for the inclusion of various
    attributes for the graph, its nodes, and edges, making it suitable
    for graph-based machine learning tasks.

    Note that the constant-0 node is always included in the graph, as
    index 0, even if it is not referenced by any edges.

    Args:
        self: The AIG object to convert.
        levels: If True, computes and adds level information for each node
            and the total number of levels to the graph, as attributes
            ``levels`` and ``level``, respectively. Defaults to False.
        fanouts: If True, adds fanout size information for each node
            as a ``fanouts`` attribute. Defaults to False.
        node_tts: If True, computes and adds a truth table for each node
            as a ``function`` attribute. Defaults to False.
        graph_tts: If True, computes and adds the graph's overall truth
            table as a ``function`` attribute to the graph. Defaults to False.
        dtype: The data type for truth tables and all one-hot encodings.
            Defaults to :obj:`~numpy.int8`. For machine learning tasks, a
            floating-point type such as :obj:`~numpy.float32` or
            :obj:`~numpy.float64` may be more appropriate, as it allows
            for gradient-based optimization.

    Returns:
        A :class:`~networkx.DiGraph` representing the AIG.

    Graph Attributes:
        - type (str): ``"AIG"``.
        - num_pis (int): Number of primary inputs.
        - num_pos (int): Number of primary outputs.
        - num_gates (int): Number of AND gates.
        - levels (int, optional): Total number of levels in the AIG.
        - function (list[:class:`~numpy.ndarray`], optional): Graph's truth tables.

    Node Attributes:
        - index (int): The node's identifier.
        - level (int, optional): The level of the node in the AIG.
        - function (:class:`~numpy.ndarray`, optional): The node's truth table.
        - type (:class:`~numpy.ndarray`): A one-hot encoded vector representing
            the node type (``[const, pi, gate, po]``). The data type is determined
            by the ``dtype`` argument, defaulting to :obj:`~numpy.int8`.

    Edge Attributes:
        - type (:class:`~numpy.ndarray`): A one-hot encoded vector representing the edge
            type (``[regular, inverted]``). The data type is determined by the
            ``dtype`` argument, defaulting to :obj:`~numpy.int8`.
    """
    # one-hot encodings for node types: [const, pi, gate, po]
    node_type_const: Final[np.ndarray[Any, np.dtype[np.int8]]] = np.array([1, 0, 0, 0], dtype=dtype)
    node_type_pi: Final[np.ndarray[Any, np.dtype[np.int8]]] = np.array([0, 1, 0, 0], dtype=dtype)
    node_type_gate: Final[np.ndarray[Any, np.dtype[np.int8]]] = np.array([0, 0, 1, 0], dtype=dtype)
    node_type_po: Final[np.ndarray[Any, np.dtype[np.int8]]] = np.array([0, 0, 0, 1], dtype=dtype)

    # one-hot encodings for edge types: [regular, inverted]
    edge_type_regular: Final[np.ndarray[Any, np.dtype[np.int8]]] = np.array([1, 0], dtype=dtype)
    edge_type_inverted: Final[np.ndarray[Any, np.dtype[np.int8]]] = np.array([0, 1], dtype=dtype)

    # Conditionally compute levels if requested
    if levels:
        depth_aig = DepthAig(self)

    node_funcs = {}
    graph_funcs = []

    # Conditionally compute node truth tables if requested
    if node_tts:
        node_funcs = {node: np.array(tt, dtype=dtype) for node, tt in simulate_nodes(self).items()}
        graph_funcs = [np.array(tt, dtype=dtype) for tt in simulate(self)]

    # Conditionally compute graph output truth tables if requested
    elif graph_tts:
        graph_funcs = [np.array(tt, dtype=dtype) for tt in simulate(self)]

    # Initialize the networkx graph
    g = nx.DiGraph()

    # Add global graph attributes
    g.graph["type"] = "AIG"
    g.graph["num_pis"] = self.num_pis()
    g.graph["num_pos"] = self.num_pos()
    g.graph["num_gates"] = self.num_gates()
    if levels:
        g.graph["levels"] = depth_aig.num_levels() + 1  # + 1 for the PO level
    if graph_tts:
        g.graph["function"] = graph_funcs

    # Iterate over all nodes in the AIG, plus synthetic PO nodes
    for node in self.nodes() + [self.po_index(po) + self.size() for po in self.pos()]:
        # Prepare node attributes dictionary
        attrs: dict[str, Any] = {"index": node}
        is_synthetic_po = node >= self.size()  # type: ignore[operator]

        if is_synthetic_po:
            type_vec = node_type_po
            if levels:
                attrs["level"] = depth_aig.num_levels() + 1
            if fanouts:
                attrs["fanouts"] = 0
            if node_tts:
                po_index = self.node_to_index(node) - self.size()
                attrs["function"] = graph_funcs[po_index]
        else:  # regular node
            if self.is_constant(node):
                type_vec = node_type_const
            elif self.is_pi(node):
                type_vec = node_type_pi
            else:  # is gate
                type_vec = node_type_gate

            if levels:
                attrs["level"] = depth_aig.level(node)
            if fanouts:
                attrs["fanouts"] = self.fanout_size(node)
            if node_tts:
                attrs["function"] = node_funcs[self.node_to_index(node)]

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
