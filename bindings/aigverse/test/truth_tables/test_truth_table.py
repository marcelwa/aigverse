from aigverse import TruthTable

import unittest
import copy


class TestTruthTable(unittest.TestCase):

    def test_create(self):
        tt_d = TruthTable(5)
        self.assertEqual(tt_d.num_vars(), 5)
        self.assertEqual(tt_d.num_bits(), 32)

        self.assertEqual(tt_d, TruthTable(5))
        self.assertTrue(tt_d.is_const0())

    def test_shallow_copy(self):
        # Create an original TruthTable and modify it
        tt_original = TruthTable(5)
        tt_original.create_nth_var(0)  # Set to the projection of the 0th variable

        # Make a shallow copy
        tt_shallow = copy.copy(tt_original)

        # Verify that the shallow copy has the same properties as the original
        self.assertEqual(tt_original.to_binary(), tt_shallow.to_binary())
        self.assertEqual(tt_original.num_vars(), tt_shallow.num_vars())

        # Modify the shallow copy and check that the original remains unchanged
        tt_shallow.clear()
        self.assertNotEqual(tt_original.to_binary(), tt_shallow.to_binary())

    def test_deep_copy(self):
        # Create an original TruthTable and modify it
        tt_original = TruthTable(5)
        tt_original.create_nth_var(1)  # Set to the projection of the 1st variable

        # Make a deep copy
        tt_deep = copy.deepcopy(tt_original)

        # Verify that the deep copy has the same properties as the original
        self.assertEqual(tt_original.to_binary(), tt_deep.to_binary())
        self.assertEqual(tt_original.num_vars(), tt_deep.num_vars())

        # Modify the deep copy and check that the original remains unchanged
        tt_deep.clear()
        self.assertNotEqual(tt_original.to_binary(), tt_deep.to_binary())

    def test_assignment_operator(self):
        # Create two distinct TruthTables
        tt_original = TruthTable(2)
        tt_copy = TruthTable(2)

        # Set the original to a specific pattern and assign it to tt_copy
        tt_original.create_from_binary_string("1100")
        tt_copy.__assign__(tt_original)

        # Verify that tt_copy now matches tt_original
        self.assertEqual(tt_copy.to_binary(), tt_original.to_binary())

        # Modify tt_copy and ensure tt_original remains unaffected
        tt_copy.clear()
        self.assertNotEqual(tt_copy.to_binary(), tt_original.to_binary())

    def test_equality_operator(self):
        # Create two identical TruthTables
        tt1 = TruthTable(2)
        tt2 = TruthTable(2)
        tt1.create_from_binary_string("1010")
        tt2.create_from_binary_string("1010")

        # Verify that they are considered equal
        self.assertTrue(tt1 == tt2)

        # Modify one of them and verify they are no longer equal
        tt2.flip_bit(0)
        self.assertFalse(tt1 == tt2)

    def test_inequality_operator(self):
        # Create two different TruthTables
        tt1 = TruthTable(2)
        tt2 = TruthTable(2)
        tt1.create_from_binary_string("1100")
        tt2.create_from_binary_string("1010")

        # Verify that they are considered not equal
        self.assertTrue(tt1 != tt2)

        # Modify one of them to match the other and verify they are now equal
        tt2.create_from_binary_string("1100")
        self.assertFalse(tt1 != tt2)

    def test_less_than_operator(self):
        # Create two TruthTables with different binary representations
        tt1 = TruthTable(2)
        tt2 = TruthTable(2)
        tt1.create_from_binary_string("0110")
        tt2.create_from_binary_string("1000")

        # Verify that tt1 is less than tt2
        self.assertTrue(tt1 < tt2)

        # Swap the binary values and verify tt1 is no longer less than tt2
        tt1.create_from_binary_string("1000")
        tt2.create_from_binary_string("0110")
        self.assertFalse(tt1 < tt2)

        # If they are identical, tt1 < tt2 should be False
        tt2.create_from_binary_string("1000")
        self.assertFalse(tt1 < tt2)

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

    def test_repr(self):
        self.assertEqual(repr(TruthTable(0)), "TruthTable <vars=0>")
        self.assertEqual(repr(TruthTable(1)), "TruthTable <vars=1>")
        self.assertEqual(repr(TruthTable(2)), "TruthTable <vars=2>")
        self.assertEqual(repr(TruthTable(3)), "TruthTable <vars=3>")
        self.assertEqual(repr(TruthTable(4)), "TruthTable <vars=4>")
        self.assertEqual(repr(TruthTable(5)), "TruthTable <vars=5>")

    def test_create_constants(self):
        tt_s = TruthTable(0)
        self.assertEqual(tt_s.num_vars(), 0)
        self.assertEqual(tt_s.num_bits(), 1)

        tt_s.create_from_hex_string("0")
        self.assertEqual(tt_s.to_binary(), "0")
        self.assertTrue(tt_s.is_const0())
        self.assertFalse(tt_s.is_const1())

        tt_s.create_from_hex_string("1")
        self.assertEqual(tt_s.to_binary(), "1")
        self.assertTrue(tt_s.is_const1())
        self.assertFalse(tt_s.is_const0())

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

    def test_all_initially_zero(self):
        tt_s = TruthTable(5)

        for i in range(tt_s.num_bits()):
            self.assertEqual(tt_s.get_bit(i), 0)

    def test_set_get_clear(self):
        tt_s = TruthTable(5)

        for i in range(tt_s.num_bits()):
            tt_s.set_bit(i)
            self.assertEqual(tt_s.get_bit(i), 1)
            tt_s.clear_bit(i)
            self.assertEqual(tt_s.get_bit(i), 0)
            tt_s.flip_bit(i)
            self.assertEqual(tt_s.get_bit(i), 1)
            tt_s.flip_bit(i)
            self.assertEqual(tt_s.get_bit(i), 0)

    def test_count_ones_small(self):
        tt = TruthTable(5)

        for _ in range(100):
            tt.create_random()

            # Count the number of 1s manually
            ctr = sum(tt.get_bit(i) for i in range(tt.num_bits()))

            # Compare with count_ones result
            self.assertEqual(ctr, tt.count_ones())

    def test_count_ones_large(self):
        tt = TruthTable(9)

        for _ in range(100):
            tt.create_random()

            # Count the number of 1s manually
            ctr = sum(tt.get_bit(i) for i in range(tt.num_bits()))

            # Compare with count_ones result
            self.assertEqual(ctr, tt.count_ones())

    def test_print_binary(self):
        # Test binary conversion from hex input
        tt = TruthTable(0)
        tt.create_from_hex_string("0")
        self.assertEqual(tt.to_binary(), "0")

        tt.create_from_hex_string("1")
        self.assertEqual(tt.to_binary(), "1")

        tt = TruthTable(1)
        tt.create_from_hex_string("1")
        self.assertEqual(tt.to_binary(), "01")

        tt.create_from_hex_string("2")
        self.assertEqual(tt.to_binary(), "10")

        tt = TruthTable(2)
        tt.create_from_hex_string("8")
        self.assertEqual(tt.to_binary(), "1000")

        tt = TruthTable(3)
        tt.create_from_hex_string("e8")
        self.assertEqual(tt.to_binary(), "11101000")

        tt = TruthTable(7)
        long_hex = "fffefee8fee8e880fee8e880e8808000"
        expected_binary = (
            "1111111111111110111111101110100011111110111010001110100010000000"
            "1111111011101000111010001000000011101000100000001000000000000000"
        )
        tt.create_from_hex_string(long_hex)
        self.assertEqual(tt.to_binary(), expected_binary)

    def test_print_hex(self):
        # Test hex conversion from hex input
        tt = TruthTable(0)
        tt.create_from_hex_string("0")
        self.assertEqual(tt.to_hex(), "0")

        tt.create_from_hex_string("1")
        self.assertEqual(tt.to_hex(), "1")

        tt = TruthTable(1)
        tt.create_from_hex_string("1")
        self.assertEqual(tt.to_hex(), "1")

        tt.create_from_hex_string("2")
        self.assertEqual(tt.to_hex(), "2")

        tt = TruthTable(2)
        tt.create_from_hex_string("8")
        self.assertEqual(tt.to_hex(), "8")

        tt = TruthTable(3)
        tt.create_from_hex_string("e8")
        self.assertEqual(tt.to_hex(), "e8")

        tt = TruthTable(7)
        long_hex = "fffefee8fee8e880fee8e880e8808000"
        tt.create_from_hex_string(long_hex)
        self.assertEqual(tt.to_hex(), long_hex.lower())

    def test_hash(self):
        counts = {}

        for _ in range(10):
            tt = TruthTable(10)
            tt.create_random()
            counts[tt] = tt.count_ones()  # Use the TruthTable as a dictionary key

        # Check that the number of unique entries in counts does not exceed 10
        self.assertLessEqual(len(counts), 10)


if __name__ == '__main__':
    unittest.main()
