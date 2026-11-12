from __future__ import annotations

import pytest

from aigverse import algorithms
from aigverse.networks import Aig, DepthAig, DepthKlut, FanoutAig, Klut, NamedAig, NamedKlut, SequentialAig

ALGORITHMS = ("heuristic", "classic", "sat", "sat_windowed")


@pytest.mark.parametrize("algorithm", ALGORITHMS)
@pytest.mark.parametrize("cut_size", [2, 6, 16])
def test_mapping_preserves_function_interface_and_source(mapping_aig, algorithm, cut_size):
    before = algorithms.simulate(mapping_aig)
    original_size = mapping_aig.size
    mapped = algorithms.lut_mapping(mapping_aig, algorithm=algorithm, cut_size=cut_size, cut_limit=1)

    assert isinstance(mapped, NamedKlut)
    assert algorithms.simulate(mapped) == before
    assert mapped.num_pis == 4
    assert mapped.get_network_name() == "mapping"
    assert [mapped.get_name(mapped.pi_at(i)) for i in range(4)] == ["a", "b", "c", "unused"]
    assert [mapped.get_output_name(i) for i in range(mapped.num_pos)] == [
        "f",
        "not_f",
        "again",
        "a_out",
        "not_a",
        "zero",
        "one",
    ]
    assert all(mapped.fanin_size(n) <= cut_size for n in mapped.gates())
    assert all(mapped.node_function(n).num_vars() == mapped.fanin_size(n) for n in mapped.gates())
    assert mapping_aig.size == original_size
    assert algorithms.simulate(mapping_aig) == before
    mapped.create_pi()
    assert mapping_aig.num_pis == 4


@pytest.mark.parametrize("algorithm", ALGORITHMS)
@pytest.mark.parametrize("shape", ["empty", "constants", "direct", "dangling", "one_gate"])
def test_mapping_small_networks(algorithm, shape):
    ntk = Aig()
    if shape == "constants":
        ntk.create_po(ntk.get_constant(False))
        ntk.create_po(ntk.get_constant(True))
    elif shape != "empty":
        a, b = ntk.create_pi(), ntk.create_pi()
        gate = ntk.create_and(a, b) if shape in {"dangling", "one_gate"} else a
        ntk.create_po(gate if shape == "one_gate" else a)
        ntk.create_po(~a)
    mapped = algorithms.lut_mapping(ntk, algorithm=algorithm)
    assert type(mapped) is Klut
    assert algorithms.simulate(mapped) == algorithms.simulate(ntk)


@pytest.mark.parametrize("view", [DepthAig, FanoutAig])
def test_mapping_aig_views(simple_and_aig, view):
    assert algorithms.simulate(algorithms.lut_mapping(view(simple_and_aig))) == algorithms.simulate(simple_and_aig)


@pytest.mark.parametrize(
    "options",
    [
        {"compute_truth": True},
        {"compute_truth": True, "minimize_truth_table": False},
        {"recompute_cuts": False},
        {"area_oriented_mapping": True},
        {"required_delay": 4},
        {"relax_required": 20},
        {"area_share_rounds": 0, "area_flow_rounds": 0, "ela_rounds": 0},
        {"edge_optimization": False, "cut_expansion": False, "remove_dominated_cuts": False},
        {"cut_limit": 31},
    ],
)
def test_heuristic_controls(mapping_aig, options):
    assert algorithms.simulate(algorithms.lut_mapping(mapping_aig, **options)) == algorithms.simulate(mapping_aig)


@pytest.mark.parametrize("algorithm", ["classic", "sat", "sat_windowed"])
def test_classic_and_sat_controls(mapping_aig, algorithm):
    mapped = algorithms.lut_mapping(
        mapping_aig,
        algorithm=algorithm,
        cut_limit=24,
        area_oriented_mapping=True,
        area_flow_rounds=0,
        ela_rounds=0,
        conflict_limit=0 if algorithm != "classic" else None,
        window_size=1 if algorithm == "sat_windowed" else None,
    )
    assert algorithms.simulate(mapped) == algorithms.simulate(mapping_aig)


@pytest.mark.parametrize("algorithm", ["classic", "sat", "sat_windowed"])
@pytest.mark.parametrize(
    ("option", "value"),
    [
        ("compute_truth", False),
        ("minimize_truth_table", False),
        ("required_delay", 0),
        ("relax_required", 0),
        ("recompute_cuts", True),
        ("area_share_rounds", 0),
        ("edge_optimization", False),
        ("cut_expansion", False),
        ("remove_dominated_cuts", True),
    ],
)
def test_rejects_heuristic_options_for_other_algorithms(simple_and_aig, algorithm, option, value):
    with pytest.raises(ValueError, match="heuristic"):
        algorithms.lut_mapping(simple_and_aig, algorithm=algorithm, **{option: value})


