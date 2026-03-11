"""Provides logic network data structures and derived views.

This module includes network types, edge and index list utilities, and helper
objects for structural manipulation.
"""

import enum
from collections.abc import Iterator, Sequence
from typing import NoReturn, overload

class NodeTensorEncoding(enum.Enum):
    """Node encoding mode for exported graph tensors.

    All node features use `float32`; only the categorical encoding scheme changes.
    - `INTEGER`: Node classes are scalar labels in the first feature column.
    - `ONE_HOT`: Node classes are one-hot vectors in `[constant, pi, gate, po]` order.
    """

    INTEGER = 0
    """
    Scalar node labels in the first feature column: 0=constant, 1=pi, 2=gate, 3=po.
    """

    ONE_HOT = 1
    """One-hot node labels in [constant, pi, gate, po] order."""

class EdgeTensorEncoding(enum.Enum):
    """Edge encoding mode for exported graph tensors.

    All edge features use `float32`; only the categorical encoding scheme changes.
    - `BINARY`: Edge polarity is binary (regular=0.0, inverted=1.0).
    - `SIGNED`: Edge polarity is signed (regular=+1.0, inverted=-1.0).
    - `ONE_HOT`: Edge polarity is one-hot in `[regular, inverted]` order.
    """

    BINARY = 0
    """Labels are encoded as 0.0 (regular) and 1.0 (inverted)."""

    SIGNED = 1
    """Labels are encoded as +1.0 (regular) and -1.0 (inverted)."""

    ONE_HOT = 2
    """One-hot edge labels in [regular, inverted] order."""

class AigSignal:
    """Represents a signal in an AIG.

    Signals point to nodes and may be complemented.
    """

    def __init__(self, index: int, complement: bool) -> None:
        """Creates a signal from a node index and complement flag.

        Args:
                index: Node index referenced by the signal.
                complement: Whether the signal is complemented.
        """

    @property
    def index(self) -> int:
        """Node index referenced by the signal."""

    @property
    def complement(self) -> bool:
        """Whether this signal is complemented."""

    @property
    def data(self) -> int:
        """Raw packed signal representation."""

    def __hash__(self) -> int:
        """Returns a hash value for dictionary/set usage."""

    def __eq__(self, other: object) -> bool:
        """Returns whether two signals are equal.

        Args:
                other: Object to compare.

        Returns:
                ``True`` if equal, otherwise ``False``.
        """

    def __ne__(self, other: object) -> bool:
        """Returns whether two signals are not equal.

        Args:
                other: Object to compare.

        Returns:
                ``True`` if not equal, otherwise ``False``.
        """

    def __lt__(self, other: AigSignal) -> bool:
        """Returns whether this signal is ordered before another signal."""

    def __invert__(self) -> AigSignal:
        """Returns the complemented signal."""

    def __pos__(self) -> AigSignal:
        """Returns a normalized positive-phase signal."""

    def __neg__(self) -> AigSignal:
        """Returns a normalized negative-phase signal."""

    def __xor__(self, complement: bool) -> AigSignal:
        """XORs the signal phase with a Boolean complement bit.

        Args:
                complement: Complement bit to XOR with the current signal phase.

        Returns:
                A phase-adjusted signal.
        """

