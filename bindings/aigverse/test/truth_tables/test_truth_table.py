from aigverse import TruthTable

import unittest


class TestTruthTable(unittest.TestCase):

    def test_create(self):
        tt_d = TruthTable(5)
        self.assertEqual(tt_d.num_vars(), 5)
        self.assertEqual(tt_d.num_bits(), 32)

    def test_create_nth_var5(self):
        tt_d = TruthTable(5)
        expected_patterns = [
            "10101010101010101010101010101010",  # Variable 0 projection
            "11001100110011001100110011001100",  # Variable 1 projection
            "11110000111100001111000011110000",  # Variable 2 projection
            "11111111000000001111111100000000",  # Variable 3 projection
            "11111111111111110000000000000000",  # Variable 4 projection
        ]

        for i in range(5):
            tt_d.create_nth_var(i)
            self.assertEqual(tt_d.to_binary(), expected_patterns[i])

    def test_create_from_binary_string(self):
        tt_d_str = TruthTable(3)
        tt_d_str.create_from_binary_string("11101000")

        self.assertEqual("11101000", tt_d_str.to_binary())

    def test_create_from_hex_string(self):
        hex_str = "FFFFFFFEFFFEFEE8FFFEFEE8FEE8E880FFFEFEE8FEE8E880FEE8E880E8808000FFFEFEE8FEE8E880FEE8E880E8808000FEE8E880E8808000E880800080000000"
        tt_d_str = TruthTable(9)

        tt_d_str.create_from_hex_string(hex_str)

        self.assertEqual(
            "fffffffefffefee8fffefee8fee8e880fffefee8fee8e880fee8e880e8808000fffefee8fee8e880fee8e880e8808000fee8e880e8808000e880800080000000",
            tt_d_str.to_hex())

    def test_create_constants(self):
        tt_s = TruthTable(0)
        self.assertEqual(tt_s.num_vars(), 0)
        self.assertEqual(tt_s.num_bits(), 1)

        tt_s.create_from_hex_string("0")
        self.assertEqual(tt_s.to_binary(), "0")

        tt_s.create_from_hex_string("1")
        self.assertEqual(tt_s.to_binary(), "1")

    def test_create_one_variable_functions(self):
        tt_s = TruthTable(1)
        self.assertEqual(tt_s.num_vars(), 1)
        self.assertEqual(tt_s.num_bits(), 2)

        # Testing each possible state for a one-variable function
        for hex_val, expected_bin in zip(["0", "1", "2", "3"], ["00", "01", "10", "11"]):
            tt_s.create_from_hex_string(hex_val)
            self.assertEqual(tt_s.to_binary(), expected_bin)

    def test_create_random(self):
        tt_d5 = TruthTable(5)
        tt_d5.create_random()
        print("Random TruthTable for 5 variables:", tt_d5.to_binary())

        tt_d7 = TruthTable(7)
        tt_d7.create_random()
        print("Random TruthTable for 7 variables:", tt_d7.to_binary())

        # A dummy assertion to enable output during testing
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
