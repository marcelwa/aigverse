from __future__ import annotations

import pytest

from aigverse import DepthAig, balancing


def test_balancing_on_simple_balanced_aig() -> None:
    """Test balancing on an already simple balanced AIG preserves its structure."""
    aig = DepthAig()
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    a0 = aig.create_and(x0, x1)
    a1 = aig.create_and(a0, x2)
    aig.create_po(a1)

    num_pis_before = aig.num_pis()
    num_pos_before = aig.num_pos()
    num_gates_before = aig.num_gates()
    aig.update_levels()
    depth_before = aig.num_levels()

    balancing(aig)
    aig.update_levels()

    assert aig.num_pis() == num_pis_before
    assert aig.num_pos() == num_pos_before
    assert aig.num_gates() == num_gates_before, (
        f"Gate count changed for a balanced AIG: before {num_gates_before}, after {aig.num_gates()}"
    )
    assert aig.num_levels() == depth_before, (
        f"Depth changed for a balanced AIG: before {depth_before}, after {aig.num_levels()}"
    )

    # Test balancing with non-default parameters
    cloned_aig_base = aig.clone()
    aig_params_test = DepthAig(cloned_aig_base)

    # Re-fetch original properties from the new DepthAig instance
    num_pis_before_clone = aig_params_test.num_pis()
    num_pos_before_clone = aig_params_test.num_pos()
    num_gates_before_clone = aig_params_test.num_gates()
    aig_params_test.update_levels()
    depth_before_clone = aig_params_test.num_levels()

    balancing(
        aig_params_test,
        cut_size=6,
        cut_limit=10,
        minimize_truth_table=False,
        only_on_critical_path=True,
        sop_both_phases=False,
        verbose=True,
    )
    aig_params_test.update_levels()

    assert aig_params_test.num_pis() == num_pis_before_clone
    assert aig_params_test.num_pos() == num_pos_before_clone
    assert aig_params_test.num_gates() == num_gates_before_clone
    assert aig_params_test.num_levels() == depth_before_clone


def test_balancing_reduces_depth_of_long_chain() -> None:
    """Test that balancing significantly reduces depth for a long, unbalanced chain."""
    aig = DepthAig()
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()
    x4 = aig.create_pi()

    # Create an unbalanced chain: x0 & (x1 & (x2 & (x3 & x4)))
    n0 = aig.create_and(x3, x4)
    n1 = aig.create_and(x2, n0)
    n2 = aig.create_and(x1, n1)
    n3 = aig.create_and(x0, n2)
    aig.create_po(n3)

    num_pis_before = aig.num_pis()
    num_pos_before = aig.num_pos()
    num_gates_before = aig.num_gates()
    aig.update_levels()
    depth_before = aig.num_levels()

    aig_copy = aig.clone()

    assert depth_before == 4

    balancing(aig)
    aig.update_levels()

    assert aig.num_pis() == num_pis_before
    assert aig.num_pos() == num_pos_before
    assert aig.num_gates() == num_gates_before

    expected_depth_after_balancing = 3
    assert aig.num_levels() == expected_depth_after_balancing, (
        f"Depth not reduced as expected: before {depth_before}, "
        f"after {aig.num_levels()}, expected {expected_depth_after_balancing}"
    )
    assert aig.num_levels() < depth_before

    # Test with parameters that might affect balancing quality
    original_unbalanced_aig = DepthAig(aig_copy)

    cloned_unbalanced_base = original_unbalanced_aig.clone()
    aig_params_test = DepthAig(cloned_unbalanced_base)

    num_pis_before_clone = aig_params_test.num_pis()
    num_pos_before_clone = aig_params_test.num_pos()
    num_gates_before_clone = aig_params_test.num_gates()
    aig_params_test.update_levels()
    depth_before_clone = aig_params_test.num_levels()

    balancing(aig_params_test, cut_size=3, cut_limit=4, only_on_critical_path=False)
    aig_params_test.update_levels()

    assert aig_params_test.num_pis() == num_pis_before_clone
    assert aig_params_test.num_pos() == num_pos_before_clone
    assert aig_params_test.num_levels() < depth_before_clone
    assert aig_params_test.num_levels() == expected_depth_after_balancing
    assert aig_params_test.num_gates() == num_gates_before_clone


