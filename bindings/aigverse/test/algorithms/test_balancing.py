from __future__ import annotations

import aigverse


class TestBalancing:
    def test_smoke_run(self):
        """Test that aig_balance runs without errors and preserves PI/PO count."""
        aig = aigverse.aig()

        # Create PIs
        x0 = aig.create_pi()
        x1 = aig.create_pi()
        x2 = aig.create_pi()

        # Create logic
        a0 = aig.create_and(x0, x1)
        a1 = aig.create_and(a0, x2)

        # Create PO
        aig.create_po(a1)

        num_pis_before = aig.num_pis()
        num_pos_before = aig.num_pos()
        # Assuming num_gates() and depth() exist, common for such libraries
        num_gates_before = aig.num_gates()
        depth_before = aig.depth()

        # Apply balancing
        aigverse.aig_balance(aig)

        assert aig.num_pis() == num_pis_before, "Number of PIs should not change."
        assert aig.num_pos() == num_pos_before, "Number of POs should not change."

        # Balancing might change gate count, but shouldn't explode for simple cases.
        # It could even increase slightly. A very loose check here.
        assert aig.num_gates() <= num_gates_before * 2, (
            f"Gate count changed significantly: before {num_gates_before}, after {aig.num_gates()}"
        )

        # Depth should ideally not increase.
        assert aig.depth() <= depth_before, f"Depth increased: before {depth_before}, after {aig.depth()}"

    def test_balancing_effect_on_depth(self):
        """Test that balancing reduces depth for an unbalanced network."""
        aig = aigverse.aig()

        # Create PIs
        x0 = aig.create_pi()
        x1 = aig.create_pi()
        x2 = aig.create_pi()
        x3 = aig.create_pi()
        x4 = aig.create_pi()

        # Create an unbalanced chain: x0 & (x1 & (x2 & (x3 & x4)))
        # Depth will be high due to the chain
        n0 = aig.create_and(x3, x4)  # depth 1 relative to x3,x4
        n1 = aig.create_and(x2, n0)  # depth 2
        n2 = aig.create_and(x1, n1)  # depth 3
        n3 = aig.create_and(x0, n2)  # depth 4

        aig.create_po(n3)

        num_pis_before = aig.num_pis()
        num_pos_before = aig.num_pos()
        depth_before = aig.depth()

        # Apply balancing
        aigverse.aig_balance(aig)

        assert aig.num_pis() == num_pis_before, "Number of PIs should not change after balancing."
        assert aig.num_pos() == num_pos_before, "Number of POs should not change after balancing."

        # For a long chain, balancing should ideally reduce depth.
        # If depth_before is very small (e.g. 1 or 2), reduction might not happen or be significant.
        # The created network has a depth of 4.
        if depth_before > 2:  # Only assert depth reduction if there's something to reduce
            assert aig.depth() < depth_before, (
                f"Depth not reduced for unbalanced chain: before {depth_before}, after {aig.depth()}"
            )
        else:
            assert aig.depth() <= depth_before, (
                f"Depth increased for shallow chain: before {depth_before}, after {aig.depth()}"
            )


