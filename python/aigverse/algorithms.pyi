"""Provides synthesis and optimization algorithms for logic network types."""

from typing import Literal

import aigverse.networks
import aigverse.utils

def equivalence_checking(
    spec: aigverse.networks.Aig,
    impl: aigverse.networks.Aig,
    *,
    conflict_limit: int = 0,
    functional_reduction: bool = True,
    verbose: bool = False,
) -> bool | None:
    """Checks functional equivalence between a specification and implementation network using SAT solving.

    Args:
        spec: The specification network.
        impl: The implementation network.
        conflict_limit: SAT conflict limit. A value of ``0`` means no limit.
        functional_reduction: Whether to perform functional reduction of the miter before checking.
        verbose: Whether to print verbose progress output.

    Returns:
        ``True`` if equivalent, ``False`` if not equivalent, or ``None`` if the
        procedure did not finish before the configured limit.

    Raises:
        RuntimeError: If miter construction fails due to incompatible interfaces (PI/PO count mismatch).
    """

def cleanup_dangling(
    ntk: aigverse.networks.Aig, *, remove_dangling_pis: bool = False, remove_redundant_pos: bool = False
) -> aigverse.networks.Aig:
    """Removes dangling logic (dead nodes) from a network.

    Args:
        ntk: The input logic network.
        remove_dangling_pis: Whether to also remove dangling primary inputs.
        remove_redundant_pos: Whether to remove redundant primary outputs.

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
        inplace: Whether to mutate ``ntk`` in place.

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
        inplace: Whether to mutate ``ntk`` in place.

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

def simulate(ntk: aigverse.networks.Aig) -> list[aigverse.utils.TruthTable]:
    """Simulates all primary outputs of a network as truth tables.

    Args:
        ntk: The input logic network.

    Returns:
        A list containing one truth table per primary output.

    Raises:
        MemoryError: If the truth tables cannot be allocated due to memory limits.
    """

def simulate_nodes(ntk: aigverse.networks.Aig) -> dict[int, aigverse.utils.TruthTable]:
    """Simulates all nodes of a network as truth tables.

    Args:
        ntk: The input logic network.

    Returns:
        A dictionary that maps node identifiers to truth tables.

    Raises:
        MemoryError: If the truth tables cannot be allocated due to memory limits.
    """