@pytest.mark.parametrize(
    "options",
    [
        {"algorithm": "unknown"},
        {"cut_size": 1},
        {"cut_size": 17},
        {"cut_limit": 0},
        {"cut_limit": 32},
        {"algorithm": "classic", "cut_limit": 25},
        {"algorithm": "classic", "area_oriented_mapping": False},
        {"area_flow_rounds": -1},
        {"ela_rounds": -1},
        {"area_share_rounds": -1},
        {"area_flow_rounds": 2**32},
        {"ela_rounds": 2**32},
        {"area_share_rounds": 2**32},
        {"algorithm": "classic", "area_flow_rounds": 2**32 - 1},
        {"algorithm": "classic", "area_flow_rounds": 2**32 - 2, "ela_rounds": 2},
        {"required_delay": -1},
        {"relax_required": -1},
        {"required_delay": 2**32},
        {"relax_required": 2**32},
        {"minimize_truth_table": True},
        {"compute_truth": True, "cut_expansion": True},
        {"recompute_cuts": False, "cut_expansion": True},
        {"required_delay": 3, "relax_required": 10},
        {"area_oriented_mapping": True, "required_delay": 0},
        {"area_oriented_mapping": True, "relax_required": 0},
        {"conflict_limit": 0},
        {"algorithm": "classic", "conflict_limit": 0},
        {"algorithm": "sat", "conflict_limit": -1},
        {"algorithm": "sat", "conflict_limit": 2**31},
        {"window_size": 32},
        {"algorithm": "sat", "window_size": 32},
        {"algorithm": "sat_windowed", "window_size": 0},
        {"algorithm": "sat_windowed", "window_size": -1},
        {"algorithm": "sat_windowed", "window_size": 2**32},
    ],
)
def test_mapping_rejects_invalid_controls(simple_and_aig, options):
    with pytest.raises(ValueError, match=r".+"):
        algorithms.lut_mapping(simple_and_aig, **options)


@pytest.mark.parametrize(
    "options",
    [
        {"required_delay": 2**32 - 1},
        {"relax_required": 2**32 - 1},
        {"algorithm": "sat", "conflict_limit": 2**31 - 1},
        {"algorithm": "sat_windowed", "window_size": 2**32 - 1},
        {"algorithm": "classic", "area_flow_rounds": 2**32 - 2, "ela_rounds": 0},
        {"algorithm": "classic", "area_flow_rounds": 0, "ela_rounds": 2**32 - 2},
        {"area_flow_rounds": 0, "ela_rounds": 0, "area_share_rounds": 2**32 - 4},
    ],
)
def test_mapping_accepts_integer_boundaries_without_running_passes(options):
    assert algorithms.lut_mapping(Aig(), **options).num_gates == 0


@pytest.mark.parametrize("map_network", [algorithms.lut_mapping])
def test_mapping_controls_are_keyword_only(simple_and_aig, map_network):
    with pytest.raises(TypeError, match="incompatible function arguments"):
        map_network(simple_and_aig, "classic")


def test_mapping_rejects_sequential_input():
    with pytest.raises(ValueError, match="combinational"):
        algorithms.lut_mapping(SequentialAig())


def test_mapping_rejects_relaxed_delay_overflow():
    ntk = Aig()
    signal = ntk.create_pi()
    for _ in range(101):
        signal = ntk.create_and(signal, ntk.create_pi())
    ntk.create_po(signal)
    with pytest.raises(ValueError, match="relax_required"):
        algorithms.lut_mapping(ntk, cut_size=2, relax_required=2**32 - 1)


def test_klut_simulation_preserves_fanin_order(asymmetric_klut):
    assert algorithms.simulate(asymmetric_klut)[0].to_binary() == "0010"
    simulated = algorithms.simulate_nodes(DepthKlut(asymmetric_klut))
    assert simulated[asymmetric_klut.po_at(0)].to_binary() == "0010"
    assert simulated[0].is_const0()
    assert simulated[1].is_const1()


@pytest.mark.parametrize("network", [Aig, Klut])
@pytest.mark.parametrize("simulate", [algorithms.simulate, algorithms.simulate_nodes])
def test_full_simulation_rejects_unrepresentable_input_count(network, simulate):
    ntk = network()
    for _ in range(32):
        ntk.create_pi()
    with pytest.raises(ValueError, match="32"):
        simulate(ntk)