class Aig:
    """Represents an AIG and its structural operations.

    Note:
        to_index_list() keeps combinational structure only.
        Augmented view metadata is not preserved.
    """

    def __init__(self) -> None:
        """Creates an empty AIG network."""

    def clone(self) -> Aig:
        """Creates a structural copy of the network."""

    @property
    def size(self) -> int:
        """Number of nodes in the network."""

    @property
    def num_gates(self) -> int:
        """Number of logic gates in the network."""

    @property
    def num_pis(self) -> int:
        """Number of primary inputs."""

    @property
    def num_pos(self) -> int:
        """Number of primary outputs."""

    def get_node(self, s: AigSignal) -> int:
        """Returns the node referenced by a signal."""

    def make_signal(self, n: int) -> AigSignal:
        """Creates a signal from a node."""

    def is_complemented(self, s: AigSignal) -> bool:
        """Returns whether a signal is complemented."""

    def node_to_index(self, n: int) -> int:
        """Returns the integer index of a node."""

    def index_to_node(self, index: int) -> int:
        """Returns the node for an index."""

    def pi_index(self, n: int) -> int:
        """Returns the primary-input position of a node."""

    def pi_at(self, index: int) -> int:
        """Returns the primary input node at ``index``."""

    def po_index(self, s: AigSignal) -> int:
        """Returns the primary-output position of a signal."""

    def po_at(self, index: int) -> AigSignal:
        """Returns the primary output signal at ``index``."""

    def get_constant(self, value: bool) -> AigSignal:
        """Returns the constant signal for a Boolean value."""

    def create_pi(self) -> AigSignal:
        """Creates and returns a new primary input signal."""

    def create_po(self, f: AigSignal) -> int:
        """Creates a primary output from signal ``f``."""

    @property
    def is_combinational(self) -> bool:
        """Whether the network is combinational."""

    def create_buf(self, a: AigSignal) -> AigSignal:
        """Creates a buffer."""

    def create_not(self, a: AigSignal) -> AigSignal:
        """Creates an inversion."""

    def create_and(self, a: AigSignal, b: AigSignal) -> AigSignal:
        """Creates an AND."""

    def create_nand(self, a: AigSignal, b: AigSignal) -> AigSignal:
        """Creates a NAND."""

    def create_or(self, a: AigSignal, b: AigSignal) -> AigSignal:
        """Creates an OR."""

    def create_nor(self, a: AigSignal, b: AigSignal) -> AigSignal:
        """Creates a NOR."""

    def create_xor(self, a: AigSignal, b: AigSignal) -> AigSignal:
        """Creates an XOR."""

    def create_xnor(self, a: AigSignal, b: AigSignal) -> AigSignal:
        """Creates an XNOR."""

    def create_lt(self, a: AigSignal, b: AigSignal) -> AigSignal:
        """Creates a less-than comparator."""

    def create_le(self, a: AigSignal, b: AigSignal) -> AigSignal:
        """Creates a less-or-equal comparator."""

    def create_maj(self, a: AigSignal, b: AigSignal, c: AigSignal) -> AigSignal:
        """Creates a majority."""

    def create_ite(self, cond: AigSignal, f_then: AigSignal, f_else: AigSignal) -> AigSignal:
        """Creates an if-then-else."""

    def create_xor3(self, a: AigSignal, b: AigSignal, c: AigSignal) -> AigSignal:
        """Creates a 3-input XOR."""

    def create_nary_and(self, fs: Sequence[AigSignal]) -> AigSignal:
        """Creates an n-ary AND."""

    def create_nary_or(self, fs: Sequence[AigSignal]) -> AigSignal:
        """Creates an n-ary OR."""

    def create_nary_xor(self, fs: Sequence[AigSignal]) -> AigSignal:
        """Creates an n-ary XOR."""

    def clone_node(self, other: Aig, source: int, children: Sequence[AigSignal]) -> AigSignal:
        """Clones one node from ``other`` into this network."""

    def nodes(self) -> list[int]:
        """Returns a list of all nodes in order of creation."""

    def gates(self) -> list[int]:
        """Returns a list of all non-constant and non-PI nodes in order of creation."""

    def pis(self) -> list[int]:
        """Returns a list of all primary input nodes in order of creation."""

    def pos(self) -> list[AigSignal]:
        """Returns a list of all primary output signals in order of creation."""

    def fanins(self, n: int) -> list[AigSignal]:
        """Returns fanin signals of node ``n``."""

    def fanin_size(self, n: int) -> int:
        """Returns the number of fanins of node ``n``."""

    def fanout_size(self, n: int) -> int:
        """Returns the number of fanouts of node ``n``."""

    def is_constant(self, n: int) -> bool:
        """Returns whether ``n`` is a constant node."""

    def is_pi(self, n: int) -> bool:
        """Returns whether ``n`` is a primary input."""

    def has_and(self, a: AigSignal, b: AigSignal) -> AigSignal | None:
        """Returns whether an AND with fanins ``a`` and ``b`` already exists."""

    def is_and(self, n: int) -> bool:
        """Returns whether ``n`` is an AND node."""

    def is_or(self, n: int) -> bool:
        """Returns whether ``n`` is an OR node."""

    def is_xor(self, n: int) -> bool:
        """Returns whether ``n`` is an XOR node."""

    def is_maj(self, n: int) -> bool:
        """Returns whether ``n`` is a majority node."""

    def is_ite(self, n: int) -> bool:
        """Returns whether ``n`` is an if-then-else node."""

    def is_xor3(self, n: int) -> bool:
        """Returns whether ``n`` is a 3-input XOR node."""

    def is_nary_and(self, n: int) -> bool:
        """Returns whether ``n`` is an n-ary AND node."""

    def is_nary_or(self, n: int) -> bool:
        """Returns whether ``n`` is an n-ary OR node."""

    def to_edge_list(self, regular_weight: int = 0, inverted_weight: int = 1) -> AigEdgeList:
        """Converts the network to an edge list.

        Args:
            regular_weight: Weight assigned to non-inverted edges.
            inverted_weight: Weight assigned to inverted edges.

        Returns:
            The corresponding edge-list representation.
        """

    def to_index_list(self) -> AigIndexList:
        """Converts the network to an index-list encoding.

        Returns:
            The corresponding index-list representation.
        """

    def to_graph_tensors(
        self,
        node_encoding: NodeTensorEncoding = ...,
        edge_encoding: EdgeTensorEncoding = ...,
        include_level: bool = True,
        include_fanout: bool = False,
        include_truth_table: bool = False,
    ) -> dict:
        """Exports graph tensors for machine-learning workflows.

        Returns sparse graph topology and features as DLPack-compatible arrays.

        Edge encoding mapping:
            - ``BINARY``: regular=0.0, inverted=1.0
            - ``SIGNED``: regular=+1.0, inverted=-1.0
            - ``ONE_HOT``: regular=[1.0, 0.0], inverted=[0.0, 1.0]

        Node encoding mapping:
            - ``INTEGER``: constant=0, pi=1, gate=2, po=3
            - ``ONE_HOT``: [constant, pi, gate, po]

        Args:
            node_encoding: Node encoding mode as :class:`~aigverse.networks.NodeTensorEncoding`.
            edge_encoding: Edge encoding mode as :class:`~aigverse.networks.EdgeTensorEncoding`.
            include_level: Appends logic level as a node feature.
            include_fanout: Appends fanout size as a node feature.
            include_truth_table: Appends simulated node/output truth-table bits.

        Returns:
            A dictionary with ``edge_index`` (shape ``(2, E)``, dtype ``int64``),
            ``edge_attr`` (shape ``(E, D_edge)``, dtype ``float32``), and ``node_attr``
            (shape ``(N, D_node)``, dtype ``float32``).
        """

    def __len__(self) -> int:
        """Returns the number of nodes."""

    def __iter__(self) -> Iterator[int]:
        """Returns an iterator over all nodes."""

    def __contains__(self, value: object) -> bool:
        """Returns whether a node index is contained in the network."""

    def __bool__(self) -> bool:
        """Returns ``True`` for non-trivial networks."""

    def __copy__(self) -> Aig:
        """Returns a shallow structural copy."""

    def __deepcopy__(self, memo: dict) -> Aig:
        """Returns a deep structural copy."""

    def __setstate__(self, state: object) -> None:
        """Restores a network from a pickled state tuple.

        Args:
            state: Tuple containing one index-list payload.

        Raises:
            ValueError: If the state shape or payload is invalid.
        """

    def __getstate__(self) -> tuple:
        """Returns pickle state as an index-list tuple.

        Preserves only combinational structure and does not capture augmented view metadata.
        """

