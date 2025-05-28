from __future__ import annotations

from aigverse import DepthAig, aig_balance


def test_balancing_on_simple_balanced_aig() -> None:
    """Test balancing on an already simple balanced AIG preserves its structure."""
    aig = DepthAig()

    # Create PIs
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    x2 = aig.create_pi()

    # Create logic: (x0 & x1) & x2
    # This is already balanced with depth 2 and 2 AND gates.
    a0 = aig.create_and(x0, x1)
    a1 = aig.create_and(a0, x2)
    aig.create_po(a1)

    num_pis_before = aig.num_pis()
    num_pos_before = aig.num_pos()
    num_gates_before = aig.num_gates()
    aig.update_levels()  # Initial depth calculation
    depth_before = aig.num_levels()

    # Apply balancing
    aig_balance(aig)  # Default parameters
    aig.update_levels()  # Recompute levels after potential structural changes

    assert aig.num_pis() == num_pis_before, "Number of PIs should not change."
    assert aig.num_pos() == num_pos_before, "Number of POs should not change."

    # For a simple, already balanced AIG, gate count should remain the same.
    assert aig.num_gates() == num_gates_before, (
        f"Gate count changed for a balanced AIG: before {num_gates_before}, after {aig.num_gates()}"
    )

    # Depth should remain the same for an already balanced AIG.
    assert aig.num_levels() == depth_before, (
        f"Depth changed for a balanced AIG: before {depth_before}, after {aig.num_levels()}"
    )

    # Test with non-default parameters that shouldn't change the outcome for this simple case
    cloned_aig_for_params = DepthAig()  # Create a new DepthAig
    x0_c = cloned_aig_for_params.create_pi()
    x1_c = cloned_aig_for_params.create_pi()
    x2_c = cloned_aig_for_params.create_pi()
    a0_c = cloned_aig_for_params.create_and(x0_c, x1_c)
    a1_c = cloned_aig_for_params.create_and(a0_c, x2_c)
    cloned_aig_for_params.create_po(a1_c)

    aig_balance(
        cloned_aig_for_params,
        cut_size=6,
        cut_limit=10,
        minimize_truth_table=False,
        only_on_critical_path=True,
        sop_both_phases=False,
        verbose=True,
    )
    cloned_aig_for_params.update_levels()

    assert cloned_aig_for_params.num_pis() == num_pis_before, "PIs changed with non-default params."
    assert cloned_aig_for_params.num_pos() == num_pos_before, "POs changed with non-default params."
    assert cloned_aig_for_params.num_gates() == num_gates_before, "Gates changed with non-default params."
    assert cloned_aig_for_params.num_levels() == depth_before, "Depth changed with non-default params."


def test_balancing_reduces_depth_of_long_chain() -> None:
    """Test that balancing significantly reduces depth for a long, unbalanced chain."""
    aig = DepthAig()

    # Create PIs
    x0 = aig.create_pi()
    x1 = aig.create_pi()
    x2 = aig.create_pi()
    x3 = aig.create_pi()
    x4 = aig.create_pi()

    # Create an unbalanced chain: x0 & (x1 & (x2 & (x3 & x4)))
    # Initial depth will be 4 (number of cascaded ANDs).
    n0 = aig.create_and(x3, x4)  # depth 1 relative to x3,x4
    n1 = aig.create_and(x2, n0)  # depth 2
    n2 = aig.create_and(x1, n1)  # depth 3
    n3 = aig.create_and(x0, n2)  # depth 4
    aig.create_po(n3)

    num_pis_before = aig.num_pis()
    num_pos_before = aig.num_pos()
    num_gates_before = aig.num_gates()  # 4 AND gates
    aig.update_levels()  # Initial depth calculation
    depth_before = aig.num_levels()

    assert depth_before == 4, f"Initial depth calculation is unexpected: {depth_before}"

    # Apply balancing
    aig_balance(aig)  # Default parameters
    aig.update_levels()

    assert aig.num_pis() == num_pis_before, "Number of PIs should not change after balancing."
    assert aig.num_pos() == num_pos_before, "Number of POs should not change after balancing."

    # A balanced 5-input AND tree would have depth log2(5) rounded up, which is 3.
    # (e.g., ((x0&x1)&(x2&x3))&x4 or (x0&x1)&((x2&x3)&x4) )
    # The number of AND gates should remain 4.
    assert aig.num_gates() == num_gates_before, (
        f"Gate count changed: before {num_gates_before}, after {aig.num_gates()}"
    )

    expected_depth_after_balancing = 3
    assert aig.num_levels() == expected_depth_after_balancing, (
        f"Depth not reduced as expected for unbalanced chain: "
        f"before {depth_before}, after {aig.num_levels()}, expected {expected_depth_after_balancing}"
    )
    assert aig.num_levels() < depth_before, f"Depth not reduced: before {depth_before}, after {aig.num_levels()}"

    # Test with parameters that might affect balancing quality but should still reduce depth
    aig_orig = DepthAig()
    x0_orig = aig_orig.create_pi()
    x1_orig = aig_orig.create_pi()
    x2_orig = aig_orig.create_pi()
    x3_orig = aig_orig.create_pi()
    x4_orig = aig_orig.create_pi()
    n0_orig = aig_orig.create_and(x3_orig, x4_orig)
    n1_orig = aig_orig.create_and(x2_orig, n0_orig)
    n2_orig = aig_orig.create_and(x1_orig, n1_orig)
    n3_orig = aig_orig.create_and(x0_orig, n2_orig)
    aig_orig.create_po(n3_orig)
    aig_orig.update_levels()
    depth_before_orig = aig_orig.num_levels()
    num_gates_before_orig = aig_orig.num_gates()

    aig_balance(aig_orig, cut_size=3, cut_limit=4, only_on_critical_path=False)  # Smaller cuts
    aig_orig.update_levels()

    assert aig_orig.num_pis() == num_pis_before, "PIs changed with non-default params."
    assert aig_orig.num_pos() == num_pos_before, "POs changed with non-default params."
    # Gate count might change slightly with different parameters, but depth should still improve
    assert aig_orig.num_levels() < depth_before_orig, "Depth not reduced with non-default params."
    # For this specific chain and cut_size=3, it should still balance to depth 3
    assert aig_orig.num_levels() == expected_depth_after_balancing, (
        f"Depth not as expected with cut_size=3: {aig_orig.num_levels()}, expected {expected_depth_after_balancing}"
    )
    # Gate count should ideally remain the same (4 ANDs) for a 5-input tree
    assert aig_orig.num_gates() == num_gates_before_orig, (
        f"Gate count changed with non-default params: {aig_orig.num_gates()}, expected {num_gates_before_orig}"
    )


