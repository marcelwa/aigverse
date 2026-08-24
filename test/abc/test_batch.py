"""Tests for `run_many`, the parallel map over the ABC bridge.

Every argument is validated before a single process starts, so the validation
half needs neither ABC nor a stand-in and runs everywhere. The concurrency half
is driven by `fake_abc` shims that branch on the input network's primary-input
count, which is what makes a batch's items distinguishable from inside ABC.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from aigverse.abc import (
    AbcError,
    AbcExecutionError,
    AbcTimeoutError,
    expand_script,
    gia,
    run_many,
    run_script,
    set_abc_binary,
)
from aigverse.networks import Aig, NamedAig, SequentialAig

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

# The fake-ABC shims rely on the executable bit, which does not carry over on Windows.
requires_posix = pytest.mark.skipif(sys.platform == "win32", reason="the fake ABC shims rely on POSIX executable bits")

# Reads the primary-input count out of the binary AIGER header, which is
# `aig M I L O A`. It is the only thing telling a shim which item it is running.
_READ_INPUTS = """
import os
cwd = pathlib.Path.cwd()
source = cwd / "in.aig"
inputs = int(source.read_bytes().split(b"\\n")[0].split()[2])
"""

# A well-behaved ABC that changes nothing.
_HAPPY = (
    _READ_INPUTS
    + """
(cwd / "out.aig").write_bytes(source.read_bytes())
"""
)

# Finishes in reverse submission order, so a batch that returned results as they
# complete would come back scrambled rather than merely lucky.
_HAPPY_REVERSED = (
    _READ_INPUTS
    + """
time.sleep(0.05 * (12 - inputs))
(cwd / "out.aig").write_bytes(source.read_bytes())
"""
)


def aig_with_pis(count: int) -> Aig:
    """Builds a network with a given number of primary inputs.

    Args:
        count: How many primary inputs to create, at least two.

    Returns:
        A network whose AIGER header carries ``count`` as its input count.
    """
    ntk = Aig()
    pis = [ntk.create_pi() for _ in range(count)]
    ntk.create_po(ntk.create_and(pis[0], pis[1]))
    return ntk


def hide_abc(monkeypatch: pytest.MonkeyPatch) -> None:
    """Makes discovery fail, so a test can prove a check runs before it.

    Args:
        monkeypatch: Used to hide any installed ABC.
    """
    monkeypatch.delenv("AIGVERSE_ABC", raising=False)
    monkeypatch.setenv("PATH", "")


# --------------------------------------------------------------------------------------
# Validation -- no ABC, no shim, every platform
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("jobs", [0, -1])
def test_non_positive_jobs_is_rejected(monkeypatch: pytest.MonkeyPatch, and_aig: Aig, jobs: int) -> None:
    """`jobs` is checked before anything looks for ABC.

    Args:
        monkeypatch: Used to hide any installed ABC.
        and_aig: A small network to batch.
        jobs: The rejected worker count.
    """
    hide_abc(monkeypatch)
    with pytest.raises(ValueError, match="jobs must be at least 1"):
        run_many([and_aig], "balance", jobs=jobs)


def test_empty_batch_needs_no_abc(monkeypatch: pytest.MonkeyPatch) -> None:
    """Nothing to run is not an error, so it must not require an executable.

    Args:
        monkeypatch: Used to hide any installed ABC.
    """
    hide_abc(monkeypatch)
    assert run_many([], "balance") == []


def test_empty_batch_still_rejects_an_empty_script(monkeypatch: pytest.MonkeyPatch) -> None:
    """A typo in the script must not pass because the data happened to be empty.

    Args:
        monkeypatch: Used to hide any installed ABC.
    """
    hide_abc(monkeypatch)
    with pytest.raises(ValueError, match="no ABC commands"):
        run_many([], "   ")


@pytest.mark.parametrize("return_exceptions", [False, True])
def test_non_aig_is_rejected_either_way(
    monkeypatch: pytest.MonkeyPatch, and_aig: Aig, *, return_exceptions: bool
) -> None:
    """`return_exceptions` governs ABC failures, not a fault in the call itself.

    Args:
        monkeypatch: Used to hide any installed ABC.
        and_aig: A valid network, so the rejection is about its neighbour.
        return_exceptions: Whether ABC failures would be returned in place.
    """
    hide_abc(monkeypatch)
    with pytest.raises(TypeError, match="expected an Aig"):
        run_many(  # ty: ignore[no-matching-overload]
            [and_aig, "not a network"],
            "balance",
            return_exceptions=return_exceptions,
        )


def test_gia_rejects_an_undefined_reset(
    monkeypatch: pytest.MonkeyPatch, sequential_aig: Callable[..., SequentialAig]
) -> None:
    """Every network is guarded, not just the first one.

    Args:
        monkeypatch: Used to hide any installed ABC.
        sequential_aig: Builds the network; called with no reset value.
    """
    hide_abc(monkeypatch)
    with pytest.raises(ValueError, match="no defined reset value"):
        gia.run_many([sequential_aig(0), sequential_aig()], "&syn2")


# --------------------------------------------------------------------------------------
# Concurrency -- a stand-in ABC, still no real one
# --------------------------------------------------------------------------------------


@requires_posix
def test_results_come_back_in_input_order(fake_abc: Callable[[str], Path]) -> None:
    """The shim finishes in reverse, so completion order cannot pass by accident.

    Args:
        fake_abc: Builds the stand-in executable.
    """
    networks = [aig_with_pis(count) for count in range(2, 10)]

    results = run_many(networks, "balance", jobs=4, binary=fake_abc(_HAPPY_REVERSED))

    assert [result.num_pis for result in results] == [network.num_pis for network in networks]


@requires_posix
def test_failures_are_returned_in_place(fake_abc: Callable[[str], Path]) -> None:
    """One bad network must not cost the sweep the results of the good ones.

    Args:
        fake_abc: Builds the stand-in executable.
    """
    shim = fake_abc(
        _READ_INPUTS
        + """