class NamedAig(Aig):
    """Extends a network with input/output and node names."""

    @overload
    def __init__(self) -> None:
        """Creates an empty named view."""

    @overload
    def __init__(self, ntk: NamedAig) -> None:
        """Copies from another named view."""

    @overload
    def __init__(self, ntk: Aig) -> None:
        """Creates a named view over an existing network."""

    def clone(self) -> NamedAig:
        """Creates a structural copy including names."""

    def __copy__(self) -> NamedAig:
        """Returns a shallow copy of the named view."""

    def __deepcopy__(self, memo: dict) -> NamedAig:
        """Returns a deep copy of the named view."""

    def create_pi(self, name: str = "") -> AigSignal:
        """Creates a primary input with an optional name."""

    def create_po(self, f: AigSignal, name: str = "") -> int:
        """Creates a primary output with an optional name."""

    def set_network_name(self, name: str) -> None:
        """Sets the network name."""

    def get_network_name(self) -> str:
        """Returns the network name."""

    def has_name(self, s: AigSignal) -> bool:
        """Returns whether signal ``s`` has a name."""

    def set_name(self, s: AigSignal, name: str) -> None:
        """Assigns a name to signal ``s``."""

    def get_name(self, s: AigSignal) -> str:
        """Returns the name of signal ``s``."""

    def has_output_name(self, index: int) -> bool:
        """Returns whether output ``index`` has a name."""

    def set_output_name(self, index: int, name: str) -> None:
        """Sets the name of output ``index``."""

    def get_output_name(self, index: int) -> str:
        """Returns the name of output ``index``."""

