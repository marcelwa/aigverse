from aigverse import Aig, sop_refactoring, equivalence_checking

import unittest


class TestAigRefactoring(unittest.TestCase):
    def test_empty_aigs(self):
        aig1 = Aig()
        aig2 = aig1.clone()

        sop_refactoring(aig1)

        self.assertTrue(equivalence_checking(aig1, aig2))

    def test_simple_aigs(self):
        aig1 = Aig()
        aig2 = Aig()

        a1 = aig1.create_pi()
        b1 = aig1.create_pi()

        and1 = aig1.create_and(a1, b1)

        aig1.create_po(and1)
        aig1.create_po(b1)

        a2 = aig2.create_pi()
        b2 = aig2.create_pi()

        and2 = aig2.create_and(a2, b2)

        aig2.create_po(and2)
        aig2.create_po(b2)

        sop_refactoring(aig1)

        self.assertTrue(equivalence_checking(aig1, aig2))
        self.assertTrue(equivalence_checking(aig1, aig1.clone()))

    def test_aig_and_its_negated_copy(self):
        aig1 = Aig()

        a1 = aig1.create_pi()
        b1 = aig1.create_pi()
        c1 = aig1.create_pi()

        and1 = aig1.create_and(a1, b1)
        and2 = aig1.create_and(~a1, c1)
        and3 = aig1.create_and(and1, and2)

        aig2 = aig1.clone()

        aig1.create_po(and3)

        aig2.create_po(~and3)

        sop_refactoring(aig1)

        self.assertFalse(equivalence_checking(aig1, aig2))

        sop_refactoring(aig2)

        self.assertFalse(equivalence_checking(aig1, aig2))

    def test_equivalent_node_merger(self):
        # x0 * !(!x0 * !x1) == > x0 (reduction of 2 nodes)
        aig1 = Aig()
        x0 = aig1.create_pi()
        x1 = aig1.create_pi()
        n0 = aig1.create_and(~x0, ~x1)
        n1 = aig1.create_and(x0, ~n0)
        aig1.create_po(n1)

        aig_before = aig1.clone()

        sop_refactoring(aig1)

        self.assertEqual(aig1.size(), aig_before.size() - 2)

        self.assertTrue(equivalence_checking(aig1, aig_before))

    def test_positive_divisor_substitution(self):
        # x1 * ( x0 * x1 ) ==> x0 * x1 (reduction of 1 node)
        aig2 = Aig()
        x0 = aig2.create_pi()
        x1 = aig2.create_pi()
        n0 = aig2.create_and(x0, x1)
        n1 = aig2.create_and(x1, n0)
        aig2.create_po(n1)

        aig_before = aig2.clone()

        sop_refactoring(aig2)

        self.assertEqual(aig2.size(), aig_before.size() - 1)

        self.assertTrue(equivalence_checking(aig2, aig_before))

    def test_negative_divisor_substitution(self):
        # !x0 * !(!x0 * !x1) == > !x0 * x1 (reduction of 2 nodes)
        aig = Aig()
        x0 = aig.create_pi()
        x1 = aig.create_pi()
        n0 = aig.create_and(~x0, ~x1)
        n1 = aig.create_and(x0, ~n0)
        aig.create_po(n1)

        aig_before = aig.clone()

        sop_refactoring(aig)

        self.assertEqual(aig.size(), aig_before.size() - 2)

        self.assertTrue(equivalence_checking(aig, aig_before))

    def test_parameters(self):
        aig = Aig()

        a = aig.create_pi()
        b = aig.create_pi()

        and1 = aig.create_and(~a, ~b)
        and2 = aig.create_and(a, ~and1)

        aig.create_po(and2)

        aig2 = aig.clone()

        sop_refactoring(aig, max_pis=2, allow_zero_gain=True, use_reconvergence_cut=False, use_dont_cares=True,
                        verbose=True)

        self.assertTrue(equivalence_checking(aig, aig2))


if __name__ == '__main__':
    unittest.main()
