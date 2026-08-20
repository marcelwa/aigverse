"""The ABC9 (``&``-space) commands, run on ABC's GIA store.

ABC keeps two independent network stores and a command only ever sees its own.
The functions in :mod:`aigverse.abc` operate on the classic store; the ones here
operate on the GIA, and transfer the network with ``&read``/``&write`` rather
than ``read_aiger``/``write_aiger``.

They are reached through the ``gia`` namespace, which mirrors ABC's own ``&``
prefix::

    from aigverse import abc

    optimized = abc.gia.dc2(aig)  # ABC's `&dc2`
    optimized = abc.dc2(aig)  # ABC's `dc2`, a different command

The ``&``-space is **not** a mirror of the classic command set. There is no
``&rewrite`` and no ``&refactor``; ``&dc2`` is the heavy-rewriting equivalent, and
``&syn2``/``&syn3``/``&syn4`` are composite scripts rather than single commands.
What the ``&``-space adds is a genuinely different optimization strategy: these
commands map to LUTs internally and unmap again, which restructures far more
aggressively than the classic commands do.

These are aimed at depth rather than area, but whether they deliver is strongly
design-dependent and worth measuring rather than assuming. On a 4-bit ripple-carry
multiplier, ``&syn4`` trades 84 gates at 16 levels for 168 gates at 13 levels --
depth the classic scripts cannot reach on that design. On a 16-bit carry-lookahead
adder the same command buys nothing: it grows the network and leaves the depth
where it was, while ``resyn2`` beats it on both counts. Neither family dominates.

The ``&`` space is also stricter than the classic one about register reset
values. ``&read`` accepts only a reset of 0 literally: it converts a 1-valued
flip-flop by complementing it, which is an equivalent network that comes back
with a reset of 0, and it models an *undefined* reset with an extra primary
input, an extra register, and three AND nodes -- a network with a different
interface than it went in with. The first is carried, the second is refused with
a ``ValueError`` by every function here. The classic store keeps either reset
value as it is.
"""

from __future__ import annotations

import tempfile
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from ._errors import AbcExecutionError, AbcTimeoutError
from ._options import check_option
from ._runner import AigT, budgeted_timeout, check_gia_supported, check_supported, resolve_binary, run_commands
from ._runner import run_script as _base_run_script
from ._stats import AbcStats, collect_stats

if TYPE_CHECKING:
    import os
    from collections.abc import Sequence

    from ..networks import Aig

__all__ = [
    "CecStatus",
    "balance",
    "cec",
    "dc2",
    "deepsyn",
    "fraig",
    "resub",
    "run_script",
    "stats",
    "syn2",
    "syn3",
    "syn4",
    "transduction",
    "transtoch",
]

_CEC_LEFT = "left.aig"
_CEC_RIGHT = "right.aig"


class CecStatus(Enum):
    """The outcome of an equivalence check.

    Deliberately not usable as a boolean: ``if cec(a, b):`` would read as
    "equivalent" while quietly also firing for :attr:`UNDECIDED` and
    :attr:`TIMEOUT`, which are not the same claim at all. Compare explicitly::

        if abc.gia.cec(a, b) is abc.gia.CecStatus.EQUIVALENT:
            ...
    """

    #: ABC proved the two networks equivalent.
    EQUIVALENT = "equivalent"
    #: ABC found a counterexample; the two networks differ.
    NOT_EQUIVALENT = "not equivalent"
    #: ABC ran out of its own resource budget without deciding.
    UNDECIDED = "undecided"
    #: ABC did not finish within the requested ``timeout``.
    TIMEOUT = "timeout"

    def __bool__(self) -> bool:
        """Refuses truth testing.

        Raises:
            TypeError: Always. Compare against a member instead.
        """
        msg = (
            f"{type(self).__name__} must not be used as a boolean, because "
            f"'undecided' is not 'not equivalent'. Compare explicitly, e.g. "
            f"`result is {type(self).__name__}.EQUIVALENT`."
        )
        raise TypeError(msg)


