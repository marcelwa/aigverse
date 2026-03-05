"""Synthesis and optimization algorithms."""

import aigverse.networks
import aigverse.utils

def equivalence_checking(
    spec: aigverse.networks.Aig,
    impl: aigverse.networks.Aig,
    conflict_limit: int = 0,
    functional_reduction: bool = True,
    verbose: bool = False,
) -> bool | None: ...
def sop_refactoring(
    ntk: aigverse.networks.Aig,
    max_pis: int = 6,
    allow_zero_gain: bool = False,
    use_reconvergence_cut: bool = False,
    use_dont_cares: bool = False,
    use_quick_factoring: bool = True,
    try_both_polarities: bool = True,
    consider_inverter_cost: bool = False,
    verbose: bool = False,
) -> None: ...
def aig_resubstitution(
    ntk: aigverse.networks.Aig,
    max_pis: int = 8,
    max_divisors: int = 150,
    max_inserts: int = 2,
    skip_fanout_limit_for_roots: int = 1000,
    skip_fanout_limit_for_divisors: int = 100,
    verbose: bool = False,
    use_dont_cares: bool = False,
    window_size: int = 12,
    preserve_depth: bool = False,
) -> None: ...
def aig_cut_rewriting(
    ntk: aigverse.networks.Aig,
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
) -> None: ...
def balancing(
    ntk: aigverse.networks.Aig,
    cut_size: int = 4,
    cut_limit: int = 8,
    minimize_truth_table: bool = True,
    only_on_critical_path: bool = False,
    rebalance_function: str = "sop",
    sop_both_phases: bool = True,
    verbose: bool = False,
) -> None: ...
def simulate(ntk: aigverse.networks.Aig) -> list[aigverse.utils.TruthTable]: ...
def simulate_nodes(ntk: aigverse.networks.Aig) -> dict[int, aigverse.utils.TruthTable]: ...