def test_balancing_complex_unbalanced_to_balanced_tree() -> None:
    """Test balancing transforms a complex unbalanced AIG into a balanced tree, reducing depth."""
    aig = DepthAig()

    # Create 8 PIs
    pis = [aig.create_pi() for _ in range(8)]
    x0, x1, x2, x3, x4, x5, x6, x7 = pis

    # Create an unbalanced structure: (x0 & x1) & (x2 & (x3 & (x4 & (x5 & (x6 & x7)))))
    n_chain_0 = aig.create_and(x6, x7)
    n_chain_1 = aig.create_and(x5, n_chain_0)
    n_chain_2 = aig.create_and(x4, n_chain_1)
    n_chain_3 = aig.create_and(x3, n_chain_2)
    n_chain_4 = aig.create_and(x2, n_chain_3)  # This part has depth 5

    n_branch_0 = aig.create_and(x0, x1)  # This part has depth 1

    output_node = aig.create_and(n_branch_0, n_chain_4)
    aig.create_po(output_node)

    num_pis_before = aig.num_pis()
    num_pos_before = aig.num_pos()
    # Gate count for the complex unbalanced tree:
    # 5 gates for the main chain + 1 for the side branch + 1 for the final AND = 7 gates.
    num_gates_before = aig.num_gates()
    aig.update_levels()  # Initial depth calculation
    depth_before = aig.num_levels()

    assert num_gates_before == 7, f"Initial gate count unexpected: {num_gates_before}"
    assert depth_before == 6, f"Initial depth calculation is unexpected: {depth_before}"

    # Apply balancing
    aig_balance(aig)  # Default parameters
    aig.update_levels()

    assert aig.num_pis() == num_pis_before, "Number of PIs should not change."
    assert aig.num_pos() == num_pos_before, "Number of POs should not change."

    # An 8-input balanced AND tree has 7 AND gates and depth 3.
    expected_gates_after = 7
    expected_depth_after = 3

    assert aig.num_gates() == expected_gates_after, (
        f"Gate count not as expected after balancing: "
        f"before {num_gates_before}, after {aig.num_gates()}, expected {expected_gates_after}"
    )
    assert aig.num_levels() == expected_depth_after, (
        f"Depth not reduced to optimal for 8-input tree: "
        f"before {depth_before}, after {aig.num_levels()}, expected {expected_depth_after}"
    )
    assert aig.num_levels() < depth_before, f"Depth not reduced: before {depth_before}, after {aig.num_levels()}"

    # Test with only_on_critical_path = True.
    aig_orig = DepthAig()
    pis_orig = [aig_orig.create_pi() for _ in range(8)]
    x0o, x1o, x2o, x3o, x4o, x5o, x6o, x7o = pis_orig
    nc0o = aig_orig.create_and(x6o, x7o)
    nc1o = aig_orig.create_and(x5o, nc0o)
    nc2o = aig_orig.create_and(x4o, nc1o)
    nc3o = aig_orig.create_and(x3o, nc2o)
    nc4o = aig_orig.create_and(x2o, nc3o)
    nb0o = aig_orig.create_and(x0o, x1o)
    outo = aig_orig.create_and(nb0o, nc4o)
    aig_orig.create_po(outo)
    aig_orig.update_levels()
    depth_before_orig_crit = aig_orig.num_levels()
    num_gates_before_orig_crit = aig_orig.num_gates()

    aig_balance(aig_orig, only_on_critical_path=True)
    aig_orig.update_levels()

    assert aig_orig.num_pis() == num_pis_before, "PIs changed with critical_path=True."
    assert aig_orig.num_pos() == num_pos_before, "POs changed with critical_path=True."
    assert aig_orig.num_gates() == expected_gates_after, (
        f"Gate count not as expected with critical_path=True: "
        f"before {num_gates_before_orig_crit}, after {aig_orig.num_gates()}, expected {expected_gates_after}"
    )
    assert aig_orig.num_levels() == expected_depth_after, (
        f"Depth not optimal with critical_path=True: "
        f"before {depth_before_orig_crit}, after {aig_orig.num_levels()}, expected {expected_depth_after}"
    )
    assert aig_orig.num_levels() < depth_before_orig_crit, "Depth not reduced with critical_path=True."


