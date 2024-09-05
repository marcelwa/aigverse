from aigverse import *

import unittest


class TestAig(unittest.TestCase):
    def test_aig_constants(self):
        aig = Aig()
        self.assertEqual(aig.size(), 1)
        self.assertEqual(aig.num_gates(), 0)
        self.assertEqual(aig.num_pis(), 0)
        self.assertEqual(aig.num_pos(), 0)

        self.assertEqual(aig.nodes(), [0])
        self.assertEqual(aig.gates(), [])
        self.assertEqual(aig.pis(), [])
        self.assertEqual(aig.pos(), [])

        self.assertTrue(aig.is_constant(0))
        c0 = aig.get_constant(False)
        self.assertTrue(aig.is_constant(aig.get_node(c0)))
        self.assertFalse(aig.is_pi(aig.get_node(c0)))
        self.assertEqual(aig.get_node(c0), 0)
        self.assertFalse(aig.is_complemented(c0))

        c1 = aig.get_constant(True)
        self.assertTrue(aig.is_constant(aig.get_node(c1)))
        self.assertFalse(aig.is_pi(aig.get_node(c1)))
        self.assertEqual(aig.get_node(c1), 0)
        self.assertTrue(aig.is_complemented(c1))

        self.assertNotEqual(c0, c1)
        self.assertEqual(aig.get_node(c0), aig.get_node(c1))
        self.assertEqual(c0, ~c1)
        self.assertEqual((~c0), c1)
        self.assertNotEqual((~c0), ~c1)
        self.assertEqual(-c0, c1)
        self.assertEqual(-c1, c1)
        self.assertEqual(c0, +c1)
        self.assertEqual(c0, +c0)

    def test_aig_primary_inputs(self):
        aig = Aig()

        # Ensure the create_pi function exists in AIG
        self.assertTrue(hasattr(aig, 'create_pi'))

        # Create primary inputs
        a = aig.create_pi()
        b = aig.create_pi()

        # Check the properties of the AIG after adding inputs
        self.assertEqual(aig.size(), 3)  # constant + two primary inputs
        self.assertEqual(aig.num_pis(), 2)
        self.assertEqual(aig.num_gates(), 0)
        self.assertTrue(aig.is_pi(aig.get_node(a)))
        self.assertTrue(aig.is_pi(aig.get_node(b)))
        self.assertEqual(aig.pi_index(aig.get_node(a)), 0)
        self.assertEqual(aig.pi_index(aig.get_node(b)), 1)

        # Verify the type of signal
        self.assertIsInstance(a, AigSignal)

        # Check initial properties of signal `a`
        self.assertEqual(a.get_index(), 1)
        self.assertEqual(a.get_complement(), 0)

        # Test negation (~)
        a = ~a
        self.assertEqual(a.get_index(), 1)
        self.assertEqual(a.get_complement(), 1)

        # Test positive sign (+)
        a = +a
        self.assertEqual(a.get_index(), 1)
        self.assertEqual(a.get_complement(), 0)

        # Reapplying positive sign should not change anything
        a = +a
        self.assertEqual(a.get_index(), 1)
        self.assertEqual(a.get_complement(), 0)

        # Test negation (-)
        a = -a
        self.assertEqual(a.get_index(), 1)
        self.assertEqual(a.get_complement(), 1)

        # Reapplying negation should not change anything
        a = -a
        self.assertEqual(a.get_index(), 1)
        self.assertEqual(a.get_complement(), 1)

        # XOR operation with True
        a = a ^ True
        self.assertEqual(a.get_index(), 1)
        self.assertEqual(a.get_complement(), 0)

        # XOR operation with True again
        a = a ^ True
        self.assertEqual(a.get_index(), 1)
        self.assertEqual(a.get_complement(), 1)

    def test_aig_primary_outputs(self):
        aig = Aig()

        # Ensure the create_po function exists in AIG
        self.assertTrue(hasattr(aig, 'create_po'))

        # Create constant and primary input
        c0 = aig.get_constant(False)
        x1 = aig.create_pi()

        # Check initial size and input/output properties
        self.assertEqual(aig.size(), 2)
        self.assertEqual(aig.num_pis(), 1)
        self.assertEqual(aig.num_pos(), 0)

        # Create primary outputs
        aig.create_po(c0)
        aig.create_po(x1)
        aig.create_po(~x1)

        # Check size and number of primary outputs after creation
        self.assertEqual(aig.size(), 2)
        self.assertEqual(aig.num_pos(), 3)

        # Retrieve the primary outputs and verify them
        pos = aig.pos()

        # Check that the outputs match the expected values
        self.assertEqual(pos[0], c0)
        self.assertEqual(pos[1], x1)
        self.assertEqual(pos[2], ~x1)

    def test_aig_unary_operations(self):
        aig = Aig()

        # Ensure the create_buf and create_not functions exist in AIG
        self.assertTrue(hasattr(aig, 'create_buf'))
        self.assertTrue(hasattr(aig, 'create_not'))

        # Create a primary input
        x1 = aig.create_pi()

        # Check the initial size after creating the primary input
        self.assertEqual(aig.size(), 2)

        # Create buffer and NOT operations
        f1 = aig.create_buf(x1)
        f2 = aig.create_not(x1)

        # Ensure the size remains the same since both operations are unary
        self.assertEqual(aig.size(), 2)

        # Check if the buffer is equal to the input and NOT is the negation
        self.assertEqual(f1, x1)
        self.assertEqual(f2, ~x1)

    def test_aig_binary_operations(self):
        aig = Aig()

        # Ensure the binary operation functions exist in AIG
        self.assertTrue(hasattr(aig, 'create_and'))
        self.assertTrue(hasattr(aig, 'create_nand'))
        self.assertTrue(hasattr(aig, 'create_or'))
        self.assertTrue(hasattr(aig, 'create_nor'))
        self.assertTrue(hasattr(aig, 'create_xor'))
        self.assertTrue(hasattr(aig, 'create_xnor'))

        # Create two primary inputs
        x1 = aig.create_pi()
        x2 = aig.create_pi()

        # Check the initial size after creating the inputs
        self.assertEqual(aig.size(), 3)

        # Create AND operation
        f1 = aig.create_and(x1, x2)
        self.assertEqual(aig.size(), 4)

        # Create NAND operation
        f2 = aig.create_nand(x1, x2)
        self.assertEqual(aig.size(), 4)
        self.assertEqual(f1, ~f2)

        # Create OR operation
        f3 = aig.create_or(x1, x2)
        self.assertEqual(aig.size(), 5)

        # Create NOR operation
        f4 = aig.create_nor(x1, x2)
        self.assertEqual(aig.size(), 5)
        self.assertEqual(f3, ~f4)

        # Create XOR operation
        f5 = aig.create_xor(x1, x2)
        self.assertEqual(aig.size(), 8)

        # Create XNOR operation
        f6 = aig.create_xnor(x1, x2)
        self.assertEqual(aig.size(), 8)
        self.assertEqual(f5, ~f6)

    def test_aig_hash_nodes(self):
        aig = Aig()

        # Create two primary inputs
        a = aig.create_pi()
        b = aig.create_pi()

        # Create two identical AND gates
        f = aig.create_and(a, b)
        g = aig.create_and(a, b)

        # Check the size and number of gates
        self.assertEqual(aig.size(), 4)
        self.assertEqual(aig.num_gates(), 1)

        # Ensure that the two AND gates correspond to the same node
        self.assertEqual(aig.get_node(f), aig.get_node(g))

    def test_aig_clone_network(self):
        # Ensure the clone method exists in AIG
        self.assertTrue(hasattr(Aig, 'clone'))

        # Create an initial AIG network and add nodes
        aig0 = Aig()
        a = aig0.create_pi()
        b = aig0.create_pi()
        f0 = aig0.create_and(a, b)

        # Check initial size and gate count
        self.assertEqual(aig0.size(), 4)
        self.assertEqual(aig0.num_gates(), 1)

        # Clone the AIG network
        aig1 = aig0  # Shallow copy
        aig_clone = aig0.clone()  # Deep clone

        # Modify the cloned network
        c = aig1.create_pi()
        aig1.create_and(f0, c)

        # Check the sizes and gate counts
        self.assertEqual(aig0.size(), 6)  # aig0 has grown with aig1
        self.assertEqual(aig0.num_gates(), 2)

        # Ensure the deep clone remains unchanged
        self.assertEqual(aig_clone.size(), 4)
        self.assertEqual(aig_clone.num_gates(), 1)

    def test_aig_clone_node(self):
        # Ensure the clone_node method exists in AIG
        self.assertTrue(hasattr(Aig, 'clone_node'))

        # Create two AIG networks
        aig1 = Aig()
        aig2 = Aig()

        # Create nodes in aig1
        a1 = aig1.create_pi()
        b1 = aig1.create_pi()
        f1 = aig1.create_and(a1, b1)

        # Check the size of aig1
        self.assertEqual(aig1.size(), 4)

        # Create nodes in aig2
        a2 = aig2.create_pi()
        b2 = aig2.create_pi()

        # Check the size of aig2 before cloning
        self.assertEqual(aig2.size(), 3)

        # Clone a node from aig1 to aig2
        f2 = aig2.clone_node(aig1, aig1.get_node(f1), [a2, b2])

        # Check the size of aig2 after cloning
        self.assertEqual(aig2.size(), 4)

        # Verify the fanin nodes are not complemented
        for fanin in aig2.fanins(aig2.get_node(f2)):
            self.assertFalse(aig2.is_complemented(fanin))

    def test_aig_structural_properties(self):
        aig = Aig()

        # Ensure the structural property methods exist in AIG
        self.assertTrue(hasattr(aig, 'size'))
        self.assertTrue(hasattr(aig, 'num_pis'))
        self.assertTrue(hasattr(aig, 'num_pos'))
        self.assertTrue(hasattr(aig, 'num_gates'))
        self.assertTrue(hasattr(aig, 'fanin_size'))
        self.assertTrue(hasattr(aig, 'fanout_size'))

        # Create two primary inputs
        x1 = aig.create_pi()
        x2 = aig.create_pi()

        # Create AND and OR gates
        f1 = aig.create_and(x1, x2)
        f2 = aig.create_or(x1, x2)

        # Create primary outputs
        aig.create_po(f1)
        aig.create_po(f2)

        # Check structural properties
        self.assertEqual(aig.size(), 5)
        self.assertEqual(aig.num_pis(), 2)
        self.assertEqual(aig.num_pos(), 2)
        self.assertEqual(aig.num_gates(), 2)

        # Check fanin sizes
        self.assertEqual(aig.fanin_size(aig.get_node(x1)), 0)
        self.assertEqual(aig.fanin_size(aig.get_node(x2)), 0)
        self.assertEqual(aig.fanin_size(aig.get_node(f1)), 2)
        self.assertEqual(aig.fanin_size(aig.get_node(f2)), 2)

        # Check fanout sizes
        self.assertEqual(aig.fanout_size(aig.get_node(x1)), 2)
        self.assertEqual(aig.fanout_size(aig.get_node(x2)), 2)
        self.assertEqual(aig.fanout_size(aig.get_node(f1)), 1)
        self.assertEqual(aig.fanout_size(aig.get_node(f2)), 1)

    def test_aig_has_and(self):
        aig = Aig()

        # Create primary inputs
        x1 = aig.create_pi()
        x2 = aig.create_pi()
        x3 = aig.create_pi()

        # Create AND gates
        n4 = aig.create_and(~x1, x2)
        n5 = aig.create_and(x1, n4)
        n6 = aig.create_and(x3, n5)
        n7 = aig.create_and(n4, x2)
        n8 = aig.create_and(~n5, ~n7)
        n9 = aig.create_and(~n8, n4)

        # Create primary outputs
        aig.create_po(n6)
        aig.create_po(n9)

        # Check for existing and non-existing AND gates using has_and
        self.assertIsNotNone(aig.has_and(~x1, x2))
        self.assertEqual(aig.has_and(~x1, x2), n4)

        self.assertIsNone(aig.has_and(~x1, x3))

        self.assertIsNotNone(aig.has_and(~n7, ~n5))
        self.assertEqual(aig.has_and(~n7, ~n5), n8)

    def test_aig_node_signal_iteration(self):
        aig = Aig()

        # Ensure the structural iteration methods exist in AIG
        self.assertTrue(hasattr(aig, 'nodes'))
        self.assertTrue(hasattr(aig, 'pis'))
        self.assertTrue(hasattr(aig, 'pos'))
        self.assertTrue(hasattr(aig, 'gates'))
        self.assertTrue(hasattr(aig, 'fanins'))

        # Create two primary inputs and two gates
        x1 = aig.create_pi()
        x2 = aig.create_pi()
        f1 = aig.create_and(x1, x2)
        f2 = aig.create_or(x1, x2)

        # Create primary outputs
        aig.create_po(f1)
        aig.create_po(f2)

        self.assertEqual(aig.size(), 5)

        # Iterate over nodes
        mask = 0
        counter = 0
        for i, n in enumerate(aig.nodes()):
            mask |= (1 << n)
            counter += i
        self.assertEqual(mask, 31)
        self.assertEqual(counter, 10)

        mask = 0
        for n in aig.nodes():
            mask |= (1 << n)
        self.assertEqual(mask, 31)

        mask = 0
        counter = 0
        for i, n in enumerate(aig.nodes()):
            mask |= (1 << n)
            counter += i
            break  # Stop after first iteration
        self.assertEqual(mask, 1)
        self.assertEqual(counter, 0)

        mask = 0
        for n in aig.nodes():
            mask |= (1 << n)
            break  # Stop after first iteration
        self.assertEqual(mask, 1)

        # Iterate over PIs
        mask = 0
        counter = 0
        for i, n in enumerate(aig.pis()):
            mask |= (1 << n)
            counter += i
        self.assertEqual(mask, 6)
        self.assertEqual(counter, 1)

        mask = 0
        for n in aig.pis():
            mask |= (1 << n)
        self.assertEqual(mask, 6)

        mask = 0
        counter = 0
        for i, n in enumerate(aig.pis()):
            mask |= (1 << n)
            counter += i
            break  # Stop after first iteration
        self.assertEqual(mask, 2)
        self.assertEqual(counter, 0)

        mask = 0
        for n in aig.pis():
            mask |= (1 << n)
            break  # Stop after first iteration
        self.assertEqual(mask, 2)

        # Iterate over POs
        mask = 0
        counter = 0
        for i, s in enumerate(aig.pos()):
            mask |= (1 << aig.get_node(s))
            counter += i
        self.assertEqual(mask, 24)
        self.assertEqual(counter, 1)

        mask = 0
        for s in aig.pos():
            mask |= (1 << aig.get_node(s))
        self.assertEqual(mask, 24)

        mask = 0
        counter = 0
        for i, s in enumerate(aig.pos()):
            mask |= (1 << aig.get_node(s))
            counter += i
            break  # Stop after first iteration
        self.assertEqual(mask, 8)
        self.assertEqual(counter, 0)

        mask = 0
        for s in aig.pos():
            mask |= (1 << aig.get_node(s))
            break  # Stop after first iteration
        self.assertEqual(mask, 8)

        # Iterate over gates
        mask = 0
        counter = 0
        for i, n in enumerate(aig.gates()):
            mask |= (1 << n)
            counter += i
        self.assertEqual(mask, 24)
        self.assertEqual(counter, 1)

        mask = 0
        for n in aig.gates():
            mask |= (1 << n)
        self.assertEqual(mask, 24)

        mask = 0
        counter = 0
        for i, n in enumerate(aig.gates()):
            mask |= (1 << n)
            counter += i
            break  # Stop after first iteration
        self.assertEqual(mask, 8)
        self.assertEqual(counter, 0)

        mask = 0
        for n in aig.gates():
            mask |= (1 << n)
            break  # Stop after first iteration
        self.assertEqual(mask, 8)

        # Iterate over fanins of a gate
        mask = 0
        counter = 0
        for i, s in enumerate(aig.fanins(aig.get_node(f1))):
            mask |= (1 << aig.get_node(s))
            counter += i
        self.assertEqual(mask, 6)
        self.assertEqual(counter, 1)

        mask = 0
        for s in aig.fanins(aig.get_node(f1)):
            mask |= (1 << aig.get_node(s))
        self.assertEqual(mask, 6)

        mask = 0
        counter = 0
        for i, s in enumerate(aig.fanins(aig.get_node(f1))):
            mask |= (1 << aig.get_node(s))
            counter += i
            break  # Stop after first iteration
        self.assertEqual(mask, 2)
        self.assertEqual(counter, 0)

        mask = 0
        for s in aig.fanins(aig.get_node(f1)):
            mask |= (1 << aig.get_node(s))
            break  # Stop after first iteration
        self.assertEqual(mask, 2)


if __name__ == '__main__':
    unittest.main()
