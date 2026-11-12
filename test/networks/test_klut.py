from __future__ import annotations

import copy
import gc
from typing import TYPE_CHECKING

import pytest

from aigverse.networks import DepthKlut, FanoutKlut, Klut, NamedKlut
from aigverse.utils import TruthTable

if TYPE_CHECKING:
    from collections.abc import Callable


def test_constants_and_arbitrary_lut() -> None:
    ntk = Klut()
    assert ntk.nodes() == [0, 1]
    assert not ntk
    assert ntk.get_constant(False) == 0
    assert ntk.get_constant(True) == 1
    assert ntk.constant_value(1)
    assert ntk.node_function(0).is_const0()
    assert ntk.node_function(1).get_bit(0)
    a, b = ntk.create_pi(), ntk.create_pi()
    table = TruthTable(2)
    table.create_from_binary_string("0010")
    gate = ntk.create_node([a, b], table)
    ntk.create_po(gate)
    assert isinstance(gate, int)
    assert ntk.fanins(gate) == [a, b]
    assert ntk.node_function(gate) == table
    assert ntk.create_node([a, b], table) == gate
    assert ntk.nodes() == list(ntk) == list(range(ntk.size))
    assert ntk.pis() == [a, b]
    assert ntk.pos() == [gate]
    assert ntk.gates() == [gate]
    assert ntk.po_index(gate) == 0
    assert ntk.fanin_size(gate) == 2
    assert ntk.fanout_size(gate) == 1
    assert ntk.is_function(gate)
    assert not ntk.is_complemented(gate)
    table.clear()
    returned = ntk.node_function(gate)
    returned.clear()
    assert ntk.node_function(gate).to_binary() == "0010"
    assert ntk.create_node([], TruthTable(0)) == 0


@pytest.mark.parametrize(
    ("operation", "arity", "expected"),
    [
        ("create_not", 1, "01"),
        ("create_and", 2, "1000"),
        ("create_nand", 2, "0111"),
        ("create_or", 2, "1110"),
        ("create_xor", 2, "0110"),
        ("create_lt", 2, "0010"),
        ("create_le", 2, "1011"),
        ("create_maj", 3, "11101000"),
        ("create_ite", 3, "11011000"),
        ("create_xor3", 3, "10010110"),
    ],
)
def test_construction_helpers(operation: str, arity: int, expected: str) -> None:
    ntk = Klut()
    inputs = [ntk.create_pi() for _ in range(arity)]
    gate = getattr(ntk, operation)(*inputs)
    assert ntk.fanins(gate) == inputs
    assert ntk.node_function(gate).to_binary() == expected


def test_nary_and_buffer(named_klut_basic: NamedKlut) -> None:
    ntk = named_klut_basic
    assert ntk.create_buf(ntk.pi_at(0)) == ntk.pi_at(0)
    assert ntk.create_nary_and(ntk.pis()) == ntk.po_at(0)
    assert ntk.create_nary_and([]) == 1
    assert ntk.create_nary_or([]) == ntk.create_nary_xor([]) == 0


@pytest.mark.parametrize("invalid", [7, 2**32, 2**63, 2**64 - 1])
@pytest.mark.parametrize(
    "method",
    [
        "get_node",
        "make_signal",
        "node_to_index",
        "index_to_node",
        "is_complemented",
        "pi_at",
        "po_at",
        "po_index",
        "create_po",
        "create_not",
        "fanins",
        "node_function",
        "fanin_size",
        "fanout_size",
        "is_constant",
        "constant_value",
        "is_pi",
        "is_function",
    ],
)
def test_full_width_handles_are_checked(method: str, invalid: int, named_klut_basic: NamedKlut) -> None:
    with pytest.raises(IndexError):
        getattr(named_klut_basic, method)(invalid)


def test_invalid_construction(named_klut_basic: NamedKlut) -> None:
    ntk = named_klut_basic
    with pytest.raises(ValueError, match="variable count"):
        ntk.create_node(ntk.pis(), TruthTable(1))
    with pytest.raises(ValueError, match="32"):
        ntk.create_node([0] * 33, TruthTable(0))
    with pytest.raises(IndexError):
        ntk.create_node([2**32], TruthTable(1))
    with pytest.raises(IndexError):
        ntk.create_and(ntk.pi_at(0), 2**32)
    with pytest.raises(IndexError):
        ntk.create_nary_xor([0, 2**32])
    with pytest.raises(TypeError):
        ntk.create_not(~ntk.pi_at(0))
    with pytest.raises(ValueError, match="constant"):
        ntk.constant_value(ntk.pi_at(0))
    with pytest.raises(ValueError, match="primary output"):
        ntk.po_index(ntk.pi_at(0))
    assert -1 not in ntk
    assert 2**100 not in ntk
    assert "0" not in ntk
    assert ntk.pi_at(0) in ntk