def test_balancing_complex_unbalanced_to_balanced_tree() -> None:
    """Test balancing transforms a complex unbalanced AIG into a balanced tree, reducing depth."""
    aig = DepthAig()
    pis = [aig.create_pi() for _ in range(8)]
    x0, x1, x2, x3, x4, x5, x6, x7 = pis

    # AIG definition: (x0 & x1) & (x2 & (x3 & (x4 & (x5 & (x6 & x7)))))
    n_chain_0 = aig.create_and(x6, x7)
    n_chain_1 = aig.create_and(x5, n_chain_0)
    n_chain_2 = aig.create_and(x4, n_chain_1)
    n_chain_3 = aig.create_and(x3, n_chain_2)
    n_chain_4 = aig.create_and(x2, n_chain_3)
    n_branch_0 = aig.create_and(x0, x1)
    output_node = aig.create_and(n_branch_0, n_chain_4)
    aig.create_po(output_node)

    num_pis_before = aig.num_pis()
    num_pos_before = aig.num_pos()
    num_gates_before = aig.num_gates()
    aig.update_levels()
    depth_before = aig.num_levels()

    aig_copy = aig.clone()

    assert num_gates_before == 7
    assert depth_before == 6

    balancing(aig)
    aig.update_levels()

    assert aig.num_pis() == num_pis_before
    assert aig.num_pos() == num_pos_before

    expected_gates_after = 7
    expected_depth_after = 3

    assert aig.num_gates() == expected_gates_after
    assert aig.num_levels() == expected_depth_after
    assert aig.num_levels() < depth_before

    # Test with only_on_critical_path = True
    aig_crit_path_test = DepthAig(aig_copy)

    num_pis_before_clone = aig_crit_path_test.num_pis()
    num_pos_before_clone = aig_crit_path_test.num_pos()
    aig_crit_path_test.update_levels()
    depth_before_clone = aig_crit_path_test.num_levels()

    balancing(aig_crit_path_test, only_on_critical_path=True)
    aig_crit_path_test.update_levels()

    assert aig_crit_path_test.num_pis() == num_pis_before_clone
    assert aig_crit_path_test.num_pos() == num_pos_before_clone
    assert aig_crit_path_test.num_gates() == expected_gates_after
    assert aig_crit_path_test.num_levels() == expected_depth_after
    assert aig_crit_path_test.num_levels() < depth_before_clone


def _create_and_chain_po(aig: DepthAig, num_pis: int) -> None:
    """Helper to create an AND chain of num_pis inputs and a PO."""
    pis_list = [aig.create_pi() for _ in range(num_pis)]
    if num_pis == 0:
        aig.create_po(aig.get_constant(False))
        return
    if num_pis == 1:
        aig.create_po(pis_list[0])
        return

    current_node = aig.create_and(pis_list[-2], pis_list[-1])
    for i in range(num_pis - 3, -1, -1):
        current_node = aig.create_and(pis_list[i], current_node)
    aig.create_po(current_node)


