from typing import Literal

from .. import networks, utils

def equivalence_checking(
    spec: networks.Aig,
    impl: networks.Aig,
    conflict_limit: int = 0,
    functional_reduction: bool = True,
    verbose: bool = False,
) -> bool | None: ...
def sop_refactoring(
    ntk: networks.Aig,
    max_pis: int = 6,
    allow_zero_gain: bool = False,
    use_reconvergence_cut: bool = False,
    use_dont_cares: bool = False,
    verbose: bool = False,
) -> None: ...
def aig_resubstitution(
    ntk: networks.Aig,
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
    ntk: networks.Aig,
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
    ntk: networks.Aig,
    cut_size: int = 4,
    cut_limit: int = 8,
    minimize_truth_table: bool = True,
    only_on_critical_path: bool = False,
    rebalance_function: Literal["sop", "esop"] = "sop",
    sop_both_phases: bool = True,
    verbose: bool = False,
) -> None: ...
def simulate(ntk: networks.Aig) -> list[utils.TruthTable]: ...
def simulate_nodes(ntk: networks.Aig) -> dict[int, utils.TruthTable]: ...
