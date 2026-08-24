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

from ._options import check_option
from ._runner import AigT, run_script

if TYPE_CHECKING:
    import os

__all__ = ["balance", "orchestrate", "refactor", "resub", "rewrite"]


def balance(
    ntk: AigT,
    *,
    minimize_levels: bool = True,
    exor: bool = False,
    duplicate: bool = False,
    duplicate_critical: bool = False,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``balance`` command on a network.

    Restructures the AND trees of the network to reduce its depth.

    Args:
        ntk: The network to optimize.
        minimize_levels: If ``True`` (ABC's default), balance for minimal depth.
        exor: If ``True``, balance multi-input EXOR structures as well.
        duplicate: If ``True``, allow logic to be duplicated.
        duplicate_critical: If ``True``, duplicate logic on the critical paths
            only, which buys depth for less area than ``duplicate`` does.
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
    if duplicate_critical:
        command += " -s"
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
        ntk: The network to optimize.
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
    min_saved: int | None = None,
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
        ntk: The network to optimize.
        max_support: Maximum support of a collapsed node (ABC's ``-N``, 1 to 15),
            or ``None`` for ABC's default of 10. Larger values are slower. ABC
            documents no range but rejects anything above 15.
        min_saved: Minimum number of nodes a single step must save to be applied
            (ABC's ``-M``, at least 0), or ``None`` for ABC's default of 1.
            Setting it to 0 accepts steps that save nothing.
        preserve_levels: If ``True`` (ABC's default), never increase the depth.
        zero_cost: If ``True``, also apply replacements that do not reduce the
            size, which perturbs the structure and can unlock later gains.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        ValueError: If ``max_support`` is outside the range ABC accepts.
    """
    command = "refactor"
    if max_support is not None:
        check_option("refactor", "N", max_support, name="max_support")
        command += f" -N {max_support}"
    if min_saved is not None:
        check_option("refactor", "M", min_saved, name="min_saved")
        command += f" -M {min_saved}"
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
    min_saved: int | None = None,
    odc_levels: int | None = None,
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
        ntk: The network to optimize.
        max_cut_size: Maximum cut size (ABC's ``-K``, 4 to 16), or ``None`` for
            ABC's default of 8. The canonical scripts sweep this from 6 to 12.
        max_inserts: Maximum number of nodes to add (ABC's ``-N``, 0 to 3), or
            ``None`` for ABC's default of 1.
        min_saved: Minimum number of nodes a single step must save to be applied
            (ABC's ``-M``, at least 0), or ``None`` for ABC's default of 1.
        odc_levels: Fanout levels used for observability-don't-care computation
            (ABC's ``-F``, at least 0), or ``None`` for ABC's default of 0, which
            disables it. Don't-cares find substitutions that are only valid in
            context, at the cost of a more expensive analysis.
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
        check_option("resub", "K", max_cut_size, name="max_cut_size")
        command += f" -K {max_cut_size}"
    if max_inserts is not None:
        check_option("resub", "N", max_inserts, name="max_inserts")
        command += f" -N {max_inserts}"
    if min_saved is not None:
        check_option("resub", "M", min_saved, name="min_saved")
        command += f" -M {min_saved}"
    if odc_levels is not None:
        check_option("resub", "F", odc_levels, name="odc_levels")
        command += f" -F {odc_levels}"
    if not preserve_levels:
        command += " -l"
    if zero_cost:
        command += " -z"
    return run_script(ntk, command, timeout=timeout, verbose=verbose, binary=binary)


def orchestrate(
    ntk: AigT,
    *,
    max_cut_size: int | None = None,
    max_inserts: int | None = None,
    odc_levels: int | None = None,
    preserve_levels: bool = True,
    zero_cost_rewrite: bool = True,
    zero_cost_refactor: bool = True,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``orchestrate`` command on a network.

    Interleaves rewriting, refactoring and resubstitution rather than running
    them one after another, choosing per node which of the three to apply. It is
    a single command doing the job of a whole schedule.

    Note that ABC enables zero-cost replacements here by default, unlike in the
    standalone :func:`rewrite` and :func:`refactor` commands.

    Args:
        ntk: The network to optimize.
        max_cut_size: Resubstitution cut size (ABC's ``-K``, 4 to 16), or ``None``
            for ABC's default of 8.
        max_inserts: Nodes resubstitution may add (ABC's ``-N``, 0 to 3), or
            ``None`` for ABC's default of 1.
        odc_levels: Fanout levels used for don't-care computation (ABC's ``-F``),
            or ``None`` for ABC's default of 0.
        preserve_levels: If ``True`` (ABC's default), never increase the depth.
        zero_cost_rewrite: If ``True`` (ABC's default here), let the rewriting
            part apply replacements that do not reduce the size.
        zero_cost_refactor: If ``True`` (ABC's default here), the same for the
            refactoring part.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        ValueError: If an option is outside the range ABC accepts.
    """
    command = "orchestrate"
    if max_cut_size is not None:
        check_option("orchestrate", "K", max_cut_size, name="max_cut_size")
        command += f" -K {max_cut_size}"
    if max_inserts is not None:
        check_option("orchestrate", "N", max_inserts, name="max_inserts")
        command += f" -N {max_inserts}"
    if odc_levels is not None:
        check_option("orchestrate", "F", odc_levels, name="odc_levels")
        command += f" -F {odc_levels}"
    # every one of these switches toggles a default of "on"
    if not preserve_levels:
        command += " -l"
    if not zero_cost_rewrite:
        command += " -z"
    if not zero_cost_refactor:
        command += " -Z"
    return run_script(ntk, command, timeout=timeout, verbose=verbose, binary=binary)
