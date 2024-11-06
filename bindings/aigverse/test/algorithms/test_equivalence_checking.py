from aigverse import Aig, equivalence_checking

import unittest


class TestEquivalenceChecking(unittest.TestCase):
    def test_empty_aigs(self):
        aig1 = Aig()
        aig2 = Aig()

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

        self.assertTrue(equivalence_checking(aig1, aig2))
        self.assertTrue(equivalence_checking(aig1, aig1.clone()))

        aig2.create_po(a1)

        with self.assertRaises(RuntimeError):
            equivalence_checking(aig1, aig2)

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

        self.assertFalse(equivalence_checking(aig1, aig2))


if __name__ == '__main__':
    unittest.main()
