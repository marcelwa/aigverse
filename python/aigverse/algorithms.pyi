"""Provides synthesis and optimization algorithms for logic network types."""

from collections.abc import Sequence
from typing import Literal, overload

import aigverse.networks
import aigverse.utils

@overload
def equivalence_checking(
    spec: aigverse.networks.Aig,
    impl: aigverse.networks.Aig,
    *,
    conflict_limit: int = 0,
    functional_reduction: bool = True,
    verbose: bool = False,
) -> bool | None: ...
@overload
def equivalence_checking(
    spec: aigverse.networks.Aig,
    impl: aigverse.networks.Klut,
    *,
    conflict_limit: int = 0,
    functional_reduction: bool = True,
    verbose: bool = False,
) -> bool | None: ...
@overload
def equivalence_checking(
    spec: aigverse.networks.Klut,
    impl: aigverse.networks.Aig,
    *,
    conflict_limit: int = 0,
    functional_reduction: bool = True,
    verbose: bool = False,
) -> bool | None: ...
@overload
def equivalence_checking(
    spec: aigverse.networks.Klut,
    impl: aigverse.networks.Klut,
    *,
    conflict_limit: int = 0,
    functional_reduction: bool = True,
    verbose: bool = False,
) -> bool | None:
    """Checks functional equivalence between a specification and implementation network using SAT solving.

    LUT fanin checks include dangling gates. The fewer-than-32-fanin bound is a representation limit,
    not a practical resource limit: LUT truth tables and ISOP/CNF construction can require exponential space and time.

    Args:
        spec: The specification network.
        impl: The implementation network.
        conflict_limit: SAT conflict limit. A value of ``0`` means no limit.
        functional_reduction: Whether to perform functional reduction of an AIG/AIG miter before checking.
            Native functional reduction is not applied when either input is a Klut.
        verbose: Whether to print verbose progress output.

    Returns:
        ``True`` if equivalent, ``False`` if not equivalent, or ``None`` if the
        procedure did not finish before the configured limit.

    Raises:
        ValueError: For Aig/Klut or Klut/Klut comparisons, if an input is sequential or any LUT has 32 or more fanins.
        RuntimeError: If miter construction fails due to incompatible interfaces (PI/PO count mismatch).
    """

@overload
def cleanup_dangling(
    ntk: aigverse.networks.Aig, *, remove_dangling_pis: bool = False, remove_redundant_pos: bool = False
) -> aigverse.networks.Aig: ...
@overload
def cleanup_dangling(
    ntk: aigverse.networks.NamedKlut, *, remove_dangling_pis: bool = False, remove_redundant_pos: bool = False
) -> aigverse.networks.NamedKlut: ...
@overload
def cleanup_dangling(
    ntk: aigverse.networks.Klut, *, remove_dangling_pis: bool = False, remove_redundant_pos: bool = False
) -> aigverse.networks.Klut:
    """Removes dangling logic (dead nodes) from a network.

    Args:
        ntk: The input logic network.
        remove_dangling_pis: Whether to also remove primary inputs with no fanouts in the input network.
        remove_redundant_pos: Whether to remove outputs driven directly by primary inputs or constants.

    Returns:
        A cleaned network with dangling structures removed.
    """

def sop_refactoring(
    ntk: aigverse.networks.Aig,
    *,
    max_pis: int = 6,
    allow_zero_gain: bool = False,
    use_reconvergence_cut: bool = False,
    use_dont_cares: bool = False,
    use_quick_factoring: bool = True,
    try_both_polarities: bool = True,
    consider_inverter_cost: bool = False,
    verbose: bool = False,
    inplace: bool = False,
) -> aigverse.networks.Aig | None:
    """Performs SOP-based network refactoring.

    Args:
        ntk: The input logic network.
        max_pis: Maximum number of leaves used in local windows.
        allow_zero_gain: Whether substitutions with zero gain are allowed.
        use_reconvergence_cut: Whether to use reconvergence-driven cuts.
        use_dont_cares: Whether to use don't-care information.
        use_quick_factoring: Whether to use the quick SOP factoring heuristic.
        try_both_polarities: Whether both output polarities are explored.
        consider_inverter_cost: Whether inverter cost is included in optimization.
        verbose: Whether to print verbose progress output.
        inplace: Whether to mutate ``ntk`` in place. A network being transformed in place
            must not be shared with another thread.

    Returns:
        The refactored network if ``inplace`` is ``False``. Otherwise ``None``.

    Raises:
        RuntimeError: If refactoring fails in the underlying synthesis engine.
    """