def test_cleanup_klut_preserves_names_and_source(named_klut_basic):
    ntk = named_klut_basic
    extra = ntk.create_pi("unused")
    ntk.create_xor(ntk.pi_at(0), extra)
    ntk.create_po(ntk.po_at(0), "duplicate")
    before = algorithms.simulate(ntk)
    result = algorithms.cleanup_dangling(ntk)
    assert isinstance(result, NamedKlut)
    assert result.num_gates == 1
    assert ntk.num_gates == 2
    assert algorithms.simulate(result) == before
    assert result.get_network_name() == "top"
    assert result.get_name(result.pi_at(2)) == "unused"
    assert result.get_output_name(1) == "duplicate"
    result.create_po(result.pi_at(0), "direct")
    compact = algorithms.cleanup_dangling(result, remove_dangling_pis=True, remove_redundant_pos=True)
    assert compact.num_pis == 2
    assert compact.num_pos == 2
    assert compact.get_output_name(0) == "out"


def test_cleanup_plain_klut(asymmetric_klut):
    asymmetric_klut.create_xor(asymmetric_klut.pi_at(0), asymmetric_klut.pi_at(1))
    result = algorithms.cleanup_dangling(asymmetric_klut)
    assert type(result) is Klut
    assert result.num_gates == 1
    assert asymmetric_klut.num_gates == 2
    assert algorithms.simulate(result)[0].to_binary() == "0010"


def test_conversion_preserves_named_interface(named_klut_basic):
    converted = algorithms.convert_klut_to_aig(named_klut_basic)
    assert isinstance(converted, NamedAig)
    assert converted.get_network_name() == "top"
    assert converted.get_name(converted.make_signal(converted.pi_at(0))) == "a"
    assert converted.get_output_name(0) == "out"
    assert algorithms.simulate(converted) == algorithms.simulate(named_klut_basic)
    converted.create_pi()
    assert named_klut_basic.num_pis == 2


def test_cleanup_names_follow_retained_outputs():
    ntk = NamedKlut()
    a, b = ntk.create_pi("a"), ntk.create_pi("b")
    gate = ntk.create_and(a, b)
    ntk.set_name(gate, "and_gate")
    ntk.create_po(a, "direct")
    ntk.create_po(gate)
    ntk.create_po(ntk.get_constant(False), "constant")
    ntk.create_po(gate, "retained")
    cleaned = algorithms.cleanup_dangling(ntk, remove_redundant_pos=True)
    assert cleaned.num_pos == 2
    assert not cleaned.has_output_name(0)
    assert cleaned.get_output_name(1) == "retained"
    assert cleaned.get_name(cleaned.po_at(0)) == "and_gate"
    assert ntk.get_output_name(0) == "direct"


def test_conversion_preserves_asymmetric_function(asymmetric_klut):
    converted = algorithms.convert_klut_to_aig(asymmetric_klut)
    assert type(converted) is Aig
    assert algorithms.simulate(converted)[0].to_binary() == "0010"


@pytest.mark.parametrize("functional_reduction", [True, False])
@pytest.mark.parametrize("left_klut", [True, False])
@pytest.mark.parametrize("right_klut", [True, False])
def test_equivalence_across_representations(asymmetric_klut, *, functional_reduction, left_klut, right_klut):
    aig = Aig()
    a, b = aig.create_pi(), aig.create_pi()
    aig.create_po(aig.create_and(a, ~b))
    left = asymmetric_klut if left_klut else aig
    right = asymmetric_klut if right_klut else aig
    assert algorithms.equivalence_checking(left, right, functional_reduction=functional_reduction)
    other = Klut()
    x, y = other.create_pi(), other.create_pi()
    other.create_po(other.create_and(x, y))
    assert not algorithms.equivalence_checking(left, other, functional_reduction=functional_reduction)


@pytest.mark.parametrize("left_klut", [True, False])
def test_cross_equivalence_rejects_sequential_inputs(left_klut):
    pair = (Klut(), SequentialAig()) if left_klut else (SequentialAig(), Klut())
    with pytest.raises(ValueError, match="combinational"):
        algorithms.equivalence_checking(*pair)


def test_cross_equivalence_rejects_mismatched_interfaces(simple_and_aig):
    with pytest.raises(RuntimeError, match="PIs or POs"):
        algorithms.equivalence_checking(simple_and_aig, Klut())