def test_balancing_with_different_cut_sizes_on_chain() -> None:
    """Test balancing a chain with varying cut_size parameters."""
    pis_count = 7  # Results in initial depth of 6
    expected_final_depth = 3  # log2(7) rounded up

    # Default cut_size (4)
    aig_cs_default = DepthAig()
    pis_cs_default = [aig_cs_default.create_pi() for _ in range(pis_count)]
    current_and_default = aig_cs_default.create_and(pis_cs_default[-2], pis_cs_default[-1])
    for i in range(pis_count - 3, -1, -1):
        current_and_default = aig_cs_default.create_and(pis_cs_default[i], current_and_default)
    aig_cs_default.create_po(current_and_default)
    aig_cs_default.update_levels()
    depth_before_cs_default = aig_cs_default.num_levels()
    assert depth_before_cs_default == pis_count - 1

    aig_balance(aig_cs_default)  # cut_size=4 by default
    aig_cs_default.update_levels()
    assert aig_cs_default.num_levels() == expected_final_depth, (
        f"Depth with default cut_size not optimal: {aig_cs_default.num_levels()}, expected {expected_final_depth}"
    )

    # Smaller cut_size (e.g., 2 - which might be too restrictive for good balancing)
    aig_cs_small = DepthAig()
    pis_cs_small = [aig_cs_small.create_pi() for _ in range(pis_count)]
    current_and_small = aig_cs_small.create_and(pis_cs_small[-2], pis_cs_small[-1])
    for i in range(pis_count - 3, -1, -1):
        current_and_small = aig_cs_small.create_and(pis_cs_small[i], current_and_small)
    aig_cs_small.create_po(current_and_small)
    aig_cs_small.update_levels()
    depth_before_cs_small = aig_cs_small.num_levels()

    aig_balance(aig_cs_small, cut_size=2, cut_limit=10)  # Using cut_size=2
    aig_cs_small.update_levels()
    assert aig_cs_small.num_levels() <= depth_before_cs_small, (
        f"Depth with cut_size=2 unexpectedly increased: {aig_cs_small.num_levels()}, was {depth_before_cs_small}"
    )
    assert aig_cs_small.num_levels() == 6, (
        f"Depth with cut_size=2 not as observed: {aig_cs_small.num_levels()}, "
        f"expected 6 (no change from original chain depth)"
    )

    # Larger cut_size (e.g., 6)
    aig_cs_large = DepthAig()
    pis_cs_large = [aig_cs_large.create_pi() for _ in range(pis_count)]
    current_and_large = aig_cs_large.create_and(pis_cs_large[-2], pis_cs_large[-1])
    for i in range(pis_count - 3, -1, -1):
        current_and_large = aig_cs_large.create_and(pis_cs_large[i], current_and_large)
    aig_cs_large.create_po(current_and_large)
    aig_cs_large.update_levels()
    aig_cs_large.num_levels()

    aig_balance(aig_cs_large, cut_size=6, cut_limit=12)
    aig_cs_large.update_levels()
    assert aig_cs_large.num_levels() == expected_final_depth, (
        f"Depth with cut_size=6 not optimal: {aig_cs_large.num_levels()}, expected {expected_final_depth}"
    )
