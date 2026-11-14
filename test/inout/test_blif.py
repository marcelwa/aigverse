from __future__ import annotations

import locale
import sys
from typing import TYPE_CHECKING

import pytest

from aigverse.io import read_blif, write_blif
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
    restored = read_blif(path)
    assert isinstance(restored, NamedKlut)
    assert restored.num_pis == original.num_pis
    assert restored.num_pos == original.num_pos
    assert output_values(restored) == output_values(original)
    if named:
        assert [restored.get_name(node) for node in restored.pis()] == ["a", "b", "late"]
        assert [restored.get_output_name(i) for i in range(restored.num_pos)] == [
            ntk.get_output_name(i) for i in range(ntk.num_pos)
        ]


def test_blif_round_trip_omits_dangling_logic(named_klut_basic: NamedKlut, tmp_path: Path) -> None:
    ntk = named_klut_basic
    dangling = ntk.pi_at(0)
    for _ in range(3):
        dangling = ntk.create_not(dangling)
    path = tmp_path / "dangling.blif"
    write_blif(ntk, path)
    restored = read_blif(path)
    assert restored.num_gates < ntk.num_gates
    assert output_values(restored) == output_values(ntk)
    assert [restored.get_name(node) for node in restored.pis()] == ["a", "b"]
    assert [restored.get_output_name(i) for i in range(restored.num_pos)] == ["out"]


@pytest.mark.parametrize("model", ["test", "topà", "topÍ", "top\u0085", "top\u00a0"])
def test_blif_covers_comments_and_forward_references(model: str, tmp_path: Path) -> None:
    path = tmp_path / "covers.blif"
    path.write_text(
        f".model {model}\n.inputs names \\\n end\n.outputs out empty one direct\n"
        ".names internal out\n0 1 # invert\n.names names end internal\n00 0\n"
        ".names names end empty\n.names one\n1\n.names names direct\n1 1\n.end\n",
        encoding="utf-8",
    )
    ntk = read_blif(path)
    assert ntk.get_network_name() == model
    assert [ntk.get_name(node) for node in ntk.pis()] == ["names", "end"]
    assert output_values(ntk) == [
        [True, False, True, False],
        [False, False, True, True],
        [False, False, True, False],
        [False, False, True, True],
    ]
    assert all(not ntk.has_name(node) for node in ntk.gates())


@pytest.mark.parametrize("separator", ["", "   ", "# comment"])
def test_continuation_ends_at_next_physical_line(separator: str, tmp_path: Path) -> None:
    path = tmp_path / "continued.blif"
    path.write_text(f".model top\n.inputs a \\\n{separator}\n.outputs a\n.end", encoding="utf-8")
    ntk = read_blif(path)
    assert ntk.num_pis == ntk.num_pos == 1
    assert ntk.get_name(ntk.pi_at(0)) == ntk.get_output_name(0) == "a"
    assert output_values(ntk) == [[False], [True]]


@pytest.mark.parametrize("name", [".a", ".model", ".inputs", ".outputs", ".names", ".end", "éclair", "à", "Í"])
def test_driver_names_round_trip(name: str, tmp_path: Path) -> None:
    ntk = NamedKlut()
    a = ntk.create_pi(name)
    ntk.create_po(a, name)
    ntk.create_po(a, name)
    ntk.create_po(0, "new_n0")
    ntk.create_po(1, "new_n1")
    path = tmp_path / "passthrough.blif"
    write_blif(ntk, path)
    restored = read_blif(path)
    assert [restored.get_output_name(i) for i in range(4)] == [name, name, "new_n0", "new_n1"]
    assert output_values(restored) == output_values(ntk)