def aig_resubstitution(
    ntk: aigverse.networks.Aig,
    *,
    max_pis: int = 8,
    max_divisors: int = 150,
    max_inserts: int = 2,
    skip_fanout_limit_for_roots: int = 1000,
    skip_fanout_limit_for_divisors: int = 100,
    verbose: bool = False,
    use_dont_cares: bool = False,
    window_size: int = 12,
    preserve_depth: bool = False,
    inplace: bool = False,
) -> aigverse.networks.Aig | None:
    """Performs AIG resubstitution-based optimization.

    Args:
        ntk: The input logic network.
        max_pis: Maximum number of leaves in a local window.
        max_divisors: Maximum number of candidate divisors.
        max_inserts: Maximum number of inserted nodes per replacement.
        skip_fanout_limit_for_roots: Fanout threshold to skip root candidates.
        skip_fanout_limit_for_divisors: Fanout threshold to skip divisor candidates.
        verbose: Whether to print verbose progress output.
        use_dont_cares: Whether to use don't-care information.
        window_size: Window size used for don't-care computation.
        preserve_depth: Whether replacements must preserve depth.
        inplace: Whether to mutate ``ntk`` in place. A network being transformed in place
            must not be shared with another thread.

    Returns:
        The optimized network if ``inplace`` is ``False``. Otherwise ``None``.
    """

def aig_cut_rewriting(
    ntk: aigverse.networks.Aig,
    *,
    cut_size: int = 4,
    cut_limit: int = 8,
    minimize_truth_table: bool = True,
    allow_zero_gain: bool = False,
    use_dont_cares: bool = False,
    min_cand_cut_size: int = 3,
    min_cand_cut_size_override: int | None = None,
    preserve_depth: bool = False,
    verbose: bool = False,
    very_verbose: bool = False,
) -> aigverse.networks.Aig:
    """Rewrites an AIG network using cut-based NPN resynthesis.

    Args:
        ntk: The input logic network.
        cut_size: Maximum cut size used during cut enumeration.
        cut_limit: Maximum number of cuts retained per node.
        minimize_truth_table: Whether to minimize cut truth tables.
        allow_zero_gain: Whether replacements with zero gain are allowed.
        use_dont_cares: Whether to use don't-care information.
        min_cand_cut_size: Minimum candidate cut size.
        min_cand_cut_size_override: Optional override for minimum candidate cut size.
        preserve_depth: Whether replacements must preserve network depth.
        verbose: Whether to print verbose progress output.
        very_verbose: Whether to print highly detailed progress output.

    Returns:
        A rewritten network.
    """

def balancing(
    ntk: aigverse.networks.Aig,
    *,
    cut_size: int = 4,
    cut_limit: int = 8,
    minimize_truth_table: bool = True,
    only_on_critical_path: bool = False,
    rebalance_function: Literal["sop", "esop"] = "sop",
    sop_both_phases: bool = True,
    verbose: bool = False,
) -> aigverse.networks.Aig:
    """Balances a network using SOP or ESOP-based local restructuring.

    Args:
        ntk: The input logic network.
        cut_size: Maximum cut size used during cut enumeration.
        cut_limit: Maximum number of cuts retained per node.
        minimize_truth_table: Whether to minimize cut truth tables during enumeration.
        only_on_critical_path: Whether to balance only nodes on the critical path.
        rebalance_function: Rebalancing engine to use. Supported values are
            ``"sop"`` and ``"esop"``.
        sop_both_phases: Whether to consider both phases in SOP/ESOP balancing.
        verbose: Whether to print verbose progress output.

    Returns:
        A new balanced network.

    Raises:
        ValueError: If ``rebalance_function`` is not one of the supported values.
    """

