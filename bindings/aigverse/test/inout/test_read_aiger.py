from aigverse import *

import unittest
import os

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestReadAiger(unittest.TestCase):
    def test_read_aiger_into_aig(self):
        aig = read_aiger_into_aig(dir_path + "/../resources/mux21.aig")

        self.assertEqual(aig.size(), 7)
        self.assertEqual(aig.nodes(), [i for i in range(7)])
        self.assertEqual(aig.num_gates(), 3)
        self.assertEqual(aig.gates(), [4, 5, 6])
        self.assertEqual(aig.pis(), [1, 2, 3])

        self.assertTrue(aig.is_and(4))
        self.assertTrue(aig.is_and(5))
        self.assertTrue(aig.is_and(6))

        self.assertTrue(aig.is_constant(0))

        self.assertEqual(aig.num_pis(), 3)
        self.assertEqual(aig.pis(), [1, 2, 3])
        self.assertTrue(aig.is_pi(2))
        self.assertTrue(aig.is_pi(3))

        self.assertEqual(aig.num_pos(), 1)

        self.assertEqual(aig.fanins(0), [])
        self.assertEqual(aig.fanins(1), [])
        self.assertEqual(aig.fanins(2), [])
        self.assertEqual(aig.fanins(3), [])
        self.assertEqual(aig.fanins(5), [aig.make_signal(2), aig.make_signal(3)])
        self.assertEqual(aig.fanins(5), [AigSignal(2, 0), AigSignal(3, 0)])
        self.assertEqual(aig.fanins(6), [~aig.make_signal(4), ~aig.make_signal(5)])
        self.assertEqual(aig.fanins(6), [AigSignal(4, 1), AigSignal(5, 1)])

        with self.assertRaises(RuntimeError):
            aig = read_aiger_into_aig(dir_path + "/mux41.aig")

    def test_read_ascii_aiger_into_aig(self):
        aig = read_ascii_aiger_into_aig(dir_path + "/../resources/or.aag")

        self.assertEqual(aig.size(), 4)
        self.assertEqual(aig.nodes(), [i for i in range(4)])
        self.assertEqual(aig.num_gates(), 1)
        self.assertEqual(aig.gates(), [3])
        self.assertEqual(aig.pis(), [1, 2])

        with self.assertRaises(RuntimeError):
            aig = read_ascii_aiger_into_aig(dir_path + "/and.aag")


if __name__ == '__main__':
    unittest.main()
