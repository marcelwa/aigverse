from __future__ import annotations

import copy
import copyreg
import pickle
from typing import Any

import pytest

from aigverse.algorithms import cleanup_dangling, equivalence_checking, simulate
from aigverse.networks import Aig, AigSignal


def test_aig_constants() -> None:
    aig = Aig()
    assert aig.size == 1
    assert aig.num_gates == 0
    assert aig.num_pis == 0
    assert aig.num_pos == 0
    assert aig.is_combinational

    assert aig.nodes() == [0]
    assert aig.gates() == []
    assert aig.pis() == []
    assert aig.pos() == []

    assert aig.is_constant(0)
    c0 = aig.get_constant(False)
    assert aig.is_constant(aig.get_node(c0))
    assert not aig.is_pi(aig.get_node(c0))
    assert aig.get_node(c0) == 0
    assert not aig.is_complemented(c0)

    c1 = aig.get_constant(True)
    assert aig.is_constant(aig.get_node(c1))
    assert not aig.is_pi(aig.get_node(c1))
    assert aig.get_node(c1) == 0
    assert aig.is_complemented(c1)

    assert c0 != c1
    assert aig.get_node(c0) == aig.get_node(c1)
    assert c0 == ~c1
    assert ~c0 == c1
    assert ~c0 != ~c1
    assert -c0 == c1
    assert -c1 == c1
    assert c0 == +c1
    assert c0 == +c0


def test_aig_primary_inputs() -> None:
    aig = Aig()

    a = aig.create_pi()
    b = aig.create_pi()

    assert aig.size == 3
    assert aig.num_pis == 2
    assert aig.num_gates == 0
    assert aig.is_pi(aig.get_node(a))
    assert aig.is_pi(aig.get_node(b))
    assert aig.pi_index(aig.get_node(a)) == 0
    assert aig.pi_index(aig.get_node(b)) == 1

    assert isinstance(a, AigSignal)

    assert a.index == 1
    assert a.complement is False
    assert a.data == 2

    a = ~a
    assert a.index == 1
    assert a.complement is True
    assert a.data == 3

    a = +a
    assert a.index == 1
    assert a.complement is False
    assert a.data == 2

    a = +a
    assert a.index == 1
    assert a.complement is False
    assert a.data == 2

    a = -a
    assert a.index == 1
    assert a.complement is True
    assert a.data == 3

    a = -a
    assert a.index == 1
    assert a.complement is True
    assert a.data == 3

    a ^= True
    assert a.index == 1
    assert a.complement is False
    assert a.data == 2

    a ^= True
    assert a.index == 1
    assert a.complement is True
    assert a.data == 3


def test_aig_primary_outputs(aig_with_single_pi: tuple[Aig, AigSignal]) -> None:
    aig, x1 = aig_with_single_pi

    c0 = aig.get_constant(False)

    assert aig.size == 2
    assert aig.num_pis == 1
    assert aig.num_pos == 0

    aig.create_po(c0)
    aig.create_po(x1)
    aig.create_po(~x1)

    assert aig.size == 2
    assert aig.num_pos == 3

    assert aig.pos() == [c0, x1, ~x1]


@pytest.mark.parametrize(("method", "complement"), [("create_buf", False), ("create_not", True)], ids=["buf", "not"])
def test_aig_unary_operations(aig_with_single_pi: tuple[Aig, AigSignal], method: str, *, complement: bool) -> None:
    aig, x1 = aig_with_single_pi
    assert aig.size == 2

    result = getattr(aig, method)(x1)
    assert result.index == x1.index
    assert result.complement is complement
    assert aig.size == 2


def test_aig_binary_operations(aig_with_two_pis: tuple[Aig, AigSignal, AigSignal]) -> None:
    aig, x1, x2 = aig_with_two_pis
    assert aig.size == 3

    for create, create_complement, expected_size in [
        (aig.create_and, aig.create_nand, 4),
        (aig.create_or, aig.create_nor, 5),
        (aig.create_xor, aig.create_xnor, 8),
    ]:
        signal = create(x1, x2)
        assert aig.size == expected_size, create.__name__
        complement = create_complement(x1, x2)
        assert aig.size == expected_size, create_complement.__name__
        assert signal == ~complement
        aig.create_po(signal)
        aig.create_po(complement)

    assert [tt.to_binary() for tt in simulate(aig)] == ["1000", "0111", "1110", "0001", "0110", "1001"]


