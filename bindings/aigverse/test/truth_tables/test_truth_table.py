from __future__ import annotations

import copy

import pytest

from aigverse import TruthTable, cofactor0, cofactor1, ternary_majority


def test_create() -> None:
    tt_d = TruthTable(5)
    assert tt_d.num_vars() == 5
    assert tt_d.num_bits() == 32

    assert tt_d == TruthTable(5)
    assert tt_d.is_const0()


def test_shallow_copy() -> None:
    # Create an original TruthTable and modify it
    tt_original = TruthTable(5)
    tt_original.create_nth_var(0)  # Set to the projection of the 0th variable

    # Make a shallow copy
    tt_shallow = copy.copy(tt_original)

    # Verify that the shallow copy has the same properties as the original
    assert tt_original.to_binary() == tt_shallow.to_binary()
    assert tt_original.num_vars() == tt_shallow.num_vars()

    # Modify the shallow copy and check that the original remains unchanged
    tt_shallow.clear()
    assert tt_original.to_binary() != tt_shallow.to_binary()


def test_deep_copy() -> None:
    # Create an original TruthTable and modify it
    tt_original = TruthTable(5)
    tt_original.create_nth_var(1)  # Set to the projection of the 1st variable

    # Make a deep copy
    tt_deep = copy.deepcopy(tt_original)

    # Verify that the deep copy has the same properties as the original
    assert tt_original.to_binary() == tt_deep.to_binary()
    assert tt_original.num_vars() == tt_deep.num_vars()

    # Modify the deep copy and check that the original remains unchanged
    tt_deep.clear()
    assert tt_original.to_binary() != tt_deep.to_binary()


def test_assignment_operator() -> None:
    # Create two distinct TruthTables
    tt_original = TruthTable(2)
    tt_copy = TruthTable(2)

    # Set the original to a specific pattern and assign it to tt_copy
    tt_original.create_from_binary_string("1100")
    tt_copy.__assign__(tt_original)

    # Verify that tt_copy now matches tt_original
    assert tt_copy.to_binary() == tt_original.to_binary()

    # Modify tt_copy and ensure tt_original remains unaffected
    tt_copy.clear()
    assert tt_copy.to_binary() != tt_original.to_binary()


def test_equality_operator() -> None:
    # Create two identical TruthTables
    tt1 = TruthTable(2)
    tt2 = TruthTable(2)
    tt1.create_from_binary_string("1010")
    tt2.create_from_binary_string("1010")

    # Verify that they are considered equal
    assert tt1 == tt2

    # Modify one of them and verify they are no longer equal
    tt2.flip_bit(0)
    assert tt1 != tt2


def test_inequality_operator() -> None:
    # Create two different TruthTables
    tt1 = TruthTable(2)
    tt2 = TruthTable(2)
    tt1.create_from_binary_string("1100")
    tt2.create_from_binary_string("1010")

    # Verify that they are considered not equal
    assert tt1 != tt2

    # Modify one of them to match the other and verify they are now equal
    tt2.create_from_binary_string("1100")
    assert tt1 == tt2


def test_less_than_operator() -> None:
    # Create two TruthTables with different binary representations
    tt1 = TruthTable(2)
    tt2 = TruthTable(2)
    tt1.create_from_binary_string("0110")
    tt2.create_from_binary_string("1000")

    # Verify that tt1 is less than tt2
    assert tt1 < tt2

    # Swap the binary values and verify tt1 is no longer less than tt2
    tt1.create_from_binary_string("1000")
    tt2.create_from_binary_string("0110")
    assert not tt1 < tt2

    # If they are identical, tt1 < tt2 should be False
    tt2.create_from_binary_string("1000")
    assert not tt1 < tt2


def test_create_nth_var5() -> None:
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
        assert tt_d.to_binary() == expected_patterns[i]


def test_create_from_binary_string() -> None:
    tt_d_str = TruthTable(3)
    tt_d_str.create_from_binary_string("11101000")

    assert tt_d_str.to_binary() == "11101000"


def test_create_from_hex_string() -> None:
    hex_str = (
        "FFFFFFFEFFFEFEE8FFFEFEE8FEE8E880FFFEFEE8FEE8E880FEE8E880E8808000"
        "FFFEFEE8FEE8E880FEE8E880E8808000FEE8E880E8808000E880800080000000"
    )
    tt_d_str = TruthTable(9)

    tt_d_str.create_from_hex_string(hex_str)

    assert tt_d_str.to_hex() == (
        "fffffffefffefee8fffefee8fee8e880fffefee8fee8e880fee8e880e8808000"
        "fffefee8fee8e880fee8e880e8808000fee8e880e8808000e880800080000000"
    )


def test_repr() -> None:
    assert repr(TruthTable(0)) == "TruthTable <vars=0>"
    assert repr(TruthTable(1)) == "TruthTable <vars=1>"
    assert repr(TruthTable(2)) == "TruthTable <vars=2>"
    assert repr(TruthTable(3)) == "TruthTable <vars=3>"
    assert repr(TruthTable(4)) == "TruthTable <vars=4>"
    assert repr(TruthTable(5)) == "TruthTable <vars=5>"


