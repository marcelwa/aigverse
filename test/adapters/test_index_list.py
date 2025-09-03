from __future__ import annotations

import pytest

from aigverse import Aig, AigIndexList, TruthTable, equivalence_checking, simulate, to_aig, to_index_list


def test_decode_empty_index_list_into_aig() -> None:
    il = AigIndexList()

    aig = to_aig(il)

    assert aig.num_gates() == 0
    assert aig.num_pis() == 0
    assert aig.num_pos() == 0

    result = simulate(aig)

    assert len(result) == 0


def test_encode_empty_aig_into_index_list() -> None:
    aig = Aig()

    il = to_index_list(aig)

    assert il.num_pis() == 0
    assert il.num_pos() == 0
    assert il.num_gates() == 0
    assert il.size() == 3  # [0, 0, 0]
    assert isinstance(il.raw(), list)
    assert il.raw() == [0, 0, 0]
    assert isinstance(str(il), str)
    assert str(il) == "{0, 0, 0}"
    assert isinstance(repr(il), str)
    assert repr(il) == "IndexList(#PIs: 0, #POs: 0, #Gates: 0, Gates: [], POs: [])"


def test_decode_pi_only_index_list_into_aig() -> None:
    il = AigIndexList()

    il.add_inputs(4)
    assert il.num_pis() == 4

    aig = to_aig(il)

    assert aig.num_gates() == 0
    assert aig.num_pis() == 4
    assert aig.num_pos() == 0


def test_encode_pi_only_aig_into_index_list() -> None:
    aig = Aig()
    aig.create_pi()
    aig.create_pi()
    aig.create_pi()
    aig.create_pi()

    il = to_index_list(aig)

    assert il.num_pis() == 4
    assert il.num_pos() == 0
    assert il.num_gates() == 0
    assert il.size() == 3  # [4, 0, 0]
    assert isinstance(il.raw(), list)
    assert il.raw() == [4, 0, 0]
    assert isinstance(str(il), str)
    assert str(il) == "{4, 0, 0}"
    assert isinstance(repr(il), str)
    assert repr(il) == "IndexList(#PIs: 4, #POs: 0, #Gates: 0, Gates: [], POs: [])"


def test_decode_index_list_into_aig() -> None:
    il = AigIndexList([4, 1, 3, 2, 4, 6, 8, 12, 10, 14])

    aig = to_aig(il)

    assert aig.num_gates() == 5
    assert aig.num_pis() == 4
    assert aig.num_pos() == 1

    tt_spec = TruthTable(4)
    tt_spec.create_from_hex_string("7888")

    tt_aig = simulate(aig)[0]

    assert tt_spec == tt_aig


def test_implicit_conversion() -> None:
    il = [4, 1, 3, 2, 4, 6, 8, 12, 10, 14]

    aig = to_aig(il)  # type: ignore[arg-type]

    assert aig.num_gates() == 5
    assert aig.num_pis() == 4
    assert aig.num_pos() == 1

    tt_spec = TruthTable(4)
    tt_spec.create_from_hex_string("7888")

    tt_aig = simulate(aig)[0]

    assert tt_spec == tt_aig


def test_encode_aig_into_index_list() -> None:
    aig = Aig()
    a = aig.create_pi()
    b = aig.create_pi()
    c = aig.create_pi()
    d = aig.create_pi()
    t0 = aig.create_and(a, b)
    t1 = aig.create_and(c, d)
    t2 = aig.create_xor(t0, t1)
    aig.create_po(t2)

    il = to_index_list(aig)

    assert il.num_pis() == 4
    assert il.num_pos() == 1
    assert il.num_gates() == 5
    assert il.size() == 14
    assert isinstance(il.raw(), list)
    assert il.raw() == [4, 1, 5, 2, 4, 6, 8, 10, 13, 11, 12, 15, 17, 19]
    assert isinstance(str(il), str)
    assert str(il) == "{4, 1, 5, 2, 4, 6, 8, 10, 13, 11, 12, 15, 17, 19}"
    assert isinstance(repr(il), str)
    assert (
        repr(il)
        == "IndexList(#PIs: 4, #POs: 1, #Gates: 5, Gates: [(2, 4), (6, 8), (10, 13), (11, 12), (15, 17)], POs: [19])"
    )


def test_encode_decode_aig_with_inverted_signals() -> None:
    aig = Aig()
    a = aig.create_pi()
    b = aig.create_pi()
    c = aig.create_pi()

    t0 = aig.create_and(a, b)
    t1 = aig.create_and(b, ~c)
    t2 = aig.create_and(~t0, ~t1)

    aig.create_po(~t1)
    aig.create_po(t2)

    il = to_index_list(aig)

    assert il.num_pis() == 3
    assert il.num_pos() == 2
    assert il.num_gates() == 3
    assert il.size() == 11
    assert il.raw() == [3, 2, 3, 2, 4, 4, 7, 9, 11, 11, 12]

    aig2 = to_aig(il)

    assert aig2.num_pis() == 3
    assert aig2.num_pos() == 2
    assert aig2.num_gates() == 3

    assert equivalence_checking(aig, aig2)


def test_aig_index_list_methods() -> None:
    il = AigIndexList(3)
    assert il.num_pis() == 3

    il.add_and(1, 2)
    il.add_and(2, 3)
    il.add_output(5)

    assert il.num_gates() == 2
    assert il.num_pos() == 1
    assert isinstance(il.gates(), list)
    assert isinstance(il.pos(), list)
    assert len(il) == il.size()

    il.clear()

    # PIs will be left
    assert il.size() == 3


def test_index_list_iter_get_set_item() -> None:
    il = AigIndexList([4, 1, 3, 2, 4, 6, 8, 12, 10, 14])

    # Test __iter__
    assert list(iter(il)) == [4, 1, 3, 2, 4, 6, 8, 12, 10, 14]

    # Test __getitem__
    assert il[0] == 4
    assert il[1] == 1
    assert il[2] == 3

    # Test __setitem__
    il[2] = 99
    assert il[2] == 99

    # Restore original value
    il[2] = 3
    assert il[2] == 3

    # Test out-of-bounds
    with pytest.raises(IndexError):
        _ = il[100]
    with pytest.raises(IndexError):
        il[100] = 1


def test_index_list_to_python_list() -> None:
    il = AigIndexList([4, 1, 3, 2, 4, 6, 8, 12, 10, 14])
    pylist = [il.num_pis(), il.num_pos(), il.num_gates(), il.gates(), il.pos()]
    assert pylist == [4, 1, 3, [(2, 4), (6, 8), (12, 10)], [14]]

    pylist = [int(i) for i in il]
    assert pylist == [4, 1, 3, 2, 4, 6, 8, 12, 10, 14]
