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

from typing import TYPE_CHECKING

from ._runner import AigT, run_script

if TYPE_CHECKING:
    import os

__all__ = [
    "gia_balance",
    "gia_dc2",
    "gia_fraig",
    "gia_resub",
    "gia_syn2",
    "gia_syn3",
    "gia_syn4",
]


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
