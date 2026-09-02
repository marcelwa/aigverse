"""Convenience wrappers for the canonical ABC optimization scripts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._runner import AigT, run_script
from ._scripts import expand_script

if TYPE_CHECKING:
    import os

__all__ = [
    "compress",
    "compress2",
    "compress2rs",
    "dc2",
    "resyn",
    "resyn2",
    "resyn2rs",
    "resyn3",
]


def resyn(
    ntk: AigT,
    *,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``resyn`` script on a network.

    A short balance/rewrite loop; the lightest of the standard scripts.

    The script is expanded into builtin ABC commands, so it does not depend on
    an ``abc.rc`` being present. See :data:`SCRIPTS` for the exact expansion.
    Errors are reported the same way as by :func:`run_script`.

    Args:
        ntk: The network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    return run_script(ntk, expand_script("resyn"), timeout=timeout, verbose=verbose, binary=binary)


def resyn2(
    ntk: AigT,
    *,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``resyn2`` script on a network.

    The most widely used ABC size-reduction script.

    The script is expanded into builtin ABC commands, so it does not depend on
    an ``abc.rc`` being present. See :data:`SCRIPTS` for the exact expansion.
    Errors are reported the same way as by :func:`run_script`.

    Args:
        ntk: The network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    return run_script(ntk, expand_script("resyn2"), timeout=timeout, verbose=verbose, binary=binary)


def resyn3(
    ntk: AigT,
    *,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``resyn3`` script on a network.

    A resubstitution-driven variant of ``resyn``.

    The script is expanded into builtin ABC commands, so it does not depend on
    an ``abc.rc`` being present. See :data:`SCRIPTS` for the exact expansion.
    Errors are reported the same way as by :func:`run_script`.

    Args:
        ntk: The network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    return run_script(ntk, expand_script("resyn3"), timeout=timeout, verbose=verbose, binary=binary)


def compress(
    ntk: AigT,
    *,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``compress`` script on a network.

    Like ``resyn``, but every command is given ``-l``, which turns ABC's default
    level preservation *off* and lets it trade depth for size.

    The script is expanded into builtin ABC commands, so it does not depend on
    an ``abc.rc`` being present. See :data:`SCRIPTS` for the exact expansion.
    Errors are reported the same way as by :func:`run_script`.

    Args:
        ntk: The network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    return run_script(ntk, expand_script("compress"), timeout=timeout, verbose=verbose, binary=binary)


def compress2(
    ntk: AigT,
    *,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``compress2`` script on a network.

    Like ``resyn2``, but every command is given ``-l``, which turns ABC's default
    level preservation *off* and lets it trade depth for size.

    The script is expanded into builtin ABC commands, so it does not depend on
    an ``abc.rc`` being present. See :data:`SCRIPTS` for the exact expansion.
    Errors are reported the same way as by :func:`run_script`.

    Args:
        ntk: The network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    return run_script(ntk, expand_script("compress2"), timeout=timeout, verbose=verbose, binary=binary)


def resyn2rs(
    ntk: AigT,
    *,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``resyn2rs`` script on a network.

    ``resyn2`` extended with resubstitution passes; slower and usually smaller.

    The script is expanded into builtin ABC commands, so it does not depend on
    an ``abc.rc`` being present. See :data:`SCRIPTS` for the exact expansion.
    Errors are reported the same way as by :func:`run_script`.

    Args:
        ntk: The network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    return run_script(ntk, expand_script("resyn2rs"), timeout=timeout, verbose=verbose, binary=binary)


def compress2rs(
    ntk: AigT,
    *,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``compress2rs`` script on a network.

    ``resyn2rs`` with level preservation turned off; the strongest of these
    scripts, and the slowest.

    The script is expanded into builtin ABC commands, so it does not depend on
    an ``abc.rc`` being present. See :data:`SCRIPTS` for the exact expansion.
    Errors are reported the same way as by :func:`run_script`.

    Args:
        ntk: The network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    return run_script(ntk, expand_script("compress2rs"), timeout=timeout, verbose=verbose, binary=binary)


def dc2(
    ntk: AigT,
    *,
    timeout: float | None = None,
    verbose: bool = False,
    binary: str | os.PathLike[str] | None = None,
) -> AigT:
    """Runs ABC's ``dc2`` script on a network.

    ABC's builtin combinational don't-care-based optimization.

    The script is expanded into builtin ABC commands, so it does not depend on
    an ``abc.rc`` being present. See :data:`SCRIPTS` for the exact expansion.
    Errors are reported the same way as by :func:`run_script`.

    Args:
        ntk: The network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.
    """
    return run_script(ntk, expand_script("dc2"), timeout=timeout, verbose=verbose, binary=binary)
