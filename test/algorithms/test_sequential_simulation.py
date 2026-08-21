from __future__ import annotations

import pytest

from aigverse.algorithms import simulate_sequential
from aigverse.networks import AigRegister, SequentialAig


def lfsr(width: int = 4, seed: int = 1) -> SequentialAig:
    """Builds a Fibonacci LFSR with taps on the top two bits.

    It has no primary inputs at all, so it runs off its reset state alone, which
    makes it a direct test of whether the reset values are honored.

    Args:
        width: Number of registers.
        seed: Reset state, as an integer whose bit ``i`` is register ``i``'s reset.

    Returns:
        The sequential network.
    """
    ntk = SequentialAig()

    state = [ntk.create_ro() for _ in range(width)]
    feedback = ntk.create_xor(state[width - 1], state[width - 2])

    # Primary outputs before register inputs: both are combinational outputs of
    # the same network, and `po_at` / `ri_at` slice that one list by position.
    ntk.create_po(state[width - 1])

    ntk.create_ri(feedback)
    for bit in range(width - 1):
        ntk.create_ri(state[bit])

    for bit in range(width):
        register = AigRegister()
        register.init = (seed >> bit) & 1
        ntk.set_register(bit, register)

    return ntk


def shift_register(depth: int = 3) -> SequentialAig:
    """Builds a shift register: the input appears at the output ``depth`` cycles later.

    Args:
        depth: Number of registers in the chain.

    Returns:
        The sequential network.
    """
    ntk = SequentialAig()

    data = ntk.create_pi()
    state = [ntk.create_ro() for _ in range(depth)]

    ntk.create_po(state[depth - 1])

    ntk.create_ri(data)
    for stage in range(depth - 1):
        ntk.create_ri(state[stage])

    for stage in range(depth):
        register = AigRegister()
        register.init = 0
        ntk.set_register(stage, register)

    return ntk


def bits(outputs: list[list[bool]]) -> str:
    """Collects the single primary output of every cycle into a bit string.

    Args:
        outputs: The per-cycle output trace.

    Returns:
        One character per cycle.
    """
    return "".join(str(int(cycle[0])) for cycle in outputs)


def test_lfsr_runs_from_its_reset_state() -> None:
    result = simulate_sequential(lfsr(), 15)

    assert result.num_cycles == 15
    assert len(result) == 15
    # a maximal-length sequence: 15 states before it comes back around
    assert bits(result.outputs) == "000100110101111"


def test_lfsr_returns_to_its_seed() -> None:
    result = simulate_sequential(lfsr(), 30)

    trace = bits(result.outputs)
    assert trace[:15] == trace[15:]
    assert result.final_state == result.reset_state


def test_a_different_seed_shifts_the_sequence() -> None:
    # seeding with the second state of the first LFSR must produce the same
    # sequence one step ahead, which only holds if the reset values are used
    from_one = bits(simulate_sequential(lfsr(seed=1), 15).outputs)
    from_two = bits(simulate_sequential(lfsr(seed=2), 15).outputs)

    assert from_one[1:] == from_two[:14]


def test_the_state_trace_is_one_longer_than_the_output_trace() -> None:
    # simulating n cycles crosses n + 1 state boundaries
    result = simulate_sequential(lfsr(), 15)

    assert len(result.states) == len(result.outputs) + 1
    assert result.reset_state == result.states[0]
    assert result.final_state == result.states[-1]
    assert result.reset_state == [True, False, False, False]


def test_every_lfsr_state_is_distinct_and_non_zero() -> None:
    result = simulate_sequential(lfsr(), 15)

    seen = [tuple(state) for state in result.states[:-1]]

    assert all(any(state) for state in seen)
    assert len(set(seen)) == len(seen)


def test_simulating_no_cycles_still_reports_the_reset_state() -> None:
    result = simulate_sequential(lfsr(), 0)

    assert result.num_cycles == 0
    assert result.outputs == []
    assert len(result.states) == 1
    assert result.reset_state == result.final_state == [True, False, False, False]


def test_a_pulse_travels_through_a_shift_register() -> None:
    # a single 1 on the input, then silence
    result = simulate_sequential(shift_register(), 6, [[True], [False]])

    assert bits(result.outputs) == "000100"


def test_a_stimulus_shorter_than_the_run_holds_its_last_assignment() -> None:
    result = simulate_sequential(shift_register(), 4, [[True]])

    assert bits(result.outputs) == "0001"


def test_without_a_stimulus_the_inputs_are_held_low() -> None:
    result = simulate_sequential(shift_register(), 4)

    assert bits(result.outputs) == "0000"


def test_a_register_holds_what_the_previous_cycle_latched() -> None:
    # one register, driven from the input and read out on the output: the output
    # of a cycle is the state it started in
    ntk = SequentialAig()
    data = ntk.create_pi()
    state = ntk.create_ro()
    ntk.create_po(state)
    ntk.create_ri(data)

    register = AigRegister()
    register.init = 0
    ntk.set_register(0, register)

    result = simulate_sequential(ntk, 3, [[True], [False], [True]])

    assert bits(result.outputs) == "010"
    for cycle in range(result.num_cycles):
        assert result.states[cycle][0] == result.outputs[cycle][0]

    # the last input latched but never read out
    assert result.final_state == [True]


@pytest.mark.parametrize(("undefined", "expected"), [(False, "000"), (True, "111")])
def test_an_undefined_reset_follows_the_argument(*, undefined: bool, expected: str) -> None:
    ntk = SequentialAig()
    state = ntk.create_ro()
    ntk.create_po(state)
    ntk.create_ri(state)
    ntk.set_register(0, AigRegister())  # a fresh descriptor has no reset value

    assert ntk.register_at(0).init not in {0, 1}

    result = simulate_sequential(ntk, 3, undefined_reset_value=undefined)

    assert bits(result.outputs) == expected


def test_a_stimulus_of_the_wrong_width_is_rejected() -> None:
    ntk = shift_register()

    with pytest.raises(ValueError, match="assigns 2 value"):
        simulate_sequential(ntk, 3, [[True, False]])

    with pytest.raises(ValueError, match="cycle 1"):
        simulate_sequential(ntk, 3, [[True], []])


def test_repr_names_the_shape_of_the_run() -> None:
    result = simulate_sequential(lfsr(), 5)

    assert repr(result) == "SequentialSimulationResult(num_cycles=5, num_pos=1, num_registers=4)"