@pytest.mark.parametrize(
    ("input_names", "output_names"),
    [
        (["", "pi2"], ["left", "right"]),
        (["", "po0"], ["", "right"]),
        (["", "b"], ["out", "pi2"]),
        (["a", "b"], ["", "po0"]),
    ],
)
def test_generated_interface_names_avoid_explicit_names(
    input_names: list[str], output_names: list[str], tmp_path: Path
) -> None:
    ntk = NamedKlut()
    for name in input_names:
        ntk.create_pi(name)
    for node, name in zip(ntk.pis(), output_names, strict=True):
        ntk.create_po(node, name)
    path = tmp_path / "default_names.blif"
    write_blif(ntk, path)
    restored = read_blif(path)
    actual_inputs = [restored.get_name(node) for node in restored.pis()]
    actual_outputs = [restored.get_output_name(i) for i in range(restored.num_pos)]
    assert len(set(actual_inputs)) == len(input_names)
    assert len(set(actual_outputs)) == len(output_names)
    for expected, actual in zip(input_names + output_names, actual_inputs + actual_outputs, strict=True):
        if expected:
            assert actual == expected
    assert output_values(restored) == output_values(ntk)


@pytest.mark.parametrize(
    "body",
    [
        ".latch a out",
        ".subckt child a=a out=out",
        ".gate AND a=a Y=out",
        ".blackbox",
        ".names a out\n1 1\n.exdc",
        ".names a out\n1 1\n.mlatch a out",
        ".names a out\n1 1\n.clock c",
        ".names a out\n1 1\n.default_input_arrival 0 0",
        ".names a out\n1 1\n.search child.blif",
        ".names missing out\n1 1",
        ".names missing out",
        ".names out internal\n1 1\n.names internal out\n1 1",
        ".names out internal\n.names internal out",
        ".names a out\n11 1",
        ".names a out\nx 1",
        ".names a out\né 1",
        ".names a out\n1 é",
        ".names a out\n1 1é",
        ".names a out\n1 -",
        ".names a out\n0 0\n1 1",
        ".names a out\n1 1 garbage",
        ".names a out\n1 1\n.inputs\n0 1",
        ".names a out\n1 1\n.outputs\n0 1",
        ".names out\n0\n1",
        ".names out\n0 1",
        "1",
        ".names a out\n1 1\n.names a out\n0 1",
        ".inputs a\n.names a out\n1 1",
        ".names a\n1\n.names a out\n1 1",
        ".names",
        ".names " + " ".join(["a"] * 33) + " out\n" + "1" * 33 + " 1",
        ".names " + " ".join(["a"] * 33) + " out",
        ".names orphan\n1",
        ".names a out\n1 1\n.model second\n.inputs b\n.outputs b",
        ".names a out\n1 1\n.end\n.model second\n.inputs b\n.outputs b",
        ".names a out\n1 1\n.end\n.names unused\n1",
        ".end extra",
    ],
)
def test_invalid_blif_is_rejected(body: str, tmp_path: Path) -> None:
    path = tmp_path / "invalid.blif"
    path.write_text(f".model top\n.inputs a\n.outputs out\n{body}\n.end\n", encoding="utf-8")
    with pytest.raises(RuntimeError):
        read_blif(path)


@pytest.mark.parametrize("text", ["", ".inputs a\n.end\n", ".model top\n", ".model top\n.inputs a \\\n"])
def test_incomplete_blif_is_rejected(text: str, tmp_path: Path) -> None:
    path = tmp_path / "incomplete.blif"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(RuntimeError):
        read_blif(path)


def test_blank_continuation_does_not_consume_bare_record(tmp_path: Path) -> None:
    path = tmp_path / "continued.blif"
    path.write_text(".model top\n.inputs a \\\n\nb\n.outputs a\n.end\n", encoding="utf-8")
    with pytest.raises(RuntimeError):
        read_blif(path)


@pytest.mark.parametrize("separator", [" ", "\t", "\f", "\v", "\r"])
def test_cover_whitespace(separator: str, tmp_path: Path) -> None:
    path = tmp_path / "whitespace.blif"
    path.write_text(f".model top\n.inputs a\n.outputs out\n.names a out\n1{separator}1\n.end\n", encoding="utf-8")
    assert output_values(read_blif(path)) == [[False], [True]]


def test_empty_cover_at_fanin_limit(tmp_path: Path) -> None:
    inputs = [f"i{i}" for i in range(32)]
    names = " ".join(inputs)
    path = tmp_path / "wide_empty.blif"
    path.write_text(f".model top\n.inputs {names}\n.outputs out\n.names {names} out\n.end\n", encoding="utf-8")
    ntk = read_blif(path)
    assert [ntk.get_name(node) for node in ntk.pis()] == inputs
    assert ntk.num_pos == 1
    assert ntk.po_at(0) == ntk.get_constant(False)
    assert ntk.get_output_name(0) == "out"