def test_aig_hash_nodes(aig_with_two_pis: tuple[Aig, AigSignal, AigSignal]) -> None:
    aig, a, b = aig_with_two_pis

    f = aig.create_and(a, b)
    g = aig.create_and(a, b)

    assert aig.size == 4
    assert aig.num_gates == 1

    assert aig.get_node(f) == aig.get_node(g)


def test_aig_clone_network(aig_with_single_and: tuple[Aig, AigSignal]) -> None:
    aig0, f0 = aig_with_single_and

    assert aig0.size == 4
    assert aig0.num_gates == 1

    aig1 = aig0
    aig_clone = aig0.clone()

    c = aig1.create_pi()
    aig1.create_and(f0, c)

    assert aig0.size == 6
    assert aig0.num_gates == 2

    assert aig_clone.size == 4
    assert aig_clone.num_gates == 1


def test_aig_clone_node(
    aig_with_single_and: tuple[Aig, AigSignal],
    aig_with_two_pis: tuple[Aig, AigSignal, AigSignal],
) -> None:
    aig1, f1 = aig_with_single_and
    aig2, a2, b2 = aig_with_two_pis

    assert aig1.size == 4

    assert aig2.size == 3

    f2 = aig2.clone_node(aig1, aig1.get_node(f1), [a2, b2])

    assert aig2.size == 4

    assert aig2.fanins(aig2.get_node(f2)) == [a2, b2]


def test_aig_structural_properties(
    aig_with_and_or_outputs: tuple[Aig, AigSignal, AigSignal, AigSignal, AigSignal],
) -> None:
    aig, x1, x2, f1, f2 = aig_with_and_or_outputs

    assert aig.size == 5
    assert aig.num_pis == 2
    assert aig.num_pos == 2
    assert aig.num_gates == 2

    assert aig.fanin_size(aig.get_node(x1)) == 0
    assert aig.fanin_size(aig.get_node(x2)) == 0
    assert aig.fanin_size(aig.get_node(f1)) == 2
    assert aig.fanin_size(aig.get_node(f2)) == 2

    assert aig.fanout_size(aig.get_node(x1)) == 2
    assert aig.fanout_size(aig.get_node(x2)) == 2
    assert aig.fanout_size(aig.get_node(f1)) == 1
    assert aig.fanout_size(aig.get_node(f2)) == 1


def test_aig_len(aig_with_single_and: tuple[Aig, AigSignal]) -> None:
    aig, _ = aig_with_single_and

    assert len(aig) == aig.size == 4


def test_aig_repr(simple_and_aig: Aig) -> None:
    aig = simple_and_aig

    assert repr(aig) == "Aig(pis=2, pos=1, gates=1, size=4)"


def test_aig_iter(aig_with_single_and: tuple[Aig, AigSignal]) -> None:
    aig, _ = aig_with_single_and

    assert list(aig) == aig.nodes() == [0, 1, 2, 3]


def test_aig_contains(aig_with_single_and: tuple[Aig, AigSignal]) -> None:
    aig, and_signal = aig_with_single_and
    and_node = aig.get_node(and_signal)

    assert 0 in aig
    assert and_node in aig
    assert -1 not in aig
    assert aig.size not in aig
    assert 1.5 not in aig


def test_aig_bool(aig_with_single_pi: tuple[Aig, AigSignal]) -> None:
    assert not Aig()

    aig, _ = aig_with_single_pi

    assert aig


@pytest.mark.parametrize("method", ["copy", "deepcopy"])
def test_aig_copy_deepcopy(simple_and_aig: Aig, method: str) -> None:
    aig = simple_and_aig
    clone = getattr(copy, method)(aig)

    assert isinstance(clone, Aig)
    assert clone is not aig
    assert equivalence_checking(aig, clone)

    aig.create_pi()
    assert aig.size == 5
    assert clone.size == 4


def test_aig_has_and(
    has_and_reference_aig: tuple[Aig, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal, AigSignal],
) -> None:
    aig, x1, x2, x3, n4, n5, n7, n8 = has_and_reference_aig

    assert aig.has_and(~x1, x2) == n4

    assert aig.has_and(~x1, x3) is None

    assert aig.has_and(~n7, ~n5) == n8


