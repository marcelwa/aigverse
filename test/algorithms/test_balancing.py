from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aigverse.algorithms import balancing
from aigverse.networks import DepthAig

if TYPE_CHECKING:
    from collections.abc import Callable

    from aigverse.networks import Aig


def _depth(aig: Aig) -> int:
    view = DepthAig(aig)
    return view.num_levels


def test_balancing_on_simple_balanced_aig(make_and_chain_aig: Callable[[int], Aig]) -> None:
    """Test balancing on an already simple balanced AIG preserves its structure."""
    aig = make_and_chain_aig(3)

    num_pis_before = aig.num_pis
    num_pos_before = aig.num_pos
    num_gates_before = aig.num_gates
    depth_before = _depth(aig)

    aig = balancing(aig)

    assert aig.num_pis == num_pis_before
    assert aig.num_pos == num_pos_before
    assert aig.num_gates == num_gates_before, (
        f"Gate count changed for a balanced AIG: before {num_gates_before}, after {aig.num_gates}"
    )
    depth_after = _depth(aig)
    assert depth_after == depth_before, f"Depth changed for a balanced AIG: before {depth_before}, after {depth_after}"

    # Test balancing with non-default parameters
    cloned_aig_base = aig.clone()
    aig_params_test = cloned_aig_base

    # Re-fetch original properties from the new DepthAig instance
    num_pis_before_clone = aig_params_test.num_pis
    num_pos_before_clone = aig_params_test.num_pos
    num_gates_before_clone = aig_params_test.num_gates
    depth_before_clone = _depth(aig_params_test)

    aig_params_test = balancing(
        aig_params_test,
        cut_size=6,
        cut_limit=10,
        minimize_truth_table=False,
        only_on_critical_path=True,
        sop_both_phases=False,
        verbose=True,
    )
    assert aig_params_test.num_pis == num_pis_before_clone
    assert aig_params_test.num_pos == num_pos_before_clone
    assert aig_params_test.num_gates == num_gates_before_clone
    assert _depth(aig_params_test) == depth_before_clone


def test_balancing_reduces_depth_of_long_chain(make_and_chain_aig: Callable[[int], Aig]) -> None:
    """Test that balancing significantly reduces depth for a long, unbalanced chain."""
    aig = make_and_chain_aig(5)

    num_pis_before = aig.num_pis
    num_pos_before = aig.num_pos
    num_gates_before = aig.num_gates
    depth_before = _depth(aig)

    aig_copy = aig.clone()

    assert depth_before == 4

    aig = balancing(aig)

    assert aig.num_pis == num_pis_before
    assert aig.num_pos == num_pos_before
    assert aig.num_gates == num_gates_before

    expected_depth_after_balancing = 3
    depth_after = _depth(aig)
    assert depth_after == expected_depth_after_balancing, (
        f"Depth not reduced as expected: before {depth_before}, "
        f"after {depth_after}, expected {expected_depth_after_balancing}"
    )
    assert depth_after < depth_before

    # Test with parameters that might affect balancing quality
    original_unbalanced_aig = aig_copy

    cloned_unbalanced_base = original_unbalanced_aig.clone()
    aig_params_test = cloned_unbalanced_base

    num_pis_before_clone = aig_params_test.num_pis
    num_pos_before_clone = aig_params_test.num_pos
    num_gates_before_clone = aig_params_test.num_gates
    depth_before_clone = _depth(aig_params_test)

    aig_params_test = balancing(aig_params_test, cut_size=3, cut_limit=4, only_on_critical_path=False)
    assert aig_params_test.num_pis == num_pis_before_clone
    assert aig_params_test.num_pos == num_pos_before_clone
    depth_after_clone = _depth(aig_params_test)
    assert depth_after_clone < depth_before_clone
    assert depth_after_clone == expected_depth_after_balancing
    assert aig_params_test.num_gates == num_gates_before_clone


def test_balancing_complex_unbalanced_to_balanced_tree(complex_unbalanced_balancing_aig: Aig) -> None:
    """Test balancing transforms a complex unbalanced AIG into a balanced tree, reducing depth."""
    aig = complex_unbalanced_balancing_aig

    num_pis_before = aig.num_pis
    num_pos_before = aig.num_pos
    num_gates_before = aig.num_gates
    depth_before = _depth(aig)

    aig_copy = aig.clone()

    assert num_gates_before == 7
    assert depth_before == 6

    aig = balancing(aig)

    assert aig.num_pis == num_pis_before
    assert aig.num_pos == num_pos_before

    expected_gates_after = 7
    expected_depth_after = 3

    assert aig.num_gates == expected_gates_after
    depth_after = _depth(aig)
    assert depth_after == expected_depth_after
    assert depth_after < depth_before

    # Test with only_on_critical_path = True
    aig_crit_path_test = aig_copy

    num_pis_before_clone = aig_crit_path_test.num_pis
    num_pos_before_clone = aig_crit_path_test.num_pos
    depth_before_clone = _depth(aig_crit_path_test)

    aig_crit_path_test = balancing(aig_crit_path_test, only_on_critical_path=True)
    assert aig_crit_path_test.num_pis == num_pis_before_clone
    assert aig_crit_path_test.num_pos == num_pos_before_clone
    assert aig_crit_path_test.num_gates == expected_gates_after
    depth_after_clone = _depth(aig_crit_path_test)
    assert depth_after_clone == expected_depth_after
    assert depth_after_clone < depth_before_clone


