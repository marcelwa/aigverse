from aigverse import *
import unittest
import os

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestAig(unittest.TestCase):

    def test_read_aiger_into_aig(self):
        network = read_aiger_into_aig(dir_path + "/../resources/mux21.aig")

        self.assertEqual(network.size(), 7)
        self.assertEqual(network.nodes(), [i for i in range(7)])
        self.assertEqual(network.num_gates(), 3)
        self.assertEqual(network.gates(), [4, 5, 6])
        self.assertTrue(network.is_and(6))
        self.assertTrue(network.is_and(7))

        self.assertTrue(network.is_constant(0))

        self.assertEqual(network.num_pis(), 3)
        self.assertEqual(network.pis(), [1, 2, 3])
        self.assertTrue(network.is_pi(2))
        self.assertTrue(network.is_pi(3))

        self.assertEqual(network.num_pos(), 1)

        self.assertEqual(network.fanins(0), [])
        self.assertEqual(network.fanins(1), [])
        self.assertEqual(network.fanins(2), [])
        self.assertEqual(network.fanins(3), [])
        self.assertEqual(network.fanins(5), [network.make_signal(2), network.make_signal(3)])
        self.assertEqual(network.fanins(6), [network.make_signal(4).complement(), network.make_signal(5).complement()])

        with self.assertRaises(RuntimeError):
            network = read_aiger_into_aig(dir_path + "/mux41.v")

    def test_is_gate_functions(self):
        network = read_aiger_into_aig(dir_path + "/../resources/mux21.aig")

        for i in network.nodes():
            self.assertFalse(network.is_maj(i))
            self.assertFalse(network.is_xor(i))


if __name__ == '__main__':
    unittest.main()
