"""LUT mapping and representation transfer through the external ABC bridge."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from aigverse import abc, algorithms
from aigverse.networks import Aig, Klut, NamedAig, NamedKlut, SequentialAig


@pytest.mark.usefixtures("abc_available")
@pytest.mark.parametrize("namespace", [abc, abc.gia], ids=["classic", "gia"])
@pytest.mark.parametrize("named", [False, True])
def test_mapping_round_trip(namespace, named_klut_basic, *, named):
    source = named_klut_basic
    a = source.pi_at(0)
    source.create_pi("unused")
    source.create_xor(a, source.pi_at(2))
    for signal, name in (
        (source.po_at(0), "duplicate"),
        (source.create_not(source.po_at(0)), "negated"),
        (a, "direct"),
        (source.get_constant(False), "zero"),
        (source.get_constant(True), "one"),
    ):
        source.create_po(signal, name)
    if not named:
        source = Klut(source)
    before = algorithms.simulate(source)
    original_size = source.size
    aig = algorithms.convert_klut_to_aig(source)
    mapped = namespace.if_(aig, cut_size=2)
    remapped = namespace.if_(source, cut_size=2)
    scripted = namespace.run_script(source, namespace.if_.cmd(cut_size=2), output_type="klut")
    for result in (mapped, remapped, scripted):
        assert type(result) is (NamedKlut if named else Klut)
        assert algorithms.equivalence_checking(aig, result)
        assert algorithms.simulate(result) == before
        assert all(result.fanin_size(node) <= 2 for node in result.gates())
        if named:
            assert [result.get_name(result.pi_at(i)) for i in range(3)] == ["a", "b", "unused"]
            assert [result.get_output_name(i) for i in range(6)] == [
                "out",
                "duplicate",
                "negated",
                "direct",
                "zero",
                "one",
            ]
    assert source.size == original_size
    assert algorithms.simulate(source) == before


@pytest.mark.usefixtures("abc_available")
@pytest.mark.parametrize("mapper", [abc.if_, abc.gia.if_], ids=["classic", "gia"])
def test_mapping_named_return_types(mapper: abc.If | abc.gia.If, named_klut_basic: NamedKlut) -> None:
    mapped: NamedKlut = mapper(algorithms.convert_klut_to_aig(named_klut_basic))
    remapped: NamedKlut = mapper(named_klut_basic)
    assert mapped.get_output_name(0) == remapped.get_output_name(0) == "out"


@pytest.mark.usefixtures("abc_available")
@pytest.mark.parametrize("namespace", [abc, abc.gia], ids=["classic", "gia"])
def test_lut_batch_keeps_input_order_and_namedness(namespace, and_aig, named_klut_basic):
    results = namespace.run_many([and_aig, named_klut_basic], namespace.if_.cmd(), output_type="klut", jobs=2)
    assert [type(result) for result in results] == [Klut, NamedKlut]
    assert all(algorithms.equivalence_checking(and_aig, result) for result in results)


@pytest.mark.usefixtures("abc_available")
@pytest.mark.parametrize(("namespace", "command"), [(abc, "strash"), (abc.gia, "&st")])
@pytest.mark.parametrize("named", [False, True])
def test_lut_input_can_explicitly_unmap_to_aig(namespace, command, named_klut_basic, *, named):
    source = named_klut_basic if named else Klut(named_klut_basic)
    result = namespace.run_script(source, command)
    assert type(result) is (NamedAig if named else Aig)
    assert algorithms.equivalence_checking(source, result)
    if named:
        assert result.get_name(result.make_signal(result.pi_at(0))) == "a"
        assert result.get_output_name(0) == "out"


@pytest.mark.usefixtures("abc_available")
@pytest.mark.parametrize(("namespace", "command"), [(abc.gia, "&ps"), (abc.gia, "&b"), (abc, "print_stats")])
@pytest.mark.parametrize("named", [False, True])
def test_default_aig_output_follows_native_store_behavior(namespace, command, named_klut_basic, *, named):
    source = named_klut_basic if named else Klut(named_klut_basic)
    if namespace is abc:
        with pytest.raises(abc.AbcExecutionError, match="structurally hashed"):
            namespace.run_script(source, command)
        return
    result = namespace.run_script(source, command)
    assert type(result) is (NamedAig if named else Aig)
    assert algorithms.equivalence_checking(source, result)
    if named:
        assert [result.get_name(result.make_signal(result.pi_at(i))) for i in range(2)] == ["a", "b"]
        assert result.get_output_name(0) == "out"


@pytest.mark.parametrize(
    ("namespace", "lut_input", "read_command"),
    [
        (abc, False, "read_aiger in.aig"),
        (abc.gia, False, "&read in.aig"),
        (abc, True, "read_blif in.blif"),
        (abc.gia, True, "read_blif in.blif; &get -m -n"),
    ],
)
@pytest.mark.parametrize(
    ("output_type", "classic_write", "gia_write"),
    [("aig", "write_aiger -s out.aig", "&write out.aig"), ("klut", "write_blif out.blif", "&put; write_blif out.blif")],
)
def test_transfer_commands_without_abc(
    namespace, read_command, output_type, classic_write, gia_write, and_aig, named_klut_basic, monkeypatch, *, lut_input
):
    from aigverse.io import read_aiger_into_aig, read_blif_into_klut, write_aiger, write_blif

    source = named_klut_basic if lut_input else and_aig
    write_command = classic_write if namespace is abc else gia_write
    monkeypatch.delenv("AIGVERSE_ABC_RC", raising=False)

    def transfer(argv, *, cwd, **_kwargs):
        assert argv[-1] == f"{read_command}; version; {write_command}"
        transferred = (
            read_blif_into_klut(Path(cwd, "in.blif")) if lut_input else read_aiger_into_aig(Path(cwd, "in.aig"))
        )
        assert algorithms.equivalence_checking(source, transferred)
        if output_type == "klut":
            write_blif(named_klut_basic, Path(cwd, "out.blif"))
        else:
            write_aiger(algorithms.convert_klut_to_aig(named_klut_basic), Path(cwd, "out.aig"))
        return subprocess.CompletedProcess(argv, 0, "")

    monkeypatch.setattr(subprocess, "run", transfer)
    result = namespace.run_script(source, "version", output_type=output_type, binary=sys.executable)
    assert isinstance(result, Klut if output_type == "klut" else Aig)
    assert algorithms.equivalence_checking(source, result)


@pytest.mark.parametrize("namespace", [abc, abc.gia], ids=["classic", "gia"])
@pytest.mark.parametrize("output_type", ["lut", "", None, 1, []])
def test_output_selector_is_checked_before_discovery(namespace, output_type, and_aig, tmp_path):
    with pytest.raises(ValueError, match="output_type"):
        namespace.run_script(and_aig, "balance", output_type=output_type, binary=tmp_path / "missing")
    with pytest.raises(ValueError, match="output_type"):
        namespace.run_many([], "balance", output_type=output_type, binary=tmp_path / "missing")


@pytest.mark.parametrize("namespace", [abc, abc.gia], ids=["classic", "gia"])
def test_mapping_rejects_sequential_before_discovery(namespace, and_aig, tmp_path):
    sequential = SequentialAig()
    with pytest.raises(ValueError, match="combinational"):
        namespace.if_(sequential, binary=tmp_path / "missing")
    with pytest.raises(ValueError, match="combinational"):
        namespace.run_many([and_aig, sequential], "if", output_type="klut", binary=tmp_path / "missing")


@pytest.mark.parametrize("namespace", [abc, abc.gia], ids=["classic", "gia"])
def test_lut_output_reports_invalid_blif(namespace, and_aig, monkeypatch):
    def corrupt(_argv, *, cwd, **_kwargs):
        Path(cwd, "out.blif").write_text("not a BLIF model", encoding="utf-8")
        return subprocess.CompletedProcess(_argv, 0, "")

    monkeypatch.setattr(subprocess, "run", corrupt)
    with pytest.raises(abc.AbcExecutionError, match="could not read"):
        namespace.run_script(and_aig, "if", output_type="klut", binary=sys.executable)


@pytest.mark.parametrize("message", ["FPGA mapping has failed.", 'Current AIG has mapping. Run "&st".'])
def test_failed_mapping_cannot_return_a_stale_network(message, named_klut_basic, monkeypatch):
    from aigverse.io import write_blif

    def stale(_argv, *, cwd, **_kwargs):
        write_blif(named_klut_basic, Path(cwd, "out.blif"))
        return subprocess.CompletedProcess(_argv, 0, message)

    monkeypatch.setattr(subprocess, "run", stale)
    with pytest.raises(abc.AbcExecutionError, match="ABC reported an error"):
        abc.run_script(named_klut_basic, "if", output_type="klut", binary=sys.executable)


@pytest.mark.parametrize(("namespace", "prefix"), [(abc, "if"), (abc.gia, "&st; &if")])
def test_mapping_options_and_command_composition(namespace, prefix):
    assert str(namespace.if_.cmd()) == f"{prefix} -K 6 -C 8"
    assert (
        str(
            namespace.if_.cmd(
                cut_size=4,
                cut_limit=12,
                area_oriented_mapping=True,
                area_flow_rounds=0,
                ela_rounds=3,
                delay_relaxation=20,
            )
        )
        == f"{prefix} -K 4 -C 12 -F 0 -A 3 -R 20 -a"
    )
    assert repr(namespace.if_) == f"{namespace.__name__}.if_"


@pytest.mark.parametrize("namespace", [abc, abc.gia], ids=["classic", "gia"])
@pytest.mark.parametrize(
    ("option", "value"),
    [
        ("cut_size", 1),
        ("cut_size", 33),
        ("cut_limit", 0),
        ("cut_limit", 4096),
        ("area_flow_rounds", -1),
        ("ela_rounds", -1),
        ("delay_relaxation", -1),
        ("delay_relaxation", float("nan")),
        ("delay_relaxation", float("inf")),
        ("cut_size", 2.5),
        ("cut_limit", float("nan")),
        ("area_flow_rounds", 0.5),
        ("ela_rounds", float("inf")),
        ("ela_rounds", 2**31),
    ],
)
def test_mapping_invalid_options_precede_discovery(namespace, option, value, and_aig, tmp_path):
    with pytest.raises(ValueError, match=option):
        namespace.if_(and_aig, **{option: value}, binary=tmp_path / "missing")


@pytest.mark.parametrize(
    "call",
    [abc.balance, abc.resyn2, abc.gia.dc2, abc.stats, abc.gia.stats],
    ids=["balance", "resyn2", "gia-dc2", "stats", "gia-stats"],
)
def test_existing_aig_wrappers_keep_their_input_contract(call, named_klut_basic, tmp_path):
    with pytest.raises(TypeError, match="expected an Aig"):
        call(named_klut_basic, binary=tmp_path / "missing")


@pytest.mark.usefixtures("abc_available")
@pytest.mark.parametrize("namespace", [abc, abc.gia], ids=["classic", "gia"])
@pytest.mark.parametrize("network", [Aig, Klut])
@pytest.mark.parametrize("shape", ["constants", "direct", "no_outputs", "empty"])
def test_mapping_zero_gate_networks(namespace, network, shape):
    source = network()
    if shape == "constants":
        source.create_po(source.get_constant(False))
        source.create_po(source.get_constant(True))
    elif shape in {"direct", "no_outputs"}:
        a = source.create_pi()
        if shape == "direct":
            source.create_po(a)
            source.create_po(source.create_not(a))
    if shape == "empty":
        with pytest.raises(abc.AbcExecutionError):
            namespace.if_(source, timeout=10)
        return
    result = namespace.if_(source)
    assert result.num_pis == source.num_pis
    assert algorithms.simulate(result) == algorithms.simulate(source)


@pytest.mark.usefixtures("abc_available")
@pytest.mark.parametrize("namespace", [abc, abc.gia], ids=["classic", "gia"])
@pytest.mark.parametrize("network", [NamedAig, NamedKlut])
def test_direct_output_can_share_its_input_name(namespace, network):
    source = network()
    source.create_po(source.create_pi("shared"), "shared")
    result = namespace.if_(source)
    assert result.get_name(result.pi_at(0)) == "shared"
    assert result.get_output_name(0) == "shared"
    assert algorithms.simulate(result) == algorithms.simulate(source)


@pytest.mark.usefixtures("abc_available")
@pytest.mark.parametrize("namespace", [abc, abc.gia], ids=["classic", "gia"])
@pytest.mark.parametrize(("cut_size", "cut_limit"), [(2, 1), (32, 4095)])
def test_mapping_numeric_boundaries_match_native_abc(namespace, and_aig, cut_size, cut_limit):
    result = namespace.if_(and_aig, cut_size=cut_size, cut_limit=cut_limit)
    assert algorithms.equivalence_checking(and_aig, result)


@pytest.mark.usefixtures("abc_available")
@pytest.mark.parametrize(("namespace", "prefix"), [(abc, "if"), (abc.gia, "&if")])
@pytest.mark.parametrize("options", ["-K 1", "-K 33", "-C 0", "-C 4096"])
def test_invalid_native_mapping_limits_report_an_abc_error(namespace, and_aig, prefix, options):
    with pytest.raises(abc.AbcExecutionError, match="Incorrect"):
        namespace.run_script(and_aig, f"{prefix} {options}", output_type="klut")


@pytest.mark.usefixtures("abc_available")
@pytest.mark.parametrize("namespace", [abc, abc.gia], ids=["classic", "gia"])
@pytest.mark.parametrize("network", [NamedAig, NamedKlut])
def test_duplicate_output_labels_report_native_abc_failure(namespace, network):
    source = network()
    gate = source.create_and(source.create_pi("a"), source.create_pi("b"))
    source.create_po(gate, "duplicate")
    source.create_po(gate, "duplicate")
    with pytest.raises(abc.AbcExecutionError):
        namespace.if_(source, timeout=10)


@pytest.mark.usefixtures("abc_available")
@pytest.mark.parametrize("namespace", [abc, abc.gia], ids=["classic", "gia"])
def test_mapping_area_and_timing_controls(namespace, and_aig):
    result = namespace.if_(and_aig, area_oriented_mapping=True, area_flow_rounds=0, ela_rounds=0, delay_relaxation=20)
    assert algorithms.equivalence_checking(and_aig, result)


@pytest.mark.parametrize("namespace", [abc, abc.gia], ids=["classic", "gia"])
def test_lut_input_reaches_binary_discovery(namespace, named_klut_basic, tmp_path):
    with pytest.raises(abc.AbcNotFoundError):
        namespace.if_(named_klut_basic, binary=tmp_path / "missing")


@pytest.mark.usefixtures("abc_available")
@pytest.mark.parametrize("namespace", [abc, abc.gia], ids=["classic", "gia"])
@pytest.mark.parametrize("jobs", [1, 2])
def test_lut_batches_return_failures_in_place(namespace, and_aig, jobs):
    results = namespace.run_many(
        [Aig(), and_aig], namespace.if_.cmd(), output_type="klut", jobs=jobs, return_exceptions=True, timeout=10
    )
    assert isinstance(results[0], abc.AbcExecutionError)
    assert isinstance(results[1], Klut)
    assert algorithms.equivalence_checking(and_aig, results[1])
