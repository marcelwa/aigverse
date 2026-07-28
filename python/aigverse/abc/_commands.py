"""Wrappers for the individual ABC optimization commands.

The canonical scripts in :mod:`._wrappers` are sequences of these four commands.
Exposing them individually makes it possible to compose a schedule from Python --
for instance in a reinforcement-learning loop over synthesis actions -- without
assembling ABC command strings by hand.

Every one of these is an ABC builtin, so they work regardless of whether an
``abc.rc`` can be found.

A note on levels: ABC's ``-l`` switch *toggles* a default of "preserve the number
of levels", so passing it turns level preservation off. These wrappers expose the
resulting behaviour directly as ``preserve_levels`` rather than the switch, so
that ``preserve_levels=False`` reads as what it does.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._runner import AigT, run_script

if TYPE_CHECKING:
    import os

__all__ = ["balance", "refactor", "resub", "rewrite"]


def balance(
    ntk: AigT,
    *,
    minimize_levels: bool = True,
    exor: bool = False,
    duplicate: bool = False,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``balance`` command on a network.

    Restructures the AND trees of the network to reduce its depth.

    Args:
        ntk: The combinational network to optimize.
        minimize_levels: If ``True`` (ABC's default), balance for minimal depth.
        exor: If ``True``, balance multi-input EXOR structures as well.
        duplicate: If ``True``, allow logic to be duplicated.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    command = "balance"
    if not minimize_levels:
        command += " -l"
    if duplicate:
        command += " -d"
    if exor:
        command += " -x"
    return run_script(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def rewrite(
    ntk: AigT,
    *,
    preserve_levels: bool = True,
    zero_cost: bool = False,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``rewrite`` command on a network.

    Replaces 4-input subgraphs with smaller pre-computed equivalents.

    Args:
        ntk: The combinational network to optimize.
        preserve_levels: If ``True`` (ABC's default), never increase the depth.
        zero_cost: If ``True``, also apply replacements that do not reduce the
            size, which perturbs the structure and can unlock later gains.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    command = "rewrite"
    if not preserve_levels:
        command += " -l"
    if zero_cost:
        command += " -z"
    return run_script(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def refactor(
    ntk: AigT,
    *,
    max_support: int | None = None,
    preserve_levels: bool = True,
    zero_cost: bool = False,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``refactor`` command on a network.

    Collapses a cone into a single node and resynthesizes it from its truth
    table, which reaches larger cuts than :func:`rewrite` does.

    Args:
        ntk: The combinational network to optimize.
        max_support: Maximum support of a collapsed node (ABC's ``-N``), or
            ``None`` for ABC's default of 10. Larger values are slower.
        preserve_levels: If ``True`` (ABC's default), never increase the depth.
        zero_cost: If ``True``, also apply replacements that do not reduce the
            size, which perturbs the structure and can unlock later gains.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        ValueError: If ``max_support`` is not positive.
    """
    command = "refactor"
    if max_support is not None:
        if max_support < 1:
            msg = f"max_support must be positive, got {max_support}"
            raise ValueError(msg)
        command += f" -N {max_support}"
    if not preserve_levels:
        command += " -l"
    if zero_cost:
        command += " -z"
    return run_script(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def resub(
    ntk: AigT,
    *,
    max_cut_size: int | None = None,
    max_inserts: int | None = None,
    preserve_levels: bool = True,
    zero_cost: bool = False,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``resub`` command on a network.

    Re-expresses a node in terms of other nodes already present, which removes
    logic that rewriting and refactoring cannot reach because it is not local.

    Args:
        ntk: The combinational network to optimize.
        max_cut_size: Maximum cut size (ABC's ``-K``, 4 to 16), or ``None`` for
            ABC's default of 8. The canonical scripts sweep this from 6 to 12.
        max_inserts: Maximum number of nodes to add (ABC's ``-N``, 0 to 3), or
            ``None`` for ABC's default of 1.
        preserve_levels: If ``True`` (ABC's default), never increase the depth.
        zero_cost: If ``True``, also apply replacements that do not reduce the
            size, which perturbs the structure and can unlock later gains.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        ValueError: If ``max_cut_size`` or ``max_inserts`` is outside the range
            ABC accepts.
    """
    command = "resub"
    if max_cut_size is not None:
        if not 4 <= max_cut_size <= 16:
            msg = f"max_cut_size must be between 4 and 16, got {max_cut_size}"
            raise ValueError(msg)
        command += f" -K {max_cut_size}"
    if max_inserts is not None:
        if not 0 <= max_inserts <= 3:
            msg = f"max_inserts must be between 0 and 3, got {max_inserts}"
            raise ValueError(msg)
        command += f" -N {max_inserts}"
    if not preserve_levels:
        command += " -l"
    if zero_cost:
        command += " -z"
    return run_script(ntk, command, timeout=timeout, verbose=verbose, binary=binary)