class DepthAig(Aig):
    """Extends a network with depth information."""

    @overload
    def __init__(self) -> None:
        """Creates an empty depth view."""

    @overload
    def __init__(self, ntk: DepthAig) -> None:
        """Copies from another depth view."""

    @overload
    def __init__(self, ntk: Aig) -> None:
        """Creates a depth view over an existing network."""

    def clone(self) -> DepthAig:
        """Creates a copy of the depth view."""

    def __copy__(self) -> DepthAig:
        """Returns a shallow copy of the depth view."""

    def __deepcopy__(self, memo: dict) -> DepthAig:
        """Returns a deep copy of the depth view."""

    @property
    def num_levels(self) -> int:
        """Current network depth in levels."""

    def level(self, n: int) -> int:
        """Returns the level of node ``n``."""

    def is_on_critical_path(self, n: int) -> bool:
        """Returns whether node ``n`` is on at least one critical path."""

    def update_levels(self) -> None:
        """Recomputes level information."""

    def create_po(self, f: AigSignal) -> int:
        """Creates an output and updates depth information."""

class FanoutAig(Aig):
    """Extends a network with fanout information."""

    @overload
    def __init__(self) -> None:
        """Creates an empty fanout view."""

    @overload
    def __init__(self, ntk: Aig) -> None:
        """Creates a fanout view over an existing network."""

    @overload
    def __init__(self, ntk: FanoutAig) -> None:
        """Copies from another fanout view."""

    def clone(self) -> FanoutAig:
        """Creates a structural copy of the fanout view."""

    def __copy__(self) -> FanoutAig:
        """Returns a shallow copy of the fanout view."""

    def __deepcopy__(self, memo: dict) -> FanoutAig:
        """Returns a deep copy of the fanout view."""

    def fanouts(self, n: int) -> list[int]:
        """Returns fanout nodes of node ``n``."""

class AigRegister:
    """Represents metadata for one sequential register."""

    @overload
    def __init__(self) -> None:
        """Creates a default register descriptor."""

    @overload
    def __init__(self, register: AigRegister) -> None:
        """Copies a register descriptor."""

    @property
    def control(self) -> str:
        """Optional control signal."""

    @control.setter
    def control(self, arg: str, /) -> None: ...
    @property
    def init(self) -> int:
        """Initial value of the register."""

    @init.setter
    def init(self, arg: int, /) -> None: ...
    @property
    def type(self) -> str:
        """Register type/category."""

    @type.setter
    def type(self, arg: str, /) -> None: ...