@pytest.mark.parametrize("view_type", [Klut, NamedKlut, DepthKlut, FanoutKlut])
@pytest.mark.parametrize("copier", [lambda ntk: ntk.clone(), copy.copy, copy.deepcopy])
def test_copies_are_independent(
    view_type: type[Klut], copier: Callable[[Klut], Klut], named_klut_basic: NamedKlut
) -> None:
    original = view_type(named_klut_basic)
    cloned = copier(original)
    assert type(cloned) is view_type
    gate = original.po_at(0)
    cloned.create_po(cloned.create_not(gate))
    assert original.num_gates == 1
    assert original.num_pos == 1
    assert cloned.num_gates == 2
    assert cloned.num_pos == 2
    del original
    gc.collect()
    if isinstance(cloned, NamedKlut):
        assert cloned.get_network_name() == "top"
        assert cloned.get_name(cloned.pi_at(0)) == "a"
        assert cloned.get_output_name(0) == "out"
    if isinstance(cloned, DepthKlut):
        cloned.update_levels()
        assert cloned.level(gate) == 1
        assert cloned.num_levels == 2
    if isinstance(cloned, FanoutKlut):
        assert cloned.fanouts(gate) == [cloned.po_at(1)]


@pytest.mark.parametrize("view_type", [NamedKlut, DepthKlut, FanoutKlut])
def test_view_constructor_shares_storage(view_type: type[Klut], named_klut_basic: NamedKlut) -> None:
    view = view_type(named_klut_basic)
    new_input = named_klut_basic.create_pi()
    assert view.pi_at(2) == new_input
    assert Klut(view).size == view.size


def test_depth_and_fanout_primary_inputs() -> None:
    depth = DepthKlut()
    a = depth.create_pi()
    assert depth.level(a) == 0
    depth.create_po(a)
    assert depth.is_on_critical_path(a)
    b = depth.create_pi()
    gate = depth.create_and(a, b)
    depth.create_po(depth.create_not(gate))
    assert depth.num_levels == 2
    assert depth.level(gate) == 1
    assert depth.is_on_critical_path(gate)
    fanout = FanoutKlut()
    a = fanout.create_pi()
    assert fanout.fanouts(a) == []
    fanout.create_po(a)
    assert fanout.fanouts(a) == []
    gate = fanout.create_not(a)
    assert fanout.fanouts(a) == [gate]
    repeated = fanout.create_and(a, a)
    assert fanout.fanouts(a) == [gate, repeated]
    assert fanout.clone().fanouts(a) == [gate, repeated]


def test_view_handle_validation(named_klut_basic: NamedKlut) -> None:
    ntk = named_klut_basic
    for operation in (ntk.get_name, ntk.has_name, ntk.get_output_name, ntk.has_output_name):
        with pytest.raises(IndexError):
            operation(2**32)
    with pytest.raises(IndexError):
        ntk.set_name(2**32, "invalid")
    with pytest.raises(IndexError):
        ntk.set_output_name(2**32, "invalid")
    with pytest.raises(IndexError):
        DepthKlut(ntk).level(2**32)
    with pytest.raises(IndexError):
        FanoutKlut(ntk).fanouts(2**32)


def test_named_view_copies_names_but_shares_structure(named_klut_basic: NamedKlut) -> None:
    view = NamedKlut(named_klut_basic)
    named_klut_basic.set_name(named_klut_basic.pi_at(0), "renamed")
    assert view.get_name(view.pi_at(0)) == "a"
    extra = named_klut_basic.create_pi("extra")
    assert view.pi_at(2) == extra
    assert not view.has_name(extra)
    with pytest.raises(IndexError):
        view.get_name(extra)


def test_depth_output_after_refreshing_dangling_logic() -> None:
    ntk = DepthKlut()
    a = ntk.create_pi()
    gate = ntk.create_not(ntk.create_not(a))
    ntk.update_levels()
    assert ntk.num_levels == 0
    gate = ntk.create_not(gate)
    ntk.create_po(gate)
    assert ntk.num_levels == ntk.level(gate) == 3


def test_depth_view_constructor_rebuilds_its_own_metadata() -> None:
    original = DepthKlut()
    a = original.create_pi()
    original.create_po(original.create_not(a))
    dangling = original.create_not(original.po_at(0))
    assert original.level(dangling) == 2
    view = DepthKlut(original)
    assert view.level(dangling) == 0
    view.create_po(dangling)
    assert view.num_levels == 2
    assert original.num_levels == 1
    original.update_levels()
    assert original.num_levels == 2


def test_fanout_view_callbacks_have_independent_lifetimes() -> None:
    original = FanoutKlut()
    a = original.create_pi()
    view = FanoutKlut(original)
    first = original.create_and(a, a)
    second = view.create_not(a)
    view.update_fanout()
    assert view.fanouts(a) == original.fanouts(a) == [first, second]
    del view
    gc.collect()
    third = original.create_or(a, second)
    assert original.fanouts(a) == [first, second, third]
