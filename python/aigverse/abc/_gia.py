"""Wrappers for the ABC9 (``&``-space) optimization commands.

These run on ABC's GIA store rather than its classic one, so they are transferred
with ``&read``/``&write`` -- see the ``gia`` flag of
:func:`~aigverse.abc.run_script`, which these are thin wrappers around.

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
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from ._errors import AbcExecutionError
from ._runner import AigT, check_supported, resolve_binary, run_commands, run_script

if TYPE_CHECKING:
    import os

    from ..networks import Aig

__all__ = [
    "gia_balance",
    "gia_cec",
    "gia_dc2",
    "gia_deepsyn",
    "gia_fraig",
    "gia_resub",
    "gia_syn2",
    "gia_syn3",
    "gia_syn4",
    "gia_transduction",
    "gia_transtoch",
]

_CEC_LEFT = "left.aig"
_CEC_RIGHT = "right.aig"


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
        ntk: The combinational network to optimize.
        command: The assembled ABC command.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    return run_script(ntk, command, timeout=timeout, gia=True, verbose=verbose, binary=binary)


def gia_balance(
    ntk: AigT,
    *,
    delay_only: bool = False,
    and_only: bool = False,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``&b`` command on a network.

    The ``&``-space counterpart of :func:`~aigverse.abc.balance`. Unlike the
    classic command it understands XOR and MUX structures, so it can restructure
    where the classic one only re-associates AND trees.

    Args:
        ntk: The combinational network to optimize.
        delay_only: If ``True``, balance for delay without regard to area.
        and_only: If ``True``, use only AND nodes instead of AND/XOR/MUX.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    command = "&b"
    if delay_only:
        command += " -d"
    if and_only:
        command += " -a"
    return _run(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def gia_resub(
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
        ntk: The combinational network to optimize.
        max_inserts: Limit on the number of nodes added (ABC's ``-N``), or
            ``None`` for ABC's default.
        max_support: Limit on the support size (ABC's ``-S``), or ``None`` for
            ABC's default.
        max_divisors: Limit on the divisor count (ABC's ``-D``), or ``None`` for
            ABC's default.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        ValueError: If any limit is negative.
    """
    command = "&resub"
    for switch, value in (("N", max_inserts), ("S", max_support), ("D", max_divisors)):
        if value is None:
            continue
        if value < 0:
            msg = f"the -{switch} limit must not be negative, got {value}"
            raise ValueError(msg)
        command += f" -{switch} {value}"
    return _run(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def gia_dc2(
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
        ntk: The combinational network to optimize.
        update_levels: If ``True`` (ABC's default), track levels while rewriting.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    command = "&dc2" if update_levels else "&dc2 -l"
    return _run(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def gia_syn2(
    ntk: AigT,
    *,
    delay_relaxation: int | None = None,
    cut_minimization: bool = False,
    delay_optimization: bool = False,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``&syn2`` script on a network.

    The lightest of the three ``&`` synthesis scripts. These aim at depth and
    usually grow the AND count doing so; on designs where they find no depth to
    remove, that growth is all you get.

    Args:
        ntk: The combinational network to optimize.
        delay_relaxation: Delay relaxation ratio (ABC's ``-R``), or ``None`` for
            ABC's default of 20. Higher values allow more delay in exchange for
            area.
        cut_minimization: If ``True``, enable cut minimization.
        delay_optimization: If ``True``, run the additional delay optimization.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        ValueError: If ``delay_relaxation`` is negative.
    """
    command = "&syn2"
    if delay_relaxation is not None:
        if delay_relaxation < 0:
            msg = f"delay_relaxation must not be negative, got {delay_relaxation}"
            raise ValueError(msg)
        command += f" -R {delay_relaxation}"
    if cut_minimization:
        command += " -m"
    if delay_optimization:
        command += " -d"
    return _run(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def gia_syn3(
    ntk: AigT,
    *,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``&syn3`` script on a network.

    A different restructuring schedule from :func:`gia_syn2`; which of the two
    wins is design-dependent, so both are worth trying.

    Args:
        ntk: The combinational network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    return _run(ntk, "&syn3", timeout=timeout, verbose=verbose, binary=binary)


def gia_syn4(
    ntk: AigT,
    *,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``&syn4`` script on a network.

    The most aggressive of the three, and the one that spends the most area to
    buy depth.

    Args:
        ntk: The combinational network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    return _run(ntk, "&syn4", timeout=timeout, verbose=verbose, binary=binary)


def gia_fraig(
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
        ntk: The combinational network to optimize.
        conflict_limit: Maximum SAT conflicts per node (ABC's ``-C``), or ``None``
            for ABC's default. Lower values bound the runtime on hard instances at
            the cost of missing some merges.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        ValueError: If ``conflict_limit`` is negative.
    """
    command = "&fraig"
    if conflict_limit is not None:
        if conflict_limit < 0:
            msg = f"conflict_limit must not be negative, got {conflict_limit}"
            raise ValueError(msg)
        command += f" -C {conflict_limit}"
    return _run(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def gia_deepsyn(
    ntk: AigT,
    *,
    iterations: int | None = None,
    timeout_seconds: int | None = None,
    stop_at_nodes: int | None = None,
    seed: int | None = None,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``&deepsyn`` command on a network.

    A search rather than a pass: it repeatedly restructures the network with
    randomized parameters and keeps whatever came out smallest. That makes it the
    strongest thing in this module and also the slowest, and it means two runs
    with different ``seed`` values give different results.

    Give it a budget. ``timeout_seconds`` is ABC's own internal limit, which lets
    it stop cleanly and return its best result so far; ``timeout`` kills the
    process and yields nothing, so keep it comfortably larger.

    Args:
        ntk: The combinational network to optimize.
        iterations: Number of search iterations (ABC's ``-I``), or ``None`` for
            ABC's default of 1.
        timeout_seconds: ABC's internal budget in seconds (ABC's ``-T``), or
            ``None`` for no limit. Strongly recommended.
        stop_at_nodes: Stop once the network is this small (ABC's ``-A``), or
            ``None`` for no such limit.
        seed: Random seed, 0 to 100 (ABC's ``-S``), or ``None`` for ABC's default.
        timeout: Seconds to wait for the ABC *process*, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        ValueError: If an option is outside the range ABC accepts.
    """
    command = "&deepsyn"
    for switch, value, low in (("I", iterations, 1), ("T", timeout_seconds, 0), ("A", stop_at_nodes, 0)):
        if value is None:
            continue
        if value < low:
            msg = f"the -{switch} value must be at least {low}, got {value}"
            raise ValueError(msg)
        command += f" -{switch} {value}"
    if seed is not None:
        if not 0 <= seed <= 100:
            msg = f"seed must be between 0 and 100, got {seed}"
            raise ValueError(msg)
        command += f" -S {seed}"
    return _run(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def gia_transduction(
    ntk: AigT,
    *,
    transduction_type: int | None = None,
    seed: int | None = None,
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

    Contributed to ABC by Yukio Miyasaka.

    Args:
        ntk: The combinational network to optimize.
        transduction_type: Which variant to run (ABC's ``-T``, 0 to 8), or
            ``None`` for ABC's default of 1 (``Resub``). Types 6 to 8 are the
            repeat scripts and are considerably more expensive.
        seed: Seed used to shuffle the inputs (ABC's ``-I``), or ``None`` not to
            shuffle. Different seeds explore different results.
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
        if not 0 <= transduction_type <= 8:
            msg = f"transduction_type must be between 0 and 8, got {transduction_type}"
            raise ValueError(msg)
        command += f" -T {transduction_type}"
    if seed is not None:
        if seed < 0:
            msg = f"seed must not be negative, got {seed}"
            raise ValueError(msg)
        command += f" -I {seed}"
    return _run(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def gia_transtoch(
    ntk: AigT,
    *,
    restarts: int | None = None,
    hops: int | None = None,
    seed: int | None = None,
    threads: int | None = None,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``&transtoch`` command on a network.

    Stochastic transduction: it runs :func:`gia_transduction` repeatedly with
    randomized parameters and keeps the best result. The most expensive command
    in this module by a wide margin, and only practical on genuinely small
    designs. Always pass a ``timeout``.

    Contributed to ABC by Yukio Miyasaka.

    Args:
        ntk: The combinational network to optimize.
        restarts: Number of restarts (ABC's ``-N``), or ``None`` for ABC's
            default. Each restart costs a full transduction run.
        hops: Perturbation steps between restarts (ABC's ``-M``), or ``None`` for
            ABC's default of 10.
        seed: Random seed (ABC's ``-R``), or ``None`` for ABC's default.
        threads: Worker threads (ABC's ``-P``), or ``None`` for ABC's default of 1.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        ValueError: If an option is negative, or ``threads`` is below one.
    """
    command = "&transtoch -V 0"
    for switch, value in (("N", restarts), ("M", hops), ("R", seed)):
        if value is None:
            continue
        if value < 0:
            msg = f"the -{switch} value must not be negative, got {value}"
            raise ValueError(msg)
        command += f" -{switch} {value}"
    if threads is not None:
        if threads < 1:
            msg = f"threads must be at least 1, got {threads}"
            raise ValueError(msg)
        command += f" -P {threads}"
    return _run(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def gia_cec(
    ntk: Aig,
    other: Aig,
    *,
    conflict_limit: int | None = None,
    effort_seconds: int | None = None,
    timeout: float | None = None,
    binary: str | os.PathLike[str] | None = None,
) -> bool:
    """Checks two networks for combinational equivalence with ABC's ``&cec``.

    Unlike everything else in this module this returns a verdict rather than a
    network. It is an independent second opinion on
    :func:`~aigverse.algorithms.equivalence_checking`, which is useful precisely
    because it is a different implementation -- if the two ever disagree, one of
    them has a bug worth finding.

    ``&cec`` is incomplete under a resource limit: it can return without deciding.
    That is reported as an exception rather than as ``False``, since "not proven
    equal" and "proven different" are very different answers.

    Args:
        ntk: The first network.
        other: The second network. It must have the same numbers of inputs and
            outputs; ABC matches them by position, not by name.
        conflict_limit: Maximum SAT conflicts per node (ABC's ``-C``), or ``None``
            for ABC's default of 1000.
        effort_seconds: Approximate runtime budget in seconds (ABC's ``-T``), or
            ``None`` for no limit. A budget makes an undecided answer more likely.
        timeout: Seconds to wait for the ABC *process*, or ``None`` for no limit.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        ``True`` if the two networks are equivalent, ``False`` if ABC found a
        counterexample.

    Raises:
        TypeError: If either argument is a ``SequentialAig`` or not an ``Aig``.
        ValueError: If an option is negative.
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
        AbcExecutionError: If ABC failed, or finished without deciding.
    """
    check_supported(ntk)
    check_supported(other)

    command = "&cec"
    for switch, value in (("C", conflict_limit), ("T", effort_seconds)):
        if value is None:
            continue
        if value < 0:
            msg = f"the -{switch} value must not be negative, got {value}"
            raise ValueError(msg)
        command += f" -{switch} {value}"

    executable = resolve_binary(binary)

    from ..io import write_aiger

    with tempfile.TemporaryDirectory(prefix="aigverse-abc-") as tmpdir:
        directory = Path(tmpdir)
        write_aiger(ntk, directory / _CEC_LEFT)
        write_aiger(other, directory / _CEC_RIGHT)

        script = f"&read {_CEC_LEFT}; {command} {_CEC_RIGHT}"
        output = run_commands(script, timeout=timeout, cwd=directory, binary=executable)

    lowered = output.lower()
    # order matters: "not equivalent" also contains "equivalent"
    if "networks are not equivalent" in lowered:
        return False
    if "networks are equivalent" in lowered:
        return True

    msg = "ABC did not decide the equivalence check"
    raise AbcExecutionError(msg, binary=str(executable), command=script, output=output)