@overload
def simulate(ntk: aigverse.networks.Aig) -> list[aigverse.utils.TruthTable]: ...
@overload
def simulate(ntk: aigverse.networks.Klut) -> list[aigverse.utils.TruthTable]:
    """Simulates all primary outputs of a network as truth tables.

    The GIL is released while reading the live network. The caller must not mutate it concurrently.

    Args:
        ntk: The input logic network.

    Returns:
        A list containing one truth table per primary output.

    Raises:
        ValueError: If there are 32 or more primary inputs.
        MemoryError: If the truth tables cannot be allocated due to memory limits.
    """

@overload
def simulate_nodes(ntk: aigverse.networks.Aig) -> dict[int, aigverse.utils.TruthTable]: ...
@overload
def simulate_nodes(ntk: aigverse.networks.Klut) -> dict[int, aigverse.utils.TruthTable]:
    """Simulates all nodes of a network as truth tables.

    The GIL is released while reading the live network. The caller must not mutate it concurrently.

    Args:
        ntk: The input logic network.

    Returns:
        A dictionary that maps node identifiers to truth tables.

    Raises:
        ValueError: If there are 32 or more primary inputs.
        MemoryError: If the truth tables cannot be allocated due to memory limits.
    """

class SequentialSimulationResult:
    """Represents the outcome of simulating a sequential network over several clock cycles.

    Both traces are indexed by clock cycle first: ``outputs[cycle][index]`` is the value primary
    output ``index`` took in that cycle, and ``states[cycle][index]`` the value register ``index``
    held while that cycle was evaluated.

    ``states`` is one entry longer than ``outputs``, because simulating ``n`` cycles crosses
    ``n + 1`` state boundaries. The first is the reset state the run started from and the last is
    the state it ended in.
    """

    @property
    def outputs(self) -> list[list[bool]]:
        """Primary output values, one list per clock cycle."""

    @property
    def states(self) -> list[list[bool]]:
        """Register values, one list per state boundary."""

    @property
    def num_cycles(self) -> int:
        """Number of clock cycles simulated."""

    @property
    def reset_state(self) -> list[bool]:
        """The state the registers were reset to."""

    @property
    def final_state(self) -> list[bool]:
        """The state the registers held after the last cycle."""

    def __len__(self) -> int: ...

def simulate_sequential(
    ntk: aigverse.networks.SequentialAig,
    num_cycles: int,
    stimulus: Sequence[Sequence[bool]] = [],
    undefined_reset_value: bool = False,
) -> SequentialSimulationResult:
    """Simulates a sequential network over a number of clock cycles.

    Every register starts at its reset value, the combinational logic is evaluated once per
    cycle, the primary outputs are recorded, and the register inputs are latched into the
    register outputs for the next cycle.

    This is what distinguishes it from :func:`~aigverse.algorithms.simulate`, which evaluates
    the combinational logic exactly once and has no notion of a register.

    Args:
        ntk: The sequential network to simulate.
        num_cycles: Number of clock cycles to run.
        stimulus: Primary input assignments, one list of ``ntk.num_pis`` values per clock cycle.
            Cycles past the end of the stimulus repeat its last assignment, so a single
            assignment holds for the whole run. Defaults to holding every primary input at
            ``False``, which is all a design without primary inputs needs.
        undefined_reset_value: Value a register starts at when its reset value is undefined,
            which is what a register defaults to and what an AIGER latch with a
            nondeterministic reset reads back as.

    Returns:
        The primary output values and the register values, per clock cycle.

    Raises:
        ValueError: If an assignment in ``stimulus`` does not have one value per primary input.
    """