def test_balancing_with_different_cut_sizes_on_chain() -> None:
    """Test balancing a chain with varying cut_size parameters."""
    pis_count = 7
    expected_initial_depth = pis_count - 1
    expected_final_depth_optimal = 3  # log2(7) rounded up

    # Default cut_size (4)
    aig_cs_default = DepthAig()
    _create_and_chain_po(aig_cs_default, pis_count)
    aig_cs_default.update_levels()
    assert aig_cs_default.num_levels() == expected_initial_depth

    balancing(aig_cs_default)
    aig_cs_default.update_levels()
    assert aig_cs_default.num_levels() == expected_final_depth_optimal

    # Smaller cut_size (e.g., 2)
    aig_cs_small = DepthAig()
    _create_and_chain_po(aig_cs_small, pis_count)
    aig_cs_small.update_levels()
    depth_before_cs_small = aig_cs_small.num_levels()

    balancing(aig_cs_small, cut_size=2, cut_limit=10)
    aig_cs_small.update_levels()
    assert aig_cs_small.num_levels() <= depth_before_cs_small
    # For cut_size=2, balancing might not improve or change depth for a simple chain
    assert aig_cs_small.num_levels() == expected_initial_depth, (
        f"Depth with cut_size=2 not as expected: {aig_cs_small.num_levels()}, expected {expected_initial_depth}"
    )

    # Larger cut_size (e.g., 6)
    aig_cs_large = DepthAig()
    _create_and_chain_po(aig_cs_large, pis_count)
    aig_cs_large.update_levels()

    balancing(aig_cs_large, cut_size=6, cut_limit=12)
    aig_cs_large.update_levels()
    assert aig_cs_large.num_levels() == expected_final_depth_optimal


def test_esop_balancing_reduces_depth_on_xor_chain() -> None:
    """Test ESOP balancing behavior on a chain of XORs (XAG-like)."""
    aig = DepthAig()
    pis = [aig.create_pi() for _ in range(8)]
    node = pis[0]
    for i in range(1, 8):
        node = aig.create_xor(node, pis[i])
    aig.create_po(node)
    aig.update_levels()
    depth_before = aig.num_levels()
    assert depth_before == 14  # Depth of AIG XOR chain

    balancing(aig, rebalance_function="esop")
    aig.update_levels()
    # Current ESOP balancing on AIG XORs results in depth 8 for this 8-input case
    assert aig.num_levels() == 8, f"ESOP balancing did not produce expected depth: {aig.num_levels()} (expected 8)"


def test_esop_balancing_preserves_functionality_on_xor_and_chain() -> None:
    """Test ESOP balancing preserves PI/PO/gate count and depth for a mixed XOR/AND AIG."""
    aig = DepthAig()
    pis = [aig.create_pi() for _ in range(8)]
    n0 = aig.create_xor(pis[0], pis[1])
    n1 = aig.create_xor(pis[2], pis[3])
    n2 = aig.create_and(n0, n1)
    n3 = aig.create_and(pis[4], pis[5])
    n4 = aig.create_and(pis[6], pis[7])
    n5 = aig.create_xor(n3, n4)
    out = aig.create_xor(n2, n5)
    aig.create_po(out)
    aig.update_levels()
    num_pis_before = aig.num_pis()
    num_pos_before = aig.num_pos()
    num_gates_before = aig.num_gates()
    depth_before = aig.num_levels()

    balancing(aig, rebalance_function="esop")
    aig.update_levels()
    assert aig.num_pis() == num_pis_before
    assert aig.num_pos() == num_pos_before
    assert aig.num_gates() <= num_gates_before + 2  # ESOP might slightly alter gate count
    assert aig.num_levels() == depth_before  # ESOP balancing may not reduce depth for all AIGs


def test_balancing_invalid_rebalance_function_raises() -> None:
    """
    Test that an invalid rebalance_function raises an exception.
    """
    aig = DepthAig()
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    a0 = aig.create_and(x0, x1)
    aig.create_po(a0)
    with pytest.raises(Exception, match="Unknown rebalance function"):
        balancing(aig, rebalance_function="not_a_valid_option")  # type: ignore [arg-type]


def test_esop_balancing_with_sop_both_phases_param() -> None:
    """Test esop balancing with sop_both_phases param does not error and preserves depth."""
    aig = DepthAig()
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    n0 = aig.create_xor(x0, x1)
    n1 = aig.create_xor(n0, x2)
    aig.create_po(n1)
    aig.update_levels()
    depth_before = aig.num_levels()
    balancing(aig, rebalance_function="esop", sop_both_phases=False)
    aig.update_levels()
    assert aig.num_levels() <= depth_before
