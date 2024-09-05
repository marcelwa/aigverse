from aigverse import *

import unittest
import os

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestWriteAiger(unittest.TestCase):
    def test_write_aiger(self):
        aig = Aig()
        x1 = aig.create_pi()
        x2 = aig.create_pi()
        x3 = aig.create_pi()

        a1 = aig.create_and(x1, x2)
        a2 = aig.create_and(x1, x3)
        a3 = aig.create_and(a1, a2)

        aig.create_po(a3)

        write_aiger(aig, dir_path + "/../resources/test.aig")

        aig2 = read_aiger_into_aig(dir_path + "/../resources/test.aig")

        self.assertEqual(aig2.size(), 7)
        self.assertEqual(aig2.nodes(), [i for i in range(7)])
        self.assertEqual(aig2.num_gates(), 3)
        self.assertEqual(aig2.gates(), [4, 5, 6])
        self.assertEqual(aig2.pis(), [1, 2, 3])


if __name__ == '__main__':
    unittest.main()