class SequentialAig(Aig):
    """Represents a sequential network with register interfaces."""

    def __init__(self) -> None:
        """Creates an empty sequential network."""

    def clone(self) -> SequentialAig:
        """Creates a structural copy of the sequential network."""

    def __copy__(self) -> SequentialAig:
        """Returns a shallow copy of the sequential network."""

    def __deepcopy__(self, memo: dict) -> SequentialAig:
        """Returns a deep copy of the sequential network."""

    def create_pi(self) -> AigSignal:
        """Creates a primary input."""

    def create_po(self, f: AigSignal) -> int:
        """Creates a primary output."""

    def create_ro(self) -> AigSignal:
        """Creates a register output node."""

    def create_ri(self, f: AigSignal) -> int:
        """Creates a register input signal."""

    @property
    def is_combinational(self) -> bool:
        """Whether the network is combinational."""

    def is_ci(self, n: int) -> bool:
        """Returns whether ``n`` is a combinational input."""

    def is_pi(self, n: int) -> bool:
        """Returns whether ``n`` is a primary input."""

    def is_ro(self, n: int) -> bool:
        """Returns whether ``n`` is a register output."""

    @property
    def num_pis(self) -> int:
        """Number of primary inputs."""

    @property
    def num_pos(self) -> int:
        """Number of primary outputs."""

    @property
    def num_cis(self) -> int:
        """Number of combinational inputs."""

    @property
    def num_cos(self) -> int:
        """Number of combinational outputs."""

    @property
    def num_registers(self) -> int:
        """Number of registers."""

    def pi_at(self, index: int) -> int:
        """Returns primary input at ``index``."""

    def po_at(self, index: int) -> AigSignal:
        """Returns primary output at ``index``."""

    def ci_at(self, index: int) -> int:
        """Returns combinational input at ``index``."""

    def co_at(self, index: int) -> AigSignal:
        """Returns combinational output at ``index``."""

    def ro_at(self, index: int) -> int:
        """Returns register output at ``index``."""

    def ri_at(self, index: int) -> AigSignal:
        """Returns register input at ``index``."""

    def set_register(self, index: int, reg: AigRegister) -> None:
        """Sets metadata for register ``index``."""

    def register_at(self, index: int) -> AigRegister:
        """Returns metadata for register ``index``."""

    def pi_index(self, n: int) -> int:
        """Returns PI index of node ``n``."""

    def ci_index(self, n: int) -> int:
        """Returns CI index of node ``n``."""

    def co_index(self, s: AigSignal) -> int:
        """Returns CO index of signal ``s``."""

    def ro_index(self, n: int) -> int:
        """Returns RO index of node ``n``."""

    def ri_index(self, s: AigSignal) -> int:
        """Returns RI index of signal ``s``."""

    def ro_to_ri(self, s: AigSignal) -> AigSignal:
        """Maps a register output signal to its input."""

    def ri_to_ro(self, s: AigSignal) -> int:
        """Maps a register input signal to its output."""

    def to_index_list(self) -> NoReturn:
        """Sequential networks cannot be encoded as combinational index lists."""

    def to_graph_tensors(
        self,
        node_encoding: NodeTensorEncoding = ...,
        edge_encoding: EdgeTensorEncoding = ...,
        include_level: bool = True,
        include_fanout: bool = False,
        include_truth_table: bool = False,
    ) -> NoReturn:
        """Sequential networks cannot be exported as combinational graph tensors."""

    def __getstate__(self) -> NoReturn:
        """Sequential networks are not pickleable via combinational index-list state."""

    def __setstate__(self, state: object) -> NoReturn:
        """Sequential networks cannot be restored from combinational index-list state."""

    def to_edge_list(self, regular_weight: int = 0, inverted_weight: int = 1) -> AigEdgeList:
        """Converts the sequential network to an edge list."""

    def pis(self) -> list[int]:
        """Returns all primary input nodes."""

    def pos(self) -> list[AigSignal]:
        """Returns all primary output signals."""

    def cis(self) -> list[int]:
        """Returns all combinational input nodes."""

    def cos(self) -> list[AigSignal]:
        """Returns all combinational output signals."""

    def ros(self) -> list[int]:
        """Returns all register output nodes."""

    def ris(self) -> list[AigSignal]:
        """Returns all register input signals."""

    def registers(self) -> list[tuple[AigSignal, int]]:
        """Returns all register pairs as ``(ri_signal, ro_node)`` tuples."""

class AigEdge:
    """Represents a directed edge in a logic network graph. A weight attribute may encode inversion."""

    @overload
    def __init__(self) -> None:
        """Creates an empty edge.

        The default edge has zero-initialized endpoints and weight.
        """

    @overload
    def __init__(self, source: int, target: int, weight: int = 0) -> None:
        """Creates an edge with explicit source, target, and weight.

        Args:
            source: Source node identifier.
            target: Target node identifier.
            weight: Optional edge weight. Defaults to ``0``.
        """

    @property
    def source(self) -> int:
        """Source node identifier."""

    @source.setter
    def source(self, arg: int, /) -> None: ...
    @property
    def target(self) -> int:
        """Target node identifier."""

    @target.setter
    def target(self, arg: int, /) -> None: ...
    @property
    def weight(self) -> int:
        """Edge weight value."""

    @weight.setter
    def weight(self, arg: int, /) -> None: ...
    def __eq__(self, other: object) -> bool:
        """Checks whether two edges are equal.

        Args:
            other: Object to compare.

        Returns:
            ``True`` if ``other`` is an edge with equal fields, otherwise ``False``.
        """

    def __ne__(self, other: object) -> bool:
        """Checks whether two edges are not equal.

        Args:
            other: Object to compare.

        Returns:
            ``True`` if ``other`` is not equal to this edge.
        """