@overload
def lut_mapping(
    ntk: aigverse.networks.NamedAig,
    *,
    algorithm: Literal["heuristic", "classic", "sat", "sat_windowed"] = "heuristic",
    cut_size: int = 6,
    cut_limit: int = 8,
    area_oriented_mapping: bool | None = None,
    area_flow_rounds: int = 1,
    ela_rounds: int | None = None,
    verbose: bool = False,
    compute_truth: bool | None = None,
    minimize_truth_table: bool | None = None,
    required_delay: int | None = None,
    relax_required: int | None = None,
    recompute_cuts: bool | None = None,
    area_share_rounds: int | None = None,
    edge_optimization: bool | None = None,
    cut_expansion: bool | None = None,
    remove_dominated_cuts: bool | None = None,
    conflict_limit: int | None = None,
    window_size: int | None = None,
) -> aigverse.networks.NamedKlut:
    """Maps a combinational AIG to a fresh k-LUT network, preserving its interface.

    Args:
        ntk: The AIG to map. NamedAig produces NamedKlut with PI/PO names and order preserved.
        algorithm: ``"heuristic"`` (default), ``"classic"``, ``"sat"``, or ``"sat_windowed"``.
            SAT modes improve a classic seed on the original AIG before collapsing it.
        cut_size: Maximum LUT fanin count, from 2 to 16.
        cut_limit: Retained nontrivial cuts per node, from 1 to 31 for heuristic or 1 to 24 otherwise.
        area_oriented_mapping: Defaults to False for heuristic, True otherwise. Only heuristic supports False.
        area_flow_rounds: Additional area-flow passes after initialization, nonnegative.
        ela_rounds: Exact local area passes, nonnegative. Defaults to 2 for heuristic, 1 otherwise.
        verbose: Whether to print native progress information.
        compute_truth: Heuristic only; compute cut truth tables during mapping (default False).
            Every returned LUT has its truth table regardless of this setting.
        minimize_truth_table: Heuristic only; minimize cut support. Defaults to compute_truth;
            True requires compute_truth=True.
        required_delay: Heuristic only; absolute depth target (default 0, no target).
        relax_required: Heuristic only; percentage depth relaxation (default 0).
            Extreme values are rejected using the input gate count as a conservative bound on depth.
            Timing controls require delay orientation and cannot both be positive. They are heuristic targets.
        recompute_cuts: Heuristic only; recompute cuts at each pass (default True).
        area_share_rounds: Heuristic only; backward area-sharing passes (default 2).
        edge_optimization: Heuristic only; reduce LUT input edges (default True).
        cut_expansion: Heuristic only; expand cuts. Defaults to True only with recompute_cuts=True
            and compute_truth=False; explicitly enabling it otherwise is invalid.
        remove_dominated_cuts: Heuristic only; discard contained cuts (default True).
        conflict_limit: SAT modes only; conflicts per solve (default 10000, 0 means unlimited), at most INT_MAX.
            This is neither a cumulative resource limit nor an optimality certificate.
        window_size: sat_windowed only; positive maximum number of original-network gates per window (default 32).
            Cells whose mandatory pivot cone exceeds this limit are skipped, so the classic seed may be retained.

    Returns:
        An independent Klut, or NamedKlut for NamedAig. The input is unchanged.
        SAT minimizes native mapped-cell count, which can differ from the materialized Klut gate count.

    Raises:
        TypeError: If an integer control is outside the signed 64-bit range accepted by the binding.
        ValueError: If the input is sequential, a control is out of range, or controls are incompatible.
    """

