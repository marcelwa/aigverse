from aigverse import Aig, DepthAig, TruthTable, simulate

import unittest


class TestSimulation(unittest.TestCase):
    def test_empty_aig(self):
        aig = Aig()

        sim = simulate(aig)

        self.assertEqual(len(sim), 0)

    def test_const0_aig(self):
        aig = Aig()

        aig.create_po(aig.make_signal(0))

        sim = simulate(aig)

        const0 = TruthTable(0)
        const0.create_from_binary_string("0")

        self.assertEqual(len(sim), 1)
        self.assertEqual(sim[0], const0)

    def test_const1_aig(self):
        aig = Aig()

        aig.create_po(~aig.make_signal(0))

        sim = simulate(aig)

        const1 = TruthTable(0)
        const1.create_from_binary_string("1")

        self.assertEqual(len(sim), 1)
        self.assertEqual(sim[0], const1)

    def test_and_aig(self):
        aig = Aig()

        a = aig.create_pi()
        b = aig.create_pi()

        and1 = aig.create_and(a, b)

        aig.create_po(and1)

        sim = simulate(aig)

        conjunction = TruthTable(2)
        conjunction.create_from_binary_string("1000")

        self.assertEqual(len(sim), 1)
        self.assertEqual(sim[0], conjunction)

    def test_or_aig(self):
        aig = Aig()

        a = aig.create_pi()
        b = aig.create_pi()

        or1 = aig.create_or(a, b)

        aig.create_po(or1)

        sim = simulate(aig)

        disjunction = TruthTable(2)
        disjunction.create_from_binary_string("1110")

        self.assertEqual(len(sim), 1)
        self.assertEqual(sim[0], disjunction)

    def test_maj_aig(self):
        aig = Aig()

        a = aig.create_pi()
        b = aig.create_pi()
        c = aig.create_pi()

        maj1 = aig.create_maj(a, b, c)

        aig.create_po(maj1)

        sim = simulate(aig)

        majority = TruthTable(3)
        majority.create_from_hex_string("e8")

        self.assertEqual(len(sim), 1)
        self.assertEqual(sim[0], majority)

    def test_multi_output_aig(self):
        # also test DepthAig
        for ntk in [Aig, DepthAig]:
            aig = ntk()

            a = aig.create_pi()
            b = aig.create_pi()

            and1 = aig.create_and(a, b)
            or1 = aig.create_or(a, b)

            aig.create_po(and1)
            aig.create_po(or1)

            sim = simulate(aig)

            conjunction = TruthTable(2)
            conjunction.create_from_binary_string("1000")

            disjunction = TruthTable(2)
            disjunction.create_from_binary_string("1110")

            self.assertEqual(len(sim), 2)
            self.assertEqual(sim[0], conjunction)
            self.assertEqual(sim[1], disjunction)


if __name__ == '__main__':
    unittest.main()
