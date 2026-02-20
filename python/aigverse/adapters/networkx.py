"""AIG to NetworkX adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, cast

import networkx as nx
import numpy as np

from ..algorithms import simulate, simulate_nodes
from ..networks import AigSignal, DepthAig, NamedAig
from ..utils import to_edge_list

if TYPE_CHECKING:
    from ..networks import Aig


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
        - name (str, optional): Network name (only for :class:`~aigverse.NamedAig`).

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
        - name (str, optional): Signal name or primary output name for edges to synthetic
            PO nodes (only for :class:`~aigverse.NamedAig`).
    """
    # one-hot encodings for node types: [const, pi, gate, po]
    node_type_const: Final[np.ndarray[Any, np.dtype[np.int8]]] = np.array([1, 0, 0, 0], dtype=dtype)
    node_type_pi: Final[np.ndarray[Any, np.dtype[np.int8]]] = np.array([0, 1, 0, 0], dtype=dtype)
    node_type_gate: Final[np.ndarray[Any, np.dtype[np.int8]]] = np.array([0, 0, 1, 0], dtype=dtype)
    node_type_po: Final[np.ndarray[Any, np.dtype[np.int8]]] = np.array([0, 0, 0, 1], dtype=dtype)

    # one-hot encodings for edge types: [regular, inverted]
    edge_type_regular: Final[np.ndarray[Any, np.dtype[np.int8]]] = np.array([1, 0], dtype=dtype)
    edge_type_inverted: Final[np.ndarray[Any, np.dtype[np.int8]]] = np.array([0, 1], dtype=dtype)

    # Check if this is a NamedAig
    self_named = cast("NamedAig", self) if isinstance(self, NamedAig) else None

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
    if self_named is not None and (network_name := self_named.get_network_name()):
        g.graph["name"] = network_name

    # Iterate over all regular nodes in the AIG
    for node in self.nodes():
        # Prepare node attributes dictionary
        # node is AigNode
        attrs: dict[str, Any] = {"index": node}

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
            attrs["function"] = node_funcs[node]

        attrs["type"] = type_vec
        g.add_node(node, **attrs)

    # Iterate over synthetic PO nodes
    for po_idx, _po in enumerate(self.pos()):
        synth_node = po_idx + self.size()
        attrs = {"index": synth_node}

        # Synthetic PO attributes
        type_vec = node_type_po
        if levels:
            attrs["level"] = depth_aig.num_levels() + 1
        if fanouts:
            attrs["fanouts"] = 0
        if node_tts:
            attrs["function"] = graph_funcs[po_idx]

        attrs["type"] = type_vec
        g.add_node(synth_node, **attrs)

    # Export the AIG as an edge list
    edges = to_edge_list(self)

    # Iterate over all edges and add them to the graph
    for src, tgt, weight in [(e.source, e.target, e.weight) for e in edges]:
        # Assign one-hot encoded edge type based on inversion
        edge_type = edge_type_inverted if weight else edge_type_regular
        edge_attrs: dict[str, Any] = {"type": edge_type}

        # Add signal name if available (edges represent signals)
        if self_named is not None:
            # source node is an integer (AigNode)
            src_int = src
            sig = AigSignal(src_int, bool(weight))
            if self_named.has_name(sig):
                edge_attrs["name"] = self_named.get_name(sig)

        g.add_edge(src, tgt, **edge_attrs)

    # Add PO names as attributes on edges going to synthetic PO nodes
    if self_named is not None:
        for po_idx, _ in enumerate(self_named.pos()):
            if self_named.has_output_name(po_idx):
                synthetic_po_node = po_idx + self_named.size()
                # Find all edges going into this synthetic PO node
                for pred in g.predecessors(synthetic_po_node):  # type: ignore[no-untyped-call]
                    g.edges[pred, synthetic_po_node]["name"] = self_named.get_output_name(po_idx)

    return g