def test_internal_names_do_not_collide(named_klut_basic: NamedKlut, tmp_path: Path) -> None:
    ntk = named_klut_basic
    ntk.set_name(ntk.pi_at(0), "new_n4")
    ntk.set_name(ntk.po_at(0), "new_n0")
    ntk.create_po(ntk.po_at(0), "out")
    path = tmp_path / "names.blif"
    write_blif(ntk, path)
    restored = read_blif(path)
    assert restored.get_name(restored.pi_at(0)) == "new_n4"
    assert restored.get_output_name(1) == "out"
    assert output_values(restored) == output_values(ntk)


@pytest.mark.parametrize(
    "name", ["new_n0", "new_n1", "a", "", "a b", "a#b", "a\\b", "a\n.inputs bad", "a\x01b", "a\x7fb"]
)
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
    assert not read_blif(path)
    pi = ntk.create_pi()
    ntk.create_po(pi)
    write_blif(ntk, path)
    assert output_values(read_blif(path)) == [[False], [True]]


def test_blif_path_errors(named_klut_basic: NamedKlut, tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="opening"):
        read_blif(tmp_path / "missing.blif")
    with pytest.raises(RuntimeError):
        read_blif(tmp_path)
    with pytest.raises(RuntimeError, match="opening"):
        write_blif(named_klut_basic, tmp_path / "missing" / "out.blif")


@pytest.mark.parametrize("cover", ["", "0", "1"])
def test_constant_covers_without_inputs(cover: str, tmp_path: Path) -> None:
    path = tmp_path / "constant.blif"
    path.write_text(f".model constant\n.inputs\n.outputs out\n.names out\n{cover}\n.end\n", encoding="utf-8")
    ntk = read_blif(path)
    assert output_values(ntk) == [[cover == "1"]]
    assert ntk.get_output_name(0) == "out"


def test_empty_blif_directives_and_blank_logical_lines(tmp_path: Path) -> None:
    path = tmp_path / "empty.blif"
    path.write_text(".model empty\n\n# comment\n.inputs\n.outputs\n\\\n\n.end", encoding="utf-8")
    assert not read_blif(path)


@pytest.mark.parametrize("header", [".model", ".model first second"])
def test_invalid_model_header(header: str, tmp_path: Path) -> None:
    path = tmp_path / "model.blif"
    path.write_text(f"{header}\n.end\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match=r"one \.model name"):
        read_blif(path)


@pytest.mark.skipif(sys.platform != "linux", reason="Requires Linux /dev/full")
def test_blif_reports_write_failure(named_klut_basic: NamedKlut) -> None:
    with pytest.raises(RuntimeError, match="writing BLIF"):
        write_blif(named_klut_basic, "/dev/full")


@pytest.mark.parametrize("ctype_locale", ["French_France.1252", "fr_FR.ISO8859-1"])
@pytest.mark.parametrize("model", ["topà", "topÍ"])
def test_utf8_names_ignore_ctype_locale(ctype_locale: str, model: str, tmp_path: Path) -> None:
    previous = locale.setlocale(locale.LC_CTYPE)
    try:
        try:
            locale.setlocale(locale.LC_CTYPE, ctype_locale)
        except locale.Error:
            pytest.skip(f"Locale {ctype_locale} is unavailable")
        path = tmp_path / "locale.blif"
        path.write_text(f".model {model}\n.inputs à Í\n.outputs à Í\n.end\n", encoding="utf-8")
        ntk = read_blif(path)
        assert ntk.get_network_name() == model
        assert [ntk.get_name(node) for node in ntk.pis()] == ["à", "Í"]
        write_blif(ntk, path)
        restored = read_blif(path)
        assert [restored.get_name(node) for node in restored.pis()] == ["à", "Í"]
        assert [restored.get_output_name(i) for i in range(restored.num_pos)] == ["à", "Í"]
        assert output_values(restored) == output_values(ntk)
    finally:
        locale.setlocale(locale.LC_CTYPE, previous)