if inputs % 2:
    print("** cmd error: unknown command 'nope'")
    sys.exit(0)
(cwd / "out.aig").write_bytes(source.read_bytes())
"""
    )
    networks = [aig_with_pis(count) for count in range(2, 8)]

    results = run_many(networks, "balance", jobs=3, binary=shim, return_exceptions=True)

    failed = [index for index, result in enumerate(results) if isinstance(result, AbcError)]
    assert failed == [1, 3, 5]
    for index, result in enumerate(results):
        if index not in failed:
            assert isinstance(result, Aig)
            assert result.num_pis == networks[index].num_pis


@requires_posix
def test_a_failure_aborts_the_batch_by_default(fake_abc: Callable[[str], Path]) -> None:
    """Without `return_exceptions`, a batch fails the way a single call does.

    Args:
        fake_abc: Builds the stand-in executable.
    """
    shim = fake_abc("print(\"** cmd error: unknown command 'nope'\")\nsys.exit(0)")
    networks = [aig_with_pis(count) for count in range(2, 6)]

    with pytest.raises(AbcExecutionError, match="unknown command"):
        run_many(networks, "nope", jobs=2, binary=shim)


@requires_posix
@pytest.mark.skipif(sys.version_info < (3, 11), reason="exception notes are 3.11+")
def test_a_raised_failure_names_its_network(fake_abc: Callable[[str], Path]) -> None:
    """The raised error says which input it belongs to; the command alone does not.

    Args:
        fake_abc: Builds the stand-in executable.
    """
    shim = fake_abc(
        _READ_INPUTS
        + """
if inputs == 4:
    print("** cmd error: unknown command 'nope'")
    sys.exit(0)
(cwd / "out.aig").write_bytes(source.read_bytes())
"""
    )
    networks = [aig_with_pis(count) for count in (2, 3, 4, 5)]

    with pytest.raises(AbcExecutionError) as excinfo:
        run_many(networks, "balance", jobs=2, binary=shim)

    assert any("index 2" in note for note in excinfo.value.__notes__)


@requires_posix
def test_a_failure_cancels_the_queued_networks(tmp_path: Path, fake_abc: Callable[[str], Path]) -> None:
    """Aborting a batch must stop it, not merely stop reporting it.

    Args:
        tmp_path: Holds the marker directory the shim records itself in.
        fake_abc: Builds the stand-in executable.
    """
    markers = tmp_path / "markers"
    markers.mkdir()
    shim = fake_abc(
        _READ_INPUTS
        + f"""
(pathlib.Path({str(markers)!r}) / f"{{os.getpid()}}").touch()
if inputs == 2:
    print("** cmd error: unknown command 'nope'")
    sys.exit(0)