def test_create_constants() -> None:
    tt_s = TruthTable(0)
    assert tt_s.num_vars() == 0
    assert tt_s.num_bits() == 1

    tt_s.create_from_hex_string("0")
    assert tt_s.to_binary() == "0"
    assert tt_s.is_const0()
    assert not tt_s.is_const1()

    tt_s.create_from_hex_string("1")
    assert tt_s.to_binary() == "1"
    assert tt_s.is_const1()
    assert not tt_s.is_const0()


def test_create_one_variable_functions() -> None:
    tt_s = TruthTable(1)
    assert tt_s.num_vars() == 1
    assert tt_s.num_bits() == 2

    # Testing each possible state for a one-variable function
    for hex_val, expected_bin in zip(["0", "1", "2", "3"], ["00", "01", "10", "11"]):
        tt_s.create_from_hex_string(hex_val)
        assert tt_s.to_binary() == expected_bin


def test_create_random() -> None:
    tt_d5 = TruthTable(5)
    tt_d5.create_random()

    tt_d7 = TruthTable(7)
    tt_d7.create_random()

    # A dummy assertion to enable output during testing
    assert True


def test_all_initially_zero() -> None:
    tt_s = TruthTable(5)

    for i in range(tt_s.num_bits()):
        assert tt_s.get_bit(i) == 0


def test_set_get_clear() -> None:
    tt_s = TruthTable(5)

    for i in range(tt_s.num_bits()):
        tt_s.set_bit(i)
        assert tt_s.get_bit(i) == 1
        tt_s.clear_bit(i)
        assert tt_s.get_bit(i) == 0
        tt_s.flip_bit(i)
        assert tt_s.get_bit(i) == 1
        tt_s.flip_bit(i)
        assert tt_s.get_bit(i) == 0


def test_count_ones_small() -> None:
    tt = TruthTable(5)

    for _ in range(100):
        tt.create_random()

        # Count the number of 1s manually
        ctr = sum(tt.get_bit(i) for i in range(tt.num_bits()))

        # Compare with count_ones result
        assert ctr == tt.count_ones()


def test_count_ones_large() -> None:
    tt = TruthTable(9)

    for _ in range(100):
        tt.create_random()

        # Count the number of 1s manually
        ctr = sum(tt.get_bit(i) for i in range(tt.num_bits()))

        # Compare with count_ones result
        assert ctr == tt.count_ones()


def test_simple_operators() -> None:
    a = TruthTable(2)
    a.create_from_binary_string("1001")

    b = TruthTable(2)
    b.create_from_binary_string("1100")

    a_and_b = TruthTable(2)
    a_and_b.create_from_binary_string("1000")

    a_or_b = TruthTable(2)
    a_or_b.create_from_binary_string("1101")

    a_xor_b = TruthTable(2)
    a_xor_b.create_from_binary_string("0101")

    assert a & b == a_and_b
    assert a | b == a_or_b
    assert a ^ b == a_xor_b
    assert a ^ b == (a | b) & ~(a & b)


def test_complex_operators() -> None:
    a = TruthTable(7)
    b = TruthTable(7)
    c = TruthTable(7)
    d = TruthTable(7)
    e = TruthTable(7)
    f = TruthTable(7)
    g = TruthTable(7)

    a.create_nth_var(0)
    b.create_nth_var(1)
    c.create_nth_var(2)
    d.create_nth_var(3)
    e.create_nth_var(4)
    f.create_nth_var(5)
    g.create_nth_var(6)

    maj7 = TruthTable(7)
    maj7.create_majority()

    def special_func(
        a: TruthTable,
        b: TruthTable,
        c: TruthTable,
        d: TruthTable,
        e: TruthTable,
        f: TruthTable,
    ) -> TruthTable:
        abc = ternary_majority(a, b, c)
        return ternary_majority(abc, d, ternary_majority(e, f, abc))

    # Check symmetry in variables {a, b, c}
    assert special_func(a, b, c, d, e, f) == special_func(a, c, b, d, e, f)
    assert special_func(a, b, c, d, e, f) == special_func(b, a, c, d, e, f)
    assert special_func(a, b, c, d, e, f) == special_func(b, c, a, d, e, f)
    assert special_func(a, b, c, d, e, f) == special_func(c, a, b, d, e, f)
    assert special_func(a, b, c, d, e, f) == special_func(c, b, a, d, e, f)

    # Check symmetry in variables {d, e, f}
    assert special_func(a, b, c, d, e, f) == special_func(a, b, c, d, f, e)
    assert special_func(a, b, c, d, e, f) == special_func(a, b, c, e, d, f)
    assert special_func(a, b, c, d, e, f) == special_func(a, b, c, e, f, d)
    assert special_func(a, b, c, d, e, f) == special_func(a, b, c, f, d, e)
    assert special_func(a, b, c, d, e, f) == special_func(a, b, c, f, e, d)

    sf0 = special_func(a, b, c, d, e, f)
    sf1 = special_func(d, e, f, a, b, c)

    th0 = cofactor0(maj7, 6)  # threshold-4 function
    th1 = cofactor1(maj7, 6)  # threshold-3 function
    te = th1 & ~th0  # =3 function

    assert (~th0 | (sf0 & sf1)).is_const1()
    assert (th0 | (~sf0 | ~sf1)).is_const1()
    assert (~th1 | (sf0 | sf1)).is_const1()
    assert (th1 | (~sf0 & ~sf1)).is_const1()

    factor1 = d ^ e ^ f
    factor2 = a ^ b ^ c

    assert sf0 == ((factor1 & th1) ^ (~factor1 & th0))
    assert sf1 == ((factor1 & th0) ^ (~factor1 & th1))
    assert sf0 == ((factor2 & th0) ^ (~factor2 & th1))
    assert sf1 == ((factor2 & th1) ^ (~factor2 & th0))

    assert sf0 == (th0 | (factor1 & te))
    assert sf1 == (th0 | (factor2 & te))

    assert ternary_majority(sf0, g, sf1) == maj7