def _run(
    ntk: AigT,
    command: str,
    *,
    timeout: float | None,
    verbose: bool,
    binary: str | os.PathLike[str] | None,
) -> AigT:
    """Runs a single ``&``-space command through the GIA transfer path.

    Args:
        ntk: The network to optimize.
        command: The assembled ABC command.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    return _base_run_script(ntk, command, timeout=timeout, gia=True, verbose=verbose, binary=binary)


def balance(
    ntk: AigT,
    *,
    delay_only: bool = False,
    and_only: bool = False,
    strict_area: bool = False,
    max_fanout: int | None = None,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``&b`` command on a network.

    The ``&``-space counterpart of :func:`~aigverse.abc.balance`. Unlike the
    classic command it understands XOR and MUX structures, so it can restructure
    where the classic one only re-associates AND trees.

    Args:
        ntk: The network to optimize.
        delay_only: If ``True``, balance for delay without regard to area.
        and_only: If ``True``, use only AND nodes instead of AND/XOR/MUX.
        strict_area: If ``True``, control area strictly while balancing for
            delay. Only has an effect together with ``delay_only``.
        max_fanout: Fanout count above which a divisor is skipped (ABC's ``-N``,
            at least 0), or ``None`` for ABC's default. Lowering it keeps the
            command away from high-fanout nodes.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        ValueError: If ``max_fanout`` is outside the range ABC accepts.
    """
    command = "&b"
    if max_fanout is not None:
        check_option("&b", "N", max_fanout, name="max_fanout")
        command += f" -N {max_fanout}"
    if delay_only:
        command += " -d"
    if and_only:
        command += " -a"
    if strict_area:
        command += " -s"
    return _run(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def resub(
    ntk: AigT,
    *,
    max_inserts: int | None = None,
    max_support: int | None = None,
    max_divisors: int | None = None,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``&resub`` command on a network.

    The ``&``-space counterpart of :func:`~aigverse.abc.resub`.

    Args:
        ntk: The network to optimize.
        max_inserts: Limit on the number of nodes added (ABC's ``-N``, at least
            0), or ``None`` for ABC's default.
        max_support: Limit on the support size (ABC's ``-S``, at least 1), or
            ``None`` for ABC's default.
        max_divisors: Limit on the divisor count (ABC's ``-D``, at least 1), or
            ``None`` for ABC's default.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        ValueError: If a limit is outside the range ABC accepts.
    """
    command = "&resub"
    for switch, value, name in (
        ("N", max_inserts, "max_inserts"),
        ("S", max_support, "max_support"),
        ("D", max_divisors, "max_divisors"),
    ):
        if value is None:
            continue
        check_option("&resub", switch, value, name=name)
        command += f" -{switch} {value}"
    return _run(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def dc2(
    ntk: AigT,
    *,
    update_levels: bool = True,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``&dc2`` command on a network.

    Heavy rewriting, and the closest ``&``-space equivalent of
    :func:`~aigverse.abc.rewrite` and :func:`~aigverse.abc.refactor` -- neither of
    which has a direct ``&`` counterpart.

    Args:
        ntk: The network to optimize.
        update_levels: If ``True`` (ABC's default), track levels while rewriting.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    command = "&dc2" if update_levels else "&dc2 -l"
    return _run(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def syn2(
    ntk: AigT,
    *,
    delay_relaxation: int | None = None,
    cut_minimization: bool = False,
    delay_optimization: bool = False,
    coarsen: bool = True,
    old_algorithm: bool = False,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``&syn2`` script on a network.

    The lightest of the three ``&`` synthesis scripts.

    .. warning::
        These scripts buy depth with area, and they spend it whether or not there
        is depth to be had. On a design where they find none, the AND count grows
        and nothing comes back for it -- a 16-bit carry-lookahead adder goes from
        186 gates to 698 under ``&syn2`` here. That is ABC behaving as designed,
        not a failure; compare the result before keeping it.

    Args:
        ntk: The network to optimize.
        delay_relaxation: Delay relaxation ratio (ABC's ``-R``, at least 0), or
            ``None`` for ABC's default of 20. Higher values allow more delay in
            exchange for area.
        cut_minimization: If ``True``, enable cut minimization.
        delay_optimization: If ``True``, run the additional delay optimization.
        coarsen: If ``True`` (ABC's default), coarsen the subject graph before
            mapping, which gives the mapper larger cuts to work with.
        old_algorithm: If ``True``, use ABC's previous implementation instead of
            the current one.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        ValueError: If ``delay_relaxation`` is outside the range ABC accepts.
    """
    command = "&syn2"
    if delay_relaxation is not None:
        check_option("&syn2", "R", delay_relaxation, name="delay_relaxation")
        command += f" -R {delay_relaxation}"
    if old_algorithm:
        command += " -a"
    if not coarsen:
        command += " -k"
    if cut_minimization:
        command += " -m"
    if delay_optimization:
        command += " -d"
    return _run(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def syn3(
    ntk: AigT,
    *,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``&syn3`` script on a network.

    A different restructuring schedule from :func:`syn2`; which of the two wins is
    design-dependent, so both are worth trying.

    .. warning::
        Like :func:`syn2`, this trades area for depth and will grow the network on
        designs where there is no depth to recover.

    Args:
        ntk: The network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    return _run(ntk, "&syn3", timeout=timeout, verbose=verbose, binary=binary)


def syn4(
    ntk: AigT,
    *,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``&syn4`` script on a network.

    The most aggressive of the three, and the one that spends the most area to
    buy depth.

    .. warning::
        Like :func:`syn2`, this trades area for depth, and it spends the most of
        the three. Expect the AND count to grow, sometimes considerably.

    Args:
        ntk: The network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    return _run(ntk, "&syn4", timeout=timeout, verbose=verbose, binary=binary)


def fraig(
    ntk: AigT,
    *,
    conflict_limit: int | None = None,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``&fraig`` command on a network.

    Combinational SAT sweeping: proves internal nodes functionally equivalent and
    merges them. This removes redundancy that no amount of structural rewriting
    can see, which makes it a good final pass -- and a good one to run *between*
    two structural scripts that each introduced their own duplicates.

    Args:
        ntk: The network to optimize.
        conflict_limit: Maximum SAT conflicts per node (ABC's ``-C``, at least 0),
            or ``None`` for ABC's default. Lower values bound the runtime on hard
            instances at the cost of missing some merges. It is the only one of
            ``&fraig``'s two dozen switches wrapped here; the rest tune the SAT
            sweeper internally and are reachable through :func:`run_script`.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        ValueError: If ``conflict_limit`` is outside the range ABC accepts.
    """
    command = "&fraig"
    if conflict_limit is not None:
        check_option("&fraig", "C", conflict_limit, name="conflict_limit")
        command += f" -C {conflict_limit}"
    return _run(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def deepsyn(
    ntk: AigT,
    *,
    timeout: float | None = None,
    iterations: int | None = None,
    patience: int | None = None,
    stop_at_nodes: int | None = None,
    seed: int | None = None,
    two_input_luts: bool = False,
    optimize: bool = False,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``&deepsyn`` command on a network.

    A search rather than a pass: it repeatedly restructures the network with
    randomized parameters and keeps whatever came out smallest. That makes it the
    strongest thing in this module and also the slowest, and it means two runs
    with different ``seed`` values can give different results.

    Give it a budget. Unlike the single-pass commands, ``timeout`` here is handed
    to ABC as its own internal limit, so ABC stops cleanly and returns the best
    result it has found rather than being killed with nothing to show.

    ABC's ``-c`` switch, which computes structural choices, is deliberately not
    exposed: it leaves an AIG *with choices* in the GIA store, which ``&write``
    cannot serialize -- ABC aborts on an internal assertion rather than reporting
    an error, so the result could never come back across the bridge.

    Args:
        ntk: The network to optimize.
        timeout: Seconds ABC may spend searching (ABC's ``-T``), or ``None`` for
            no limit. Strongly recommended.
        iterations: Number of search iterations (ABC's ``-I``, at least 1), or
            ``None`` for ABC's default of 1.
        patience: Number of steps without improvement after which the search
            gives up (ABC's ``-J``, at least 1), or ``None`` for ABC's default,
            which is effectively unlimited.
        stop_at_nodes: Stop once the network is this small (ABC's ``-A``), or
            ``None`` for no such limit.
        seed: Random seed (ABC's ``-S``, 0 to 100), or ``None`` for ABC's default.
        two_input_luts: If ``True``, search over two-input LUTs.
        optimize: If ``True``, enable ABC's additional optimization step.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        ValueError: If an option is outside the range ABC accepts.
    """
    command = "&deepsyn"
    # switches in ABC's own order, with the budget handed over as `-T` so that
    # ABC stops on its own terms and keeps the best result it has found
    for switch, value, name in (
        ("I", iterations, "iterations"),
        ("J", patience, "patience"),
        ("T", None if timeout is None else int(timeout), "timeout"),
        ("A", stop_at_nodes, "stop_at_nodes"),
        ("S", seed, "seed"),
    ):
        if value is None:
            continue
        check_option("&deepsyn", switch, value, name=name)
        command += f" -{switch} {value}"
    if two_input_luts:
        command += " -t"
    if optimize:
        command += " -o"
    return _run(ntk, command, timeout=budgeted_timeout(timeout), verbose=verbose, binary=binary)


def transduction(
    ntk: AigT,
    *,
    transduction_type: int | None = None,
    fanin_sort: int | None = None,
    script_parameters: int | None = None,
    seed: int | None = None,
    randomize_seed: int | None = None,
    truth_tables: bool = False,
    mspf: bool = False,
    preserve_levels: bool = False,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``&transduction`` command on a network.

    Transduction reasons about permissible functions node by node, so it finds
    redundancy that structural rewriting cannot. It is BDD-based and its cost
    grows steeply with the network, so it is realistically limited to small
    designs -- treat a few thousand AND nodes as the upper end and pass a
    ``timeout``.

    ABC offers no internal budget for this command, so ``timeout`` kills the
    process and yields nothing.

    Contributed to ABC by Yukio Miyasaka.

    Args:
        ntk: The network to optimize.
        transduction_type: Which variant to run (ABC's ``-T``, 0 to 8), or
            ``None`` for ABC's default of 1 (``Resub``). Types 6 to 8 are the
            repeat scripts and are considerably more expensive.
        fanin_sort: Order in which fanins are visited (ABC's ``-S``, 0 to 4), or
            ``None`` for ABC's default of 0 (topological). The order decides which
            of several valid reductions is found first.
        script_parameters: Parameters for the repeat scripts (ABC's ``-P``, at
            least 0), or ``None`` for ABC's default of 0. Only meaningful for
            ``transduction_type`` 6 to 8.
        seed: Seed used to shuffle the inputs (ABC's ``-I``), or ``None`` not to
            shuffle. Different seeds explore different results.
        randomize_seed: Seed from which *all* parameters are drawn at random
            (ABC's ``-R``), or ``None`` to use the parameters as given. Setting it
            overrides the individual choices above.
        truth_tables: If ``True``, reason with truth tables instead of BDDs, which
            is faster on small functions and infeasible on wide ones.
        mspf: If ``True``, use maximum set of permissible functions instead of
            compatible ones. Stronger and more expensive.
        preserve_levels: If ``True``, do not increase the depth. ABC's default
            here is ``False``, unlike the classic commands.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        ValueError: If an option is outside the range ABC accepts.
    """
    # -V 0 silences the progress report, which is on by default and would
    # otherwise be mistaken for something having gone wrong.
    command = "&transduction -V 0"
    if transduction_type is not None:
        check_option("&transduction", "T", transduction_type, name="transduction_type")
        command += f" -T {transduction_type}"
    for switch, value, name in (
        ("S", fanin_sort, "fanin_sort"),
        ("I", seed, "seed"),
        ("P", script_parameters, "script_parameters"),
        ("R", randomize_seed, "randomize_seed"),
    ):
        if value is None:
            continue
        check_option("&transduction", switch, value, name=name)
        command += f" -{switch} {value}"
    if truth_tables:
        command += " -t"
    if mspf:
        command += " -m"
    if preserve_levels:
        command += " -l"
    return _run(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def transtoch(
    ntk: AigT,
    *,
    restarts: int | None = None,
    hops: int | None = None,
    seed: int | None = None,
    threads: int | None = None,
    mspf: bool = True,
    resub_shared: bool = True,
    reset_hops_on_improvement: bool = True,
    drf_hop: bool = False,
    drf_iterate: bool = False,
    truth_tables: bool = False,
    start_from_smallest: bool = False,
    start_from_given: bool = False,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``&transtoch`` command on a network.

    Stochastic transduction: it runs :func:`transduction` repeatedly with
    randomized parameters and keeps the best result. The most expensive command
    in this module by a wide margin, and only practical on genuinely small
    designs. Always pass a ``timeout``.

    ABC offers no internal budget for this command either, so ``timeout`` kills
    the process and yields nothing. Bound the work with ``restarts`` as well.

    Contributed to ABC by Yukio Miyasaka.

    Args:
        ntk: The network to optimize.
        restarts: Number of restarts (ABC's ``-N``), or ``None`` for ABC's
            default. Each restart costs a full transduction run.
        hops: Perturbation steps between restarts (ABC's ``-M``), or ``None`` for
            ABC's default of 10.
        seed: Random seed (ABC's ``-R``), or ``None`` for ABC's default.
        threads: Worker threads (ABC's ``-P``, at least 1), or ``None`` for ABC's
            default of 1.
        mspf: If ``True`` (ABC's default here), use maximum sets of permissible
            functions rather than compatible ones.
        resub_shared: If ``True`` (ABC's default here), use the ``ResubShared``
            transduction variant.
        reset_hops_on_improvement: If ``True`` (ABC's default here), reset the hop
            counter whenever a new minimum is found, so a productive direction is
            followed further.
        drf_hop: If ``True``, perturb with ``drf -z`` instead of
            ``if; mfs2; strash``.
        drf_iterate: If ``True``, iterate with ``drf -z`` instead of ``&dc2``.
        truth_tables: If ``True``, reason with truth tables instead of BDDs.
        start_from_smallest: If ``True``, restart from the smallest network found
            so far rather than from the last one.
        start_from_given: If ``True``, restart from the network as given rather
            than from an intermediate result.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        ValueError: If an option is outside the range ABC accepts.
    """
    command = "&transtoch -V 0"
    for switch, value, name in (
        ("N", restarts, "restarts"),
        ("M", hops, "hops"),
        ("R", seed, "seed"),
        ("P", threads, "threads"),
    ):
        if value is None:
            continue
        check_option("&transtoch", switch, value, name=name)
        command += f" -{switch} {value}"
    # the first three toggle a default of "on"
    for switch, enabled in (
        ("m", not mspf),
        ("g", not resub_shared),
        ("r", not reset_hops_on_improvement),
        ("z", drf_hop),
        ("f", drf_iterate),
        ("t", truth_tables),
        ("s", start_from_smallest),
        ("o", start_from_given),
    ):
        if enabled:
            command += f" -{switch}"
    return _run(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def cec(
    ntk: Aig,
    other: Aig,
    *,
    conflict_limit: int | None = None,
    timeout: float | None = None,
    binary: str | os.PathLike[str] | None = None,
) -> CecStatus:
    """Checks two networks for combinational equivalence with ABC's ``&cec``.

    Unlike everything else in this module this returns a verdict rather than a
    network. It is an independent second opinion on
    :func:`~aigverse.algorithms.equivalence_checking`, which is useful precisely
    because it is a different implementation -- if the two ever disagree, one of
    them has a bug worth finding.

    ``&cec`` is incomplete under a resource limit, so there are four outcomes and
    not two. "Not proven equal" and "proven different" are very different answers,
    which is why this returns a :class:`CecStatus` rather than a ``bool`` and why
    that enum refuses to be truth-tested.

    ``timeout`` is handed to ABC as its own limit, so an exhausted budget comes
    back as :attr:`CecStatus.TIMEOUT` rather than as an exception.

    Args:
        ntk: The first network.
        other: The second network. It must have the same numbers of inputs and
            outputs; ``&cec`` matches them by position, not by name.
        conflict_limit: Maximum SAT conflicts per node (ABC's ``-C``, at least 0),
            or ``None`` for ABC's default of 1000. ``&cec``'s remaining switches
            select solvers and miter encodings rather than changing the verdict,
            and are reachable through :func:`~aigverse.abc.run_commands`.
        timeout: Seconds ABC may spend (ABC's ``-T``), or ``None`` for no limit.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The outcome of the check.

    Raises:
        TypeError: If either argument is not an ``Aig``.
        ValueError: If an option is outside the range ABC accepts, or if either
            argument has a register whose reset value is undefined.
        AbcNotFoundError: If no ABC executable could be located.
        AbcExecutionError: If ABC failed outright.
    """
    check_supported(ntk)
    check_supported(other)
    check_gia_supported(ntk)
    check_gia_supported(other)

    command = "&cec"
    if conflict_limit is not None:
        check_option("&cec", "C", conflict_limit, name="conflict_limit")
        command += f" -C {conflict_limit}"
    if timeout is not None:
        check_option("&cec", "T", int(timeout), name="timeout")
        command += f" -T {int(timeout)}"

    executable = resolve_binary(binary)

    from ..io import write_aiger

    with tempfile.TemporaryDirectory(prefix="aigverse-abc-") as tmpdir:
        directory = Path(tmpdir)
        write_aiger(ntk, directory / _CEC_LEFT)
        write_aiger(other, directory / _CEC_RIGHT)

        script = f"&read {_CEC_LEFT}; {command} {_CEC_RIGHT}"
        try:
            output = run_commands(
                script,
                timeout=budgeted_timeout(timeout),
                cwd=directory,
                binary=executable,
            )
        except AbcTimeoutError:
            return CecStatus.TIMEOUT

    lowered = output.lower()
    # order matters: "not equivalent" also contains "equivalent"
    if "networks are not equivalent" in lowered:
        return CecStatus.NOT_EQUIVALENT
    if "networks are equivalent" in lowered:
        return CecStatus.EQUIVALENT
    if "undecided" in lowered or "timeout" in lowered:
        return CecStatus.UNDECIDED

    msg = "ABC did not report a verdict for the equivalence check"
    raise AbcExecutionError(msg, binary=str(executable), command=script, output=output)


def stats(
    ntk: Aig,
    *,
    timeout: float | None = None,
    binary: str | os.PathLike[str] | None = None,
) -> AbcStats:
    """Reports ABC's ``&ps`` for a network.

    The GIA store's own view. It agrees with :func:`~aigverse.abc.stats` on the
    counts and adds an average level and a memory figure.

    .. warning::
        ABC structurally hashes a network as it reads it, so these counts describe
        the network *ABC* ended up with, which can be smaller than the one that
        was handed over. See :func:`~aigverse.abc.stats` for the details.

    Args:
        ntk: The network to measure.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        What ABC reports about the network.

    Raises:
        TypeError: If ``ntk`` is not an ``Aig``.
        ValueError: If ``ntk`` has a register whose reset value is undefined.
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
        AbcExecutionError: If ABC reported an error or printed nothing usable.
    """
    # -x suppresses the colour codes; the parser strips them anyway, but this
    # keeps `raw` readable for anyone printing it.
    return collect_stats(ntk, "&read", "&ps -x", timeout=timeout, binary=binary)


def run_script(
    ntk: AigT,
    commands: str | Sequence[str],
    *,
    timeout: float | None = None,
    use_init_file: bool = False,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs arbitrary ``&``-space commands on a network.

    The GIA counterpart of :func:`~aigverse.abc.run_script`: the network is
    transferred with ``&read``/``&write`` so that ``&``-prefixed commands operate
    on it directly. Equivalent to calling that function with ``gia=True``.

    Args:
        ntk: The network to optimize.
        commands: A single ``;``-separated ABC command string, or a sequence of
            individual commands.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        use_init_file: If ``False`` (default), ABC is invoked with ``-s`` so that
            no ``abc.rc`` is read.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        TypeError: If ``ntk`` is not an ``Aig``.
        ValueError: If no command was given, or if ``ntk`` has a register whose
            reset value is undefined.
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
        AbcExecutionError: If ABC reported an error or produced no usable output.
    """
    return _base_run_script(
        ntk,
        commands,
        timeout=timeout,
        use_init_file=use_init_file,
        gia=True,
        verbose=verbose,
        binary=binary,
    )
