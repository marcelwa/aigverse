from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aigverse.io import read_blif_into_klut, write_blif
from aigverse.networks import DepthKlut, Klut, NamedKlut
from aigverse.utils import TruthTable

if TYPE_CHECKING:
    from pathlib import Path


def output_values(ntk: Klut) -> list[list[bool]]:
    """Evaluate every input assignment for a small test network.

    Args:
        ntk: Network with topologically ordered gates.

    Returns:
        Output values for each assignment in binary order.
    """
    outputs = []
    for assignment in range(1 << ntk.num_pis):
        values = {0: False, 1: True}
        values.update({node: bool(assignment & (1 << i)) for i, node in enumerate(ntk.pis())})
        for node in ntk.gates():
            index = sum(int(values[fanin]) << i for i, fanin in enumerate(ntk.fanins(node)))
            values[node] = ntk.node_function(node).get_bit(index)
        outputs.append([values[node] for node in ntk.pos()])
    return outputs


@pytest.mark.parametrize("named", [True, False])
def test_blif_round_trip(named_klut_basic: NamedKlut, tmp_path: Path, *, named: bool) -> None:
    ntk = named_klut_basic
    a = ntk.pi_at(0)
    # A PI created after a gate exercises native topological-index naming.
    late_input = ntk.create_pi("late")
    asymmetric = TruthTable(2)
    asymmetric.create_from_binary_string("0010")
    ntk.create_po(ntk.create_node([a, late_input], asymmetric), "asymmetric")
    ntk.create_po(ntk.create_not(a), "inverted")
    ntk.create_po(0, "zero")
    ntk.create_po(1, "one")
    ntk.create_po(a, "direct")
    ntk.create_po(ntk.po_at(0), "duplicate")
    original = ntk if named else Klut(ntk)
    path = tmp_path / "roundtrip.blif"
    write_blif(original, path)
    restored = read_blif_into_klut(path)
    assert isinstance(restored, NamedKlut)
    assert restored.num_pis == original.num_pis
    assert restored.num_pos == original.num_pos
    assert output_values(restored) == output_values(original)
    if named:
        assert [restored.get_name(node) for node in restored.pis()] == ["a", "b", "late"]
        assert [restored.get_output_name(i) for i in range(restored.num_pos)] == [
            ntk.get_output_name(i) for i in range(ntk.num_pos)
        ]


def test_blif_covers_comments_and_forward_references(tmp_path: Path) -> None:
    path = tmp_path / "covers.blif"
    path.write_text(
        ".model test\n.inputs names \\\n end\n.outputs out empty one direct\n"
        ".names internal out\n0 1 # invert\n.names names end internal\n00 0\n"
        ".names names end empty\n.names one\n1\n.names names direct\n1 1\n.end\n",
        encoding="utf-8",
    )
    ntk = read_blif_into_klut(path)
    assert ntk.get_network_name() == "test"
    assert [ntk.get_name(node) for node in ntk.pis()] == ["names", "end"]
    assert output_values(ntk) == [
        [True, False, True, False],
        [False, False, True, True],
        [False, False, True, False],
        [False, False, True, True],
    ]


@pytest.mark.parametrize(
    "body",
    [
        ".latch a out",
        ".subckt child a=a out=out",
        ".gate AND a=a Y=out",
        ".blackbox",
        ".names missing out\n1 1",
        ".names out internal\n1 1\n.names internal out\n1 1",
        ".names a out\n11 1",
        ".names a out\nx 1",
        ".names a out\n1 -",
        ".names a out\n0 0\n1 1",
        ".names a out\n1 1 garbage",
        ".names out\n0\n1",
        ".names a out\n1 1\n.names a out\n0 1",
        ".inputs a",
        ".names a\n1",
        ".names",
        ".names " + " ".join(["a"] * 33) + " out\n" + "1" * 33 + " 1",
        ".names orphan\n1",
        ".model second",
        ".end\n.model second",
    ],
)
def test_invalid_blif_is_rejected(body: str, tmp_path: Path) -> None:
    path = tmp_path / "invalid.blif"
    path.write_text(f".model top\n.inputs a\n.outputs out\n{body}\n.end\n", encoding="utf-8")
    with pytest.raises(RuntimeError):
        read_blif_into_klut(path)


@pytest.mark.parametrize("text", ["", ".inputs a\n.end\n", ".model top\n", ".model top\n.inputs a \\\n"])
def test_incomplete_blif_is_rejected(text: str, tmp_path: Path) -> None:
    path = tmp_path / "incomplete.blif"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(RuntimeError):
        read_blif_into_klut(path)


def test_internal_names_do_not_collide(named_klut_basic: NamedKlut, tmp_path: Path) -> None:
    ntk = named_klut_basic
    ntk.set_name(ntk.pi_at(0), "new_n4")
    ntk.set_name(ntk.po_at(0), "new_n0")
    ntk.create_po(ntk.po_at(0), "out")
    path = tmp_path / "names.blif"
    write_blif(ntk, path)
    restored = read_blif_into_klut(path)
    assert restored.get_name(restored.pi_at(0)) == "new_n4"
    assert restored.get_output_name(1) == "out"
    assert output_values(restored) == output_values(ntk)


@pytest.mark.parametrize("name", ["new_n0", "new_n1", "a", "", "a b", "a#b", "a\\b", "a\n.inputs bad"])
def test_invalid_output_names_rejected(name: str, named_klut_basic: NamedKlut, tmp_path: Path) -> None:
    named_klut_basic.set_output_name(0, name)
    path = tmp_path / "output.blif"
    with pytest.raises(ValueError, match="BLIF interface name"):
        write_blif(named_klut_basic, path)
    assert not path.exists()


def test_conflicting_outputs_and_duplicate_inputs(named_klut_basic: NamedKlut, tmp_path: Path) -> None:
    ntk = named_klut_basic
    ntk.create_po(ntk.pi_at(0), "out")
    with pytest.raises(ValueError, match="conflicting"):
        write_blif(ntk, tmp_path / "outputs.blif")
    ntk.set_output_name(1, "direct")
    ntk.set_name(ntk.pi_at(1), "a")
    with pytest.raises(ValueError, match="conflicting"):
        write_blif(ntk, tmp_path / "inputs.blif")


def test_empty_and_direct_networks(tmp_path: Path) -> None:
    ntk = DepthKlut()
    path = tmp_path / "empty.blif"
    write_blif(ntk, path)
    assert not read_blif_into_klut(path)
    pi = ntk.create_pi()
    ntk.create_po(pi)
    write_blif(ntk, path)
    assert output_values(read_blif_into_klut(path)) == [[False], [True]]


def test_blif_path_errors(named_klut_basic: NamedKlut, tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="opening"):
        read_blif_into_klut(tmp_path / "missing.blif")
    with pytest.raises(RuntimeError, match="opening"):
        write_blif(named_klut_basic, tmp_path / "missing" / "out.blif")
