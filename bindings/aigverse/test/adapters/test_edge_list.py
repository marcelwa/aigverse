from aigverse import *

import unittest


class EdgeTest(unittest.TestCase):
    def test_aig_edge(self):
        null_edge = AigEdge()

        self.assertIs(type(null_edge), AigEdge)

        self.assertEqual(null_edge.source, 0)
        self.assertEqual(null_edge.target, 0)
        self.assertEqual(null_edge.weight, 0)

        self.assertEqual(null_edge, AigEdge(0, 0, 0))
        self.assertNotEqual(null_edge, AigEdge(1, 0, 0))
        self.assertNotEqual(null_edge, AigEdge(1, 1, 0))
        self.assertNotEqual(null_edge, AigEdge(1, 1, 1))

        self.assertEqual(null_edge.__repr__(), "Edge(s:0,t:0,w:0)")

        edge = AigEdge(1, 2, 3)

        self.assertIs(type(edge), AigEdge)

        self.assertEqual(edge.source, 1)
        self.assertEqual(edge.target, 2)
        self.assertEqual(edge.weight, 3)

        self.assertEqual(edge, AigEdge(1, 2, 3))
        self.assertNotEqual(edge, AigEdge(1, 2, 4))
        self.assertNotEqual(edge, AigEdge(1, 3, 3))
        self.assertNotEqual(edge, AigEdge(2, 2, 3))

        self.assertEqual(edge.__repr__(), "Edge(s:1,t:2,w:3)")

    def test_aig_edge_list(self):
        edge_list = AigEdgeList(Aig())

        self.assertIs(type(edge_list), AigEdgeList)

        self.assertEqual(len(edge_list), 0)

        edge_list.append(AigEdge(1, 2, 3))
        edge_list.append(AigEdge(2, 3, 4))
        edge_list.append(AigEdge(3, 4, 5))

        self.assertEqual(len(edge_list), 3)

        self.assertEqual(edge_list[0], AigEdge(1, 2, 3))
        self.assertEqual(edge_list[1], AigEdge(2, 3, 4))
        self.assertEqual(edge_list[2], AigEdge(3, 4, 5))

        edge_list[0] = AigEdge(4, 5, 6)
        edge_list[1] = AigEdge(5, 6, 7)
        edge_list[2] = AigEdge(6, 7, 8)

        self.assertEqual(edge_list[0], AigEdge(4, 5, 6))
        self.assertEqual(edge_list[1], AigEdge(5, 6, 7))
        self.assertEqual(edge_list[2], AigEdge(6, 7, 8))

        with self.assertRaises(IndexError):
            edge_list[3]

        with self.assertRaises(IndexError):
            edge_list[3] = AigEdge(7, 8, 9)

        self.assertEqual(edge_list.__repr__(), "EdgeList({Edge(s:4,t:5,w:6), Edge(s:5,t:6,w:7), Edge(s:6,t:7,w:8)})")

        edge_list.clear()

        self.assertEqual(len(edge_list), 0)

        self.assertEqual(edge_list.__repr__(), "EdgeList({})")

    def test_aig_to_edge_list(self):
        aig = Aig()

        x1 = aig.create_pi()
        x2 = aig.create_pi()
        x3 = aig.create_pi()

        y1 = aig.create_and(x1, ~x2)
        y2 = aig.create_and(x2, x3)
        y3 = aig.create_and(~y1, y2)

        aig.create_po(y3)

        edge_list = to_edge_list(aig)

        self.assertIs(type(edge_list), AigEdgeList)

        self.assertEqual(len(edge_list), 6)

        self.assertIn(AigEdge(1, 4, 0), edge_list)
        self.assertIn(AigEdge(2, 5, 0), edge_list)
        self.assertIn(AigEdge(2, 4, 1), edge_list)
        self.assertIn(AigEdge(3, 5, 0), edge_list)
        self.assertIn(AigEdge(4, 6, 1), edge_list)
        self.assertIn(AigEdge(5, 6, 0), edge_list)


if __name__ == '__main__':
    unittest.main()