time.sleep(1.0)
(cwd / "out.aig").write_bytes(source.read_bytes())
"""
    )
    # The failing network is submitted first, so everything after it is still queued.
    networks = [aig_with_pis(2), *(aig_with_pis(3) for _ in range(40))]

    with pytest.raises(AbcExecutionError):
        run_many(networks, "balance", jobs=2, binary=shim)

    # Two workers, so at most a handful can have started; the margin is deliberately
    # enormous, because what is being pinned is "not all of them", not a count.
    assert len(list(markers.iterdir())) < len(networks) // 2


@requires_posix
def test_timeout_applies_to_each_network(and_aig: Aig, fake_abc: Callable[[str], Path]) -> None:
    """`timeout` is a per-network budget, so every network hits it rather than one.

    Args:
        and_aig: A small network to batch.
        fake_abc: Builds the stand-in executable.
    """
    shim = fake_abc("time.sleep(30)")

    results = run_many([and_aig, and_aig], "balance", jobs=2, timeout=0.5, binary=shim, return_exceptions=True)

    assert [type(result) for result in results] == [AbcTimeoutError, AbcTimeoutError]


@requires_posix
def test_one_job_runs_without_a_thread_pool(
    monkeypatch: pytest.MonkeyPatch, and_aig: Aig, fake_abc: Callable[[str], Path]
) -> None:
    """`jobs=1` is a genuine serial loop, so a traceback carries no worker frame.

    Args:
        monkeypatch: Used to make any pool construction fail loudly.
        and_aig: A small network to batch.
        fake_abc: Builds the stand-in executable.
    """
    from aigverse.abc import _batch

    def refuse(*_args: object, **_kwargs: object) -> None:
        """Fails if a thread pool is constructed at all.

        Raises:
            AssertionError: Always.
        """
        msg = "jobs=1 must not build a thread pool"
        raise AssertionError(msg)

    monkeypatch.setattr(_batch, "ThreadPoolExecutor", refuse)

    results = run_many([and_aig, and_aig], "balance", jobs=1, binary=fake_abc(_HAPPY))

    assert len(results) == 2


@requires_posix
def test_the_binary_is_resolved_once_for_a_batch(
    monkeypatch: pytest.MonkeyPatch, fake_abc: Callable[[str], Path]
) -> None:
    """Discovery walks PATH, so a batch must not repeat it per network.

    Args:
        monkeypatch: Used to count discovery calls.
        fake_abc: Builds the stand-in executable.
    """
    from aigverse.abc import _binary, _runner

    calls = 0

    def counted() -> Path:
        """Counts a discovery call and performs it.

        Returns:
            The resolved ABC executable.
        """
        nonlocal calls
        calls += 1
        return _binary.abc_binary()

    monkeypatch.setattr(_runner, "abc_binary", counted)
    set_abc_binary(fake_abc(_HAPPY))

    run_many([aig_with_pis(count) for count in range(2, 7)], "balance", jobs=2)

    assert calls == 1


@requires_posix
def test_a_single_call_resolves_the_binary_once(
    monkeypatch: pytest.MonkeyPatch, and_aig: Aig, fake_abc: Callable[[str], Path]
) -> None:
    """`run_script` used to resolve again after ABC had run, only to name it in errors.

    Args:
        monkeypatch: Used to count discovery calls.
        and_aig: A small network to optimize.
        fake_abc: Builds the stand-in executable.
    """
    from aigverse.abc import _binary, _runner

    calls = 0

    def counted() -> Path:
        """Counts a discovery call and performs it.

        Returns:
            The resolved ABC executable.
        """
        nonlocal calls
        calls += 1
        return _binary.abc_binary()

    monkeypatch.setattr(_runner, "abc_binary", counted)
    set_abc_binary(fake_abc(_HAPPY))

    run_script(and_aig, "balance")

    assert calls == 1


@requires_posix
def test_gia_batch_uses_the_gia_transfer(and_aig: Aig, fake_abc: Callable[[str], Path]) -> None:
    """The `gia` namespace loads the GIA store, as its single-network twin does.

    Args:
        and_aig: A small network to batch.
        fake_abc: Builds the stand-in executable.
    """
    shim = fake_abc("print(\"** cmd error: unknown command 'nope'\")\nsys.exit(0)")

    results = gia.run_many([and_aig], "nope", binary=shim, return_exceptions=True)

    failure = results[0]
    assert isinstance(failure, AbcExecutionError)
    assert "&read in.aig" in failure.command
    assert "&write out.aig" in failure.command


@requires_posix
def test_every_network_keeps_its_type(
    and_aig: Aig, sequential_aig: Callable[..., SequentialAig], fake_abc: Callable[[str], Path]
) -> None:
    """A batch is as type-preserving as the single-network path it delegates to.

    Args:
        and_aig: The plain-Aig member of the batch.
        sequential_aig: Builds the SequentialAig member.
        fake_abc: Builds the stand-in executable.
    """
    named = NamedAig()
    x0 = named.create_pi()
    named.set_name(x0, "alpha")
    named.create_po(named.create_and(x0, named.create_pi()))

    networks: list[Aig] = [and_aig, named, sequential_aig(0)]

    results = run_many(networks, "balance", jobs=2, binary=fake_abc(_HAPPY))

    assert [type(result) for result in results] == [Aig, NamedAig, SequentialAig]


# --------------------------------------------------------------------------------------
# Integration -- a real ABC
# --------------------------------------------------------------------------------------


@pytest.mark.usefixtures("abc_available")
def test_a_batch_matches_a_serial_loop() -> None:
    """A batch is a parallel map, so it must agree with the loop it replaces."""
    from aigverse.generators import carry_lookahead_adder, ripple_carry_adder

    networks = [ripple_carry_adder(8), carry_lookahead_adder(8), ripple_carry_adder(12)]
    script = expand_script("resyn2")

    batched = run_many(networks, script)
    serial = [run_script(network, script) for network in networks]

    assert [result.num_gates for result in batched] == [result.num_gates for result in serial]


@pytest.mark.usefixtures("abc_available")
def test_a_gia_batch_matches_a_serial_loop() -> None:
    """The same, through the `&`-space transfer."""
    from aigverse.generators import carry_lookahead_adder, ripple_carry_adder

    networks = [ripple_carry_adder(8), carry_lookahead_adder(8)]

    batched = gia.run_many(networks, "&syn2")
    serial = [gia.run_script(network, "&syn2") for network in networks]

    assert [result.num_gates for result in batched] == [result.num_gates for result in serial]