def test_print_binary() -> None:
    # Test binary conversion from hex input
    tt = TruthTable(0)
    tt.create_from_hex_string("0")
    assert tt.to_binary() == "0"

    tt.create_from_hex_string("1")
    assert tt.to_binary() == "1"

    tt = TruthTable(1)
    tt.create_from_hex_string("1")
    assert tt.to_binary() == "01"

    tt.create_from_hex_string("2")
    assert tt.to_binary() == "10"

    tt = TruthTable(2)
    tt.create_from_hex_string("8")
    assert tt.to_binary() == "1000"

    tt = TruthTable(3)
    tt.create_from_hex_string("e8")
    assert tt.to_binary() == "11101000"

    tt = TruthTable(7)
    long_hex = "fffefee8fee8e880fee8e880e8808000"
    expected_binary = (
        "1111111111111110111111101110100011111110111010001110100010000000"
        "1111111011101000111010001000000011101000100000001000000000000000"
    )
    tt.create_from_hex_string(long_hex)
    assert tt.to_binary() == expected_binary


def test_print_hex() -> None:
    # Test hex conversion from hex input
    tt = TruthTable(0)
    tt.create_from_hex_string("0")
    assert tt.to_hex() == "0"

    tt.create_from_hex_string("1")
    assert tt.to_hex() == "1"

    tt = TruthTable(1)
    tt.create_from_hex_string("1")
    assert tt.to_hex() == "1"

    tt.create_from_hex_string("2")
    assert tt.to_hex() == "2"

    tt = TruthTable(2)
    tt.create_from_hex_string("8")
    assert tt.to_hex() == "8"

    tt = TruthTable(3)
    tt.create_from_hex_string("e8")
    assert tt.to_hex() == "e8"

    tt = TruthTable(7)
    long_hex = "fffefee8fee8e880fee8e880e8808000"
    tt.create_from_hex_string(long_hex)
    assert tt.to_hex() == long_hex.lower()


def test_hash() -> None:
    counts = {}

    for _ in range(10):
        tt = TruthTable(10)
        tt.create_random()
        counts[tt] = tt.count_ones()  # Use the TruthTable as a dictionary key

    # Check that the number of unique entries in counts does not exceed 10
    assert len(counts) <= 10


def test_list_like_access() -> None:
    tt = TruthTable(3)  # 8 bits
    assert len(tt) == 8

    # Initially all zero
    assert all(b is False for b in tt)

    # __setitem__ / __getitem__
    tt[0] = True
    tt[2] = True
    tt[5] = True

    assert tt[0] is True
    assert tt[1] is False
    assert tt[2] is True
    assert tt[3] is False
    assert tt[4] is False
    assert tt[5] is True
    assert tt[6] is False
    assert tt[7] is False

    # Negative indexing
    assert tt[-1] is False  # bit 7
    assert tt[-3] is True  # bit 5
    assert tt[-8] is True  # bit 0

    tt[-1] = True  # set bit 7
    assert tt[7] is True

    # __iter__
    bits = list(tt)  # type: ignore[unreachable]  # mypy false positive
    expected_bits = [True, False, True, False, False, True, False, True]
    assert bits == expected_bits

    # Test clearing bits
    tt[0] = False
    assert tt[0] is False
    bits = list(tt)
    expected_bits[0] = False
    assert bits == expected_bits

    # Test out of bounds
    with pytest.raises(IndexError):
        _ = tt[8]
    with pytest.raises(IndexError):
        tt[8] = False
    with pytest.raises(IndexError):
        _ = tt[-9]
    with pytest.raises(IndexError):
        tt[-9] = True