def test_balancing_with_different_cut_sizes_on_chain(make_and_chain_aig: Callable[[int], Aig]) -> None:
    """Test balancing a chain with varying cut_size parameters."""
    pis_count = 7
    expected_initial_depth = pis_count - 1
    expected_final_depth_optimal = 3  # log2(7) rounded up

    # Default cut_size (4)
    aig_cs_default = make_and_chain_aig(pis_count)
    assert _depth(aig_cs_default) == expected_initial_depth

    aig_cs_default = balancing(aig_cs_default)
    assert _depth(aig_cs_default) == expected_final_depth_optimal

    # Smaller cut_size (e.g., 2)
    aig_cs_small = make_and_chain_aig(pis_count)
    depth_before_cs_small = _depth(aig_cs_small)

    aig_cs_small = balancing(aig_cs_small, cut_size=2, cut_limit=10)
    depth_after_cs_small = _depth(aig_cs_small)
    assert depth_after_cs_small <= depth_before_cs_small
    # For cut_size=2, balancing might not improve or change depth for a simple chain
    assert depth_after_cs_small == expected_initial_depth, (
        f"Depth with cut_size=2 not as expected: {depth_after_cs_small}, expected {expected_initial_depth}"
    )

    # Larger cut_size (e.g., 6)
    aig_cs_large = make_and_chain_aig(pis_count)

    aig_cs_large = balancing(aig_cs_large, cut_size=6, cut_limit=12)
    assert _depth(aig_cs_large) == expected_final_depth_optimal


def test_esop_balancing_reduces_depth_on_xor_chain(make_xor_chain_aig: Callable[[int], Aig]) -> None:
    """Test ESOP balancing behavior on a chain of XORs (XAG-like)."""
    aig = make_xor_chain_aig(8)
    depth_before = _depth(aig)
    assert depth_before == 14  # Depth of AIG XOR chain

    aig = balancing(aig, rebalance_function="esop")
    depth_after = _depth(aig)
    # Current ESOP balancing on AIG XORs results in depth 8 for this 8-input case
    assert depth_after == 8, f"ESOP balancing did not produce expected depth: {depth_after} (expected 8)"


def test_esop_balancing_preserves_functionality_on_xor_and_chain(mixed_xor_and_balancing_aig: Aig) -> None:
    """Test ESOP balancing preserves PI/PO/gate count and depth for a mixed XOR/AND AIG."""
    aig = mixed_xor_and_balancing_aig
    num_pis_before = aig.num_pis
    num_pos_before = aig.num_pos
    num_gates_before = aig.num_gates
    depth_before = _depth(aig)

    aig = balancing(aig, rebalance_function="esop")
    depth_after = _depth(aig)
    assert aig.num_pis == num_pis_before
    assert aig.num_pos == num_pos_before
    assert aig.num_gates <= num_gates_before + 2  # ESOP might slightly alter gate count
    assert depth_after == depth_before  # ESOP balancing may not reduce depth for all AIGs


def test_balancing_invalid_rebalance_function_raises(and_gate_aig: Aig) -> None:
    """
    Test that an invalid rebalance_function raises an exception.
    """
    aig = and_gate_aig
    with pytest.raises(Exception, match="Unknown rebalance function"):
        balancing(aig, rebalance_function="not_a_valid_option")  # ty: ignore[invalid-argument-type]


def test_esop_balancing_with_sop_both_phases_param(make_xor_chain_aig: Callable[[int], Aig]) -> None:
    """Test esop balancing with sop_both_phases param does not error and preserves depth."""
    aig = make_xor_chain_aig(3)
    depth_before = _depth(aig)
    aig = balancing(aig, rebalance_function="esop", sop_both_phases=False)
    assert _depth(aig) <= depth_before


def test_return_new_does_not_mutate_input(make_and_chain_aig: Callable[[int], Aig]) -> None:
    aig = make_and_chain_aig(4)

    aig_before = aig.clone()
    result = balancing(aig)

    assert result is not None
    assert _depth(aig) == _depth(aig_before)