def test_aig_node_signal_iteration(
    aig_with_and_or_outputs: tuple[Aig, AigSignal, AigSignal, AigSignal, AigSignal],
) -> None:
    aig, x1, x2, f1, f2 = aig_with_and_or_outputs

    assert aig.size == 5
    assert aig.nodes() == [0, 1, 2, 3, 4]
    assert [aig.node_to_index(node) for node in aig.nodes()] == [0, 1, 2, 3, 4]
    assert aig.pis() == [1, 2]
    assert aig.gates() == [3, 4]
    assert aig.pos() == [f1, f2]
    assert [aig.get_node(signal) for signal in aig.pos()] == [3, 4]
    assert aig.fanins(aig.get_node(f1)) == [x1, x2]
    assert [aig.get_node(signal) for signal in aig.fanins(aig.get_node(f1))] == [1, 2]


def test_cleanup_dangling(cleanup_dangling_reference_aig: Aig) -> None:
    aig = cleanup_dangling_reference_aig

    assert aig.size == 8

    aig_copy = aig.clone()

    cleaned = cleanup_dangling(aig)
    assert cleaned is not None

    assert cleaned.size == 5

    assert aig.size == 8

    assert equivalence_checking(cleaned, aig_copy)

    aig = cleanup_dangling(aig)
    assert aig.size == 5


def test_pickle_empty_aig() -> None:
    aig = Aig()

    assert aig.size == 1
    assert aig.num_gates == 0

    unpickled_aig = pickle.loads(pickle.dumps(aig))

    assert unpickled_aig.size == 1
    assert unpickled_aig.num_gates == 0

    assert equivalence_checking(aig, unpickled_aig)


def test_pickle_simple_aig(simple_and_aig: Aig) -> None:
    aig = simple_and_aig

    assert aig.size == 4
    assert aig.num_gates == 1

    unpickled_aig = pickle.loads(pickle.dumps(aig))

    assert unpickled_aig.size == 4
    assert unpickled_aig.num_gates == 1

    assert equivalence_checking(aig, unpickled_aig)


def test_pickle_complex_aig(complex_mixed_logic_aig: Aig) -> None:
    aig = complex_mixed_logic_aig

    unpickled_aig = pickle.loads(pickle.dumps(aig))

    assert unpickled_aig.size == aig.size
    assert unpickled_aig.num_gates == aig.num_gates

    assert equivalence_checking(aig, unpickled_aig)


def test_pickle_multiple_aigs(simple_and_aig: Aig, simple_or_aig: Aig, simple_xor_aig: Aig) -> None:
    aig1 = simple_and_aig
    aig2 = simple_or_aig
    aig3 = simple_xor_aig

    pickled = pickle.dumps((aig1, aig2, aig3))
    unpickled_aig1, unpickled_aig2, unpickled_aig3 = pickle.loads(pickled)

    assert equivalence_checking(aig1, unpickled_aig1)
    assert equivalence_checking(aig2, unpickled_aig2)
    assert equivalence_checking(aig3, unpickled_aig3)


@pytest.mark.parametrize(
    ("state", "message"),
    [
        pytest.param(
            ([], 42),
            "Invalid state: expected a tuple of size 1 containing an index list",
            id="wrong-size",
        ),
        pytest.param(("not a list",), "Invalid state: expected an index list", id="payload"),
        pytest.param(([1, 2, "bad"],), "Invalid state: expected an index list", id="element"),
    ],
)
def test_aig_setstate_exceptions(state: tuple[Any, ...], message: str) -> None:
    class Dummy:
        pass

    # Unpickling must call __setstate__ on an uninitialized nanobind instance.
    copyreg.pickle(Dummy, lambda _: (Aig.__new__, (Aig,), state))
    with pytest.raises(ValueError, match=message):
        pickle.loads(pickle.dumps(Dummy()))


@pytest.mark.parametrize(
    "method",
    [
        "make_signal",
        "node_to_index",
        "pi_index",
        "fanins",
        "fanin_size",
        "fanout_size",
        "is_constant",
        "is_pi",
        "is_and",
        "is_or",
        "is_xor",
        "is_maj",
        "is_ite",
        "is_xor3",
        "is_nary_and",
        "is_nary_or",
    ],
)
def test_aig_node_methods_raise_on_out_of_range_node(aig_with_single_and: tuple[Aig, AigSignal], method: str) -> None:
    aig, _ = aig_with_single_and
    with pytest.raises(IndexError):
        getattr(aig, method)(aig.size)