class AigEdgeList:
    """Represents a list of edges associated with a network."""

    @overload
    def __init__(self) -> None:
        """Creates an empty edge list."""

    @overload
    def __init__(self, ntk: Aig) -> None:
        """Creates an edge list for a given network.

        Args:
            ntk: Network associated with the edge list.
        """

    @overload
    def __init__(self, edges: Sequence[AigEdge]) -> None:
        """Creates an edge list from existing edges.

        Args:
            edges: Initial edge collection.
        """

    @overload
    def __init__(self, ntk: Aig, edges: Sequence[AigEdge]) -> None:
        """Creates an edge list with network and edge collection.

        Args:
            ntk: Network associated with the edge list.
            edges: Initial edge collection.
        """

    @property
    def ntk(self) -> Aig:
        """Underlying network associated with this list."""

    @ntk.setter
    def ntk(self, arg: Aig, /) -> None: ...
    @property
    def edges(self) -> list[AigEdge]:
        """Stored edges in insertion order."""

    @edges.setter
    def edges(self, arg: Sequence[AigEdge], /) -> None: ...
    def append(self, edge: AigEdge) -> None:
        """Appends an edge to the list.

        Args:
            edge: Edge to append.
        """

    def clear(self) -> None:
        """Removes all edges from the list."""

    def __iter__(self) -> Iterator[AigEdge]:
        """Returns an iterator over stored edges."""

    def __len__(self) -> int:
        """Returns the number of edges."""

    def __getitem__(self, index: int) -> AigEdge:
        """Returns the edge at a given position.

        Args:
            index: Edge index. Negative indices are supported.

        Returns:
            The edge at the requested position.

        Raises:
            IndexError: If ``index`` is out of bounds.
        """

    def __setitem__(self, index: int, edge: AigEdge) -> None:
        """Replaces the edge at a given position.

        Args:
            index: Edge index. Negative indices are supported.
            edge: Replacement edge.

        Raises:
            IndexError: If ``index`` is out of bounds.
        """

class AigIndexList:
    """Represents an index-list encoding of an AIG network."""

    @overload
    def __init__(self, num_pis: int = 0) -> None:
        """Creates an empty index list with a given number of primary inputs.

        Args:
            num_pis: Number of primary inputs to initialize.
        """

    @overload
    def __init__(self, values: Sequence[int]) -> None:
        """Creates an index list from raw integer values.

        Args:
            values: Raw index-list encoding values.
        """

    def raw(self) -> list[int]:
        """Returns the raw integer encoding.

        Returns:
            A list of encoded index-list values.
        """

    @property
    def size(self) -> int:
        """Number of raw entries in the encoding."""

    @property
    def num_gates(self) -> int:
        """Number of encoded gates."""

    @property
    def num_pis(self) -> int:
        """Number of encoded primary inputs."""

    @property
    def num_pos(self) -> int:
        """Number of encoded primary outputs."""

    def add_inputs(self, n: int = 1) -> None:
        """Appends primary inputs to the encoding.

        Args:
            n: Number of inputs to append.
        """

    def add_and(self, lit0: int, lit1: int) -> int:
        """Appends an AND gate to the encoding.

        Args:
            lit0: First fanin literal.
            lit1: Second fanin literal.
        """

    def add_xor(self, lit0: int, lit1: int) -> int:
        """Appends an XOR gate to the encoding.

        Args:
            lit0: First fanin literal.
            lit1: Second fanin literal.
        """

    def add_output(self, lit: int) -> None:
        """Appends a primary output literal.

        Args:
            lit: Output literal.
        """

    def clear(self) -> None:
        """Clears all encoded data."""

    def to_aig(self) -> Aig:
        """Decodes the index list into an AIG network.

        Returns:
            A decoded AIG network.
        """

    def gates(self) -> list[tuple[int, int]]:
        """Returns encoded gate fanins as literal pairs.

        Returns:
            A list of ``(lit0, lit1)`` tuples for each gate.
        """

    def pos(self) -> list[int]:
        """Returns encoded primary output literals.

        Returns:
            A list of output literals.
        """

    def __iter__(self) -> Iterator[int]:
        """Returns an iterator over the raw encoding values."""

    def __getitem__(self, index: int) -> int:
        """Returns one raw encoding value by index.

        Args:
            index: Position in the raw encoding.

        Returns:
            The raw value at ``index``.

        Raises:
            IndexError: If ``index`` is out of range.
        """

    def __setitem__(self, index: int, value: int) -> None:
        """Sets one raw encoding value by index.

        Args:
                index: Position in the raw encoding.
                value: Replacement raw value.

        Raises:
                IndexError: If ``index`` is out of range.
        """

    def __len__(self) -> int:
        """Returns the number of raw encoding entries."""
