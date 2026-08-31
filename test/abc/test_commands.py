"""Tests for the individual ABC command wrappers.

Each wrapper builds its command through `cmd()`, so the argument translation is
asserted directly on the command it returns, without ABC and without a shim. That
a call actually issues the command it built is pinned separately, against a
stand-in ABC that always fails and therefore carries the generated script on the
raised error.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from aigverse.abc import (
    AbcExecutionError,
    Command,
    balance,
    gia,
    orchestrate,
    refactor,
    resub,
    rewrite,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from aigverse.networks import Aig

# The fake-ABC shims rely on the executable bit, which does not carry over on Windows.
requires_posix = pytest.mark.skipif(sys.platform == "win32", reason="the fake ABC shims rely on POSIX executable bits")

_FAILING = 'print("** cmd error: stop right there")'


def _command_for(run: Callable[[], object]) -> str:
    """Runs a wrapper against a failing ABC and returns the script it generated.

    Args:
        run: A zero-argument callable invoking the wrapper under test.

    Returns:
        The full ABC script the bridge assembled.
    """
    with pytest.raises(AbcExecutionError) as excinfo:
        run()
    return excinfo.value.command


@pytest.mark.parametrize(
    ("build", "expected"),
    [
        (balance.cmd, "balance"),
        (lambda: balance.cmd(minimize_levels=False), "balance -l"),
        (lambda: balance.cmd(exor=True, duplicate=True), "balance -d -x"),
        (lambda: balance.cmd(duplicate_critical=True), "balance -s"),
        (lambda: refactor.cmd(min_saved=0), "refactor -M 0"),
        (lambda: resub.cmd(min_saved=0, odc_levels=2), "resub -M 0 -F 2"),
        (rewrite.cmd, "rewrite"),
        (lambda: rewrite.cmd(zero_cost=True), "rewrite -z"),
        (lambda: rewrite.cmd(preserve_levels=False), "rewrite -l"),
        (refactor.cmd, "refactor"),
        (lambda: refactor.cmd(max_support=12, zero_cost=True), "refactor -N 12 -z"),
        (resub.cmd, "resub"),
        (lambda: resub.cmd(max_cut_size=6), "resub -K 6"),
        (lambda: resub.cmd(max_cut_size=12, max_inserts=2), "resub -K 12 -N 2"),
    ],
    ids=[
        "balance-default",
        "balance-no-level-minimization",
        "balance-exor-and-duplication",
        "balance-duplicate-critical",
        "refactor-min-saved",
        "resub-min-saved-and-odc",
        "rewrite-default",
        "rewrite-zero-cost",
        "rewrite-no-level-preservation",
        "refactor-default",
        "refactor-support-and-zero-cost",
        "resub-default",
        "resub-cut-size",
        "resub-cut-size-and-inserts",
    ],
)
def test_options_translate_to_abc_switches(build: Callable[[], Command], expected: str) -> None:
    """Keyword arguments must map onto exactly the ABC switches they claim to.

    Args:
        build: Builds the command of the wrapper under test.
        expected: The ABC command the wrapper is expected to build.
    """
    assert str(build()) == expected


def test_level_switch_is_inverted() -> None:
    """ABC's `-l` toggles a default of "preserve levels", so it must appear only
    when preservation is switched off -- getting this backwards silently changes
    what every wrapper optimizes for.
    """
    assert " -l" not in str(rewrite.cmd(preserve_levels=True))
    assert " -l" in str(rewrite.cmd(preserve_levels=False))


@pytest.mark.parametrize(
    ("build", "message"),
    [
        (lambda: refactor.cmd(max_support=0), "max_support must be between 1 and 15"),
        (lambda: resub.cmd(max_cut_size=3), "max_cut_size must be between 4 and 16"),
        (lambda: resub.cmd(max_cut_size=17), "max_cut_size must be between 4 and 16"),
        (lambda: resub.cmd(max_inserts=4), "max_inserts must be between 0 and 3"),
    ],
    ids=["refactor-support", "resub-cut-too-small", "resub-cut-too-large", "resub-inserts"],
)
def test_out_of_range_options_are_rejected(build: Callable[[], Command], message: str) -> None:
    """Values ABC would reject are caught while the command is built, before any
    process could be started.

    Args:
        build: Builds the command with an out-of-range option.
        message: Expected substring of the raised error.
    """
    with pytest.raises(ValueError, match=message):
        build()


@pytest.mark.parametrize(
    ("build", "expected"),
    [
        (gia.balance.cmd, "&b"),
        (lambda: gia.balance.cmd(delay_only=True, and_only=True), "&b -d -a"),
        (lambda: gia.balance.cmd(max_fanout=64, strict_area=True), "&b -N 64 -s"),
        (gia.resub.cmd, "&resub"),
        (lambda: gia.resub.cmd(max_inserts=2, max_support=6), "&resub -N 2 -S 6"),
        (gia.dc2.cmd, "&dc2"),
        (lambda: gia.dc2.cmd(update_levels=False), "&dc2 -l"),
        (gia.syn2.cmd, "&syn2"),
        (lambda: gia.syn2.cmd(delay_relaxation=0), "&syn2 -R 0"),
        (lambda: gia.syn2.cmd(old_algorithm=True, coarsen=False), "&syn2 -a -k"),
        (gia.syn3.cmd, "&syn3"),
        (gia.syn4.cmd, "&syn4"),
        (lambda: gia.fraig.cmd(conflict_limit=100), "&fraig -C 100"),
    ],
    ids=[
        "gia-balance-default",
        "gia-balance-delay-and-only",
        "gia-balance-fanout-and-strict-area",
        "gia-resub-default",
        "gia-resub-limits",
        "gia-dc2-default",
        "gia-dc2-no-level-update",
        "gia-syn2-default",
        "gia-syn2-relaxation-zero",
        "gia-syn2-old-and-no-coarsening",
        "gia-syn3",
        "gia-syn4",
        "gia-fraig-conflict-limit",
    ],
)
def test_gia_options_translate_to_abc_switches(build: Callable[[], Command], expected: str) -> None:
    """The `&`-space wrappers must build exactly the commands they claim to.

    Args:
        build: Builds the command of the wrapper under test.
        expected: The ABC command the wrapper is expected to build.
    """
    assert str(build()) == expected


def test_delay_relaxation_of_zero_is_not_dropped() -> None:
    """`0` is a meaningful relaxation ratio and must survive the `None` default."""
    assert "-R 0" in str(gia.syn2.cmd(delay_relaxation=0))


@pytest.mark.parametrize(
    ("build", "message"),
    [
        (lambda: gia.resub.cmd(max_inserts=-1), "max_inserts must be at least 0"),
        (lambda: gia.syn2.cmd(delay_relaxation=-1), "delay_relaxation must be at least 0"),
        (lambda: gia.fraig.cmd(conflict_limit=-1), "conflict_limit must be at least 0"),
    ],
    ids=["gia-resub-inserts", "gia-syn2-relaxation", "gia-fraig-conflicts"],
)
def test_negative_gia_options_are_rejected(build: Callable[[], Command], message: str) -> None:
    """Negative limits are caught while the command is built.

    Args:
        build: Builds the command with a negative option.
        message: Expected substring of the raised error.
    """
    with pytest.raises(ValueError, match=message):
        build()


@pytest.mark.parametrize(
    ("build", "expected"),
    [
        (orchestrate.cmd, "orchestrate"),
        (lambda: orchestrate.cmd(max_cut_size=12), "orchestrate -K 12"),
        # every one of these three toggles a default of "on" for orchestrate
        (lambda: orchestrate.cmd(preserve_levels=False), "orchestrate -l"),
        (lambda: orchestrate.cmd(zero_cost_rewrite=False), "orchestrate -z"),
        (lambda: orchestrate.cmd(zero_cost_refactor=False), "orchestrate -Z"),
        (gia.deepsyn.cmd, "&deepsyn"),
        (lambda: gia.deepsyn.cmd(timeout=30, seed=7), "&deepsyn -T 30 -S 7"),
        (lambda: gia.deepsyn.cmd(patience=5, two_input_luts=True, optimize=True), "&deepsyn -J 5 -t -o"),
        (
            lambda: gia.transduction.cmd(fanin_sort=2, mspf=True, preserve_levels=True),
            "&transduction -V 0 -S 2 -m -l",
        ),
        (lambda: gia.transtoch.cmd(mspf=False, resub_shared=False), "&transtoch -V 0 -m -g"),
        (gia.transduction.cmd, "&transduction -V 0"),
        (lambda: gia.transduction.cmd(transduction_type=8), "&transduction -V 0 -T 8"),
        (gia.transtoch.cmd, "&transtoch -V 0"),
        (lambda: gia.transtoch.cmd(restarts=2, threads=4), "&transtoch -V 0 -N 2 -P 4"),
    ],
    ids=[
        "orchestrate-default",
        "orchestrate-cut-size",
        "orchestrate-no-level-preservation",
        "orchestrate-no-zero-cost-rewrite",
        "orchestrate-no-zero-cost-refactor",
        "deepsyn-default",
        "deepsyn-budget-and-seed",
        "deepsyn-patience-luts-optimize",
        "transduction-sort-mspf-levels",
        "transtoch-no-mspf-no-shared",
        "transduction-default",
        "transduction-type",
        "transtoch-default",
        "transtoch-restarts-and-threads",
    ],
)
def test_high_effort_options_translate_to_abc_switches(build: Callable[[], Command], expected: str) -> None:
    """The high-effort wrappers must build exactly the commands they claim to.

    Args:
        build: Builds the command of the wrapper under test.
        expected: The ABC command the wrapper is expected to build.
    """
    assert str(build()) == expected


def test_orchestrate_zero_cost_defaults_are_not_inverted() -> None:
    """`orchestrate` enables zero-cost replacements by default, unlike `rewrite`.

    Emitting `-z`/`-Z` for the default would turn them off, quietly making
    `orchestrate` weaker than ABC intends. Worth its own test because the two
    commands read the same switch in opposite directions.
    """
    default = str(orchestrate.cmd())
    assert " -z" not in default
    assert " -Z" not in default

    # ... whereas the standalone command has to be asked for it
    assert " -z" in str(rewrite.cmd(zero_cost=True))


@pytest.mark.parametrize(
    ("build", "message"),
    [
        (lambda: orchestrate.cmd(max_cut_size=3), "max_cut_size must be between 4 and 16"),
        (lambda: orchestrate.cmd(odc_levels=-1), "odc_levels must be at least 0"),
        (lambda: gia.deepsyn.cmd(seed=101), "seed must be between 0 and 100"),
        (lambda: gia.deepsyn.cmd(timeout=-1), "timeout must be at least 0"),
        (lambda: gia.transduction.cmd(transduction_type=9), "transduction_type must be between 0 and 8"),
        (lambda: gia.transtoch.cmd(threads=0), "threads must be at least 1"),
    ],
    ids=["orch-cut", "orch-odc", "deepsyn-seed", "deepsyn-budget", "transduction-type", "transtoch-threads"],
)
def test_high_effort_out_of_range_options_are_rejected(build: Callable[[], Command], message: str) -> None:
    """Values ABC would reject are caught while the command is built.

    Args:
        build: Builds the command with an out-of-range option.
        message: Expected substring of the raised error.
    """
    with pytest.raises(ValueError, match=message):
        build()


def test_a_command_is_hashable_and_compares_by_its_text() -> None:
    """A study keys its rows by command, which needs equality and hashing."""
    assert rewrite.cmd(zero_cost=True) == rewrite.cmd(zero_cost=True)
    assert rewrite.cmd(zero_cost=True) != rewrite.cmd()
    assert {rewrite.cmd(zero_cost=True): "row"}[Command("rewrite -z")] == "row"


@requires_posix
@pytest.mark.parametrize(
    ("call", "build"),
    [
        (lambda ntk, exe: rewrite(ntk, zero_cost=True, binary=exe), lambda: rewrite.cmd(zero_cost=True)),
        (lambda ntk, exe: resub(ntk, max_cut_size=12, binary=exe), lambda: resub.cmd(max_cut_size=12)),
        (lambda ntk, exe: orchestrate(ntk, odc_levels=2, binary=exe), lambda: orchestrate.cmd(odc_levels=2)),
    ],
    ids=["rewrite", "resub", "orchestrate"],
)
def test_a_call_issues_the_command_it_builds(
    call: Callable[[Aig, Path], object],
    build: Callable[[], Command],
    and_aig: Aig,
    fake_abc: Callable[[str], Path],
) -> None:
    """Calling a wrapper must send ABC exactly what its `cmd()` returns.

    Args:
        call: Invokes the wrapper under test with a network and a binary.
        build: Builds the command the same options are expected to produce.
        and_aig: A minimal two-input AND network.
        fake_abc: Factory for the stand-in ABC executable.
    """
    shim = fake_abc(_FAILING)
    script = _command_for(lambda: call(and_aig, shim))

    # the generated script wraps the command in the read and write steps
    assert f"; {build()}; " in script


@requires_posix
def test_a_gia_call_issues_its_command_through_the_gia_transfer(
    and_aig: Aig,
    fake_abc: Callable[[str], Path],
) -> None:
    """A `&`-space call must reach ABC through `&read`/`&write`.

    Against the classic store the command would silently see nothing.

    Args:
        and_aig: A minimal two-input AND network.
        fake_abc: Factory for the stand-in ABC executable.
    """
    shim = fake_abc(_FAILING)
    script = _command_for(lambda: gia.syn2(and_aig, delay_relaxation=0, binary=shim))

    assert f"; {gia.syn2.cmd(delay_relaxation=0)}; " in script
    # Not anchored to the start: a resource file registered via AIGVERSE_ABC_RC
    # prepends a `source` step to what ABC is actually asked to run.
    assert "&read in.aig" in script
    assert "read_aiger" not in script
    assert script.endswith("&write out.aig")