@overload
def lut_mapping(
    ntk: aigverse.networks.Aig,
    *,
    algorithm: Literal["heuristic", "classic", "sat", "sat_windowed"] = "heuristic",
    cut_size: int = 6,
    cut_limit: int = 8,
    area_oriented_mapping: bool | None = None,
    area_flow_rounds: int = 1,
    ela_rounds: int | None = None,
    verbose: bool = False,
    compute_truth: bool | None = None,
    minimize_truth_table: bool | None = None,
    required_delay: int | None = None,
    relax_required: int | None = None,
    recompute_cuts: bool | None = None,
    area_share_rounds: int | None = None,
    edge_optimization: bool | None = None,
    cut_expansion: bool | None = None,
    remove_dominated_cuts: bool | None = None,
    conflict_limit: int | None = None,
    window_size: int | None = None,
) -> aigverse.networks.Klut:
    """Maps a combinational AIG to a fresh k-LUT network, preserving its interface.

    Args:
        ntk: The AIG to map. NamedAig produces NamedKlut with PI/PO names and order preserved.
        algorithm: ``"heuristic"`` (default), ``"classic"``, ``"sat"``, or ``"sat_windowed"``.
            SAT modes improve a classic seed on the original AIG before collapsing it.
        cut_size: Maximum LUT fanin count, from 2 to 16.
        cut_limit: Retained nontrivial cuts per node, from 1 to 31 for heuristic or 1 to 24 otherwise.
        area_oriented_mapping: Defaults to False for heuristic, True otherwise. Only heuristic supports False.
        area_flow_rounds: Additional area-flow passes after initialization, nonnegative.
        ela_rounds: Exact local area passes, nonnegative. Defaults to 2 for heuristic, 1 otherwise.
        verbose: Whether to print native progress information.
        compute_truth: Heuristic only; compute cut truth tables during mapping (default False).
            Every returned LUT has its truth table regardless of this setting.
        minimize_truth_table: Heuristic only; minimize cut support. Defaults to compute_truth;
            True requires compute_truth=True.
        required_delay: Heuristic only; absolute depth target (default 0, no target).
        relax_required: Heuristic only; percentage depth relaxation (default 0).
            Extreme values are rejected using the input gate count as a conservative bound on depth.
            Timing controls require delay orientation and cannot both be positive. They are heuristic targets.
        recompute_cuts: Heuristic only; recompute cuts at each pass (default True).
        area_share_rounds: Heuristic only; backward area-sharing passes (default 2).
        edge_optimization: Heuristic only; reduce LUT input edges (default True).
        cut_expansion: Heuristic only; expand cuts. Defaults to True only with recompute_cuts=True
            and compute_truth=False; explicitly enabling it otherwise is invalid.
        remove_dominated_cuts: Heuristic only; discard contained cuts (default True).
        conflict_limit: SAT modes only; conflicts per solve (default 10000, 0 means unlimited), at most INT_MAX.
            This is neither a cumulative resource limit nor an optimality certificate.
        window_size: sat_windowed only; positive maximum number of original-network gates per window (default 32).
            Cells whose mandatory pivot cone exceeds this limit are skipped, so the classic seed may be retained.

    Returns:
        An independent Klut, or NamedKlut for NamedAig. The input is unchanged.
        SAT minimizes native mapped-cell count, which can differ from the materialized Klut gate count.

    Raises:
        TypeError: If an integer control is outside the signed 64-bit range accepted by the binding.
        ValueError: If the input is sequential, a control is out of range, or controls are incompatible.
    """

@overload
def convert_klut_to_aig(ntk: aigverse.networks.NamedKlut) -> aigverse.networks.NamedAig: ...
@overload
def convert_klut_to_aig(ntk: aigverse.networks.Klut) -> aigverse.networks.Aig:
    """Resynthesizes a k-LUT network into an independent AIG.

    Args:
        ntk: The input k-LUT network, which is left unchanged.

    Returns:
        An Aig, or NamedAig for NamedKlut, preserving primary input/output order and names.
        Native disjoint-support and Shannon decomposition with NPN resynthesis implement the conversion.
    """
