"""Bridge to the external ABC logic synthesis system.

`aigverse` does not ship ABC. This module drives an ABC executable that is
already installed on the machine, transferring networks as binary AIGER files.
Point it at an executable with the ``AIGVERSE_ABC`` environment variable or
:func:`set_abc_binary`, or put ``abc`` on ``PATH``.

Importing this module always succeeds, whether or not ABC is installed. Use
:func:`is_available` to check, and expect :exc:`AbcNotFoundError` from any call
that needs the executable.

Example:
    >>> from aigverse import abc
    >>> from aigverse.generators import ripple_carry_adder
    >>> aig = ripple_carry_adder(4)
    >>> if abc.is_available():
    ...     optimized = abc.resyn2(aig)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._binary import (
    ABC_ENV_VAR,
    abc_binary,
    abc_version,
    find_abc_binary,
    is_available,
    set_abc_binary,
)
from ._errors import AbcError, AbcExecutionError, AbcNotFoundError, AbcTimeoutError
from ._runner import AigT, run_commands, run_script
from ._scripts import SCRIPTS, expand_script

if TYPE_CHECKING:
    import os

__all__ = [
    "ABC_ENV_VAR",
    "SCRIPTS",
    "AbcError",
    "AbcExecutionError",
    "AbcNotFoundError",
    "AbcTimeoutError",
    "abc_binary",
    "abc_version",
    "compress",
    "compress2",
    "compress2rs",
    "dc2",
    "expand_script",
    "find_abc_binary",
    "is_available",
    "resyn",
    "resyn2",
    "resyn2rs",
    "resyn3",
    "run_commands",
    "run_script",
    "set_abc_binary",
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

    Args:
        ntk: The combinational network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        TypeError: If ``ntk`` is a ``SequentialAig`` or not an ``Aig`` at all.
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
        AbcExecutionError: If ABC reported an error or produced no usable output.
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

    Args:
        ntk: The combinational network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        TypeError: If ``ntk`` is a ``SequentialAig`` or not an ``Aig`` at all.
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
        AbcExecutionError: If ABC reported an error or produced no usable output.
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

    Args:
        ntk: The combinational network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        TypeError: If ``ntk`` is a ``SequentialAig`` or not an ``Aig`` at all.
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
        AbcExecutionError: If ABC reported an error or produced no usable output.
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

    Like ``resyn``, but every command runs in level-preserving mode.

    The script is expanded into builtin ABC commands, so it does not depend on
    an ``abc.rc`` being present. See :data:`SCRIPTS` for the exact expansion.

    Args:
        ntk: The combinational network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        TypeError: If ``ntk`` is a ``SequentialAig`` or not an ``Aig`` at all.
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
        AbcExecutionError: If ABC reported an error or produced no usable output.
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

    Like ``resyn2``, but every command runs in level-preserving mode.

    The script is expanded into builtin ABC commands, so it does not depend on
    an ``abc.rc`` being present. See :data:`SCRIPTS` for the exact expansion.

    Args:
        ntk: The combinational network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        TypeError: If ``ntk`` is a ``SequentialAig`` or not an ``Aig`` at all.
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
        AbcExecutionError: If ABC reported an error or produced no usable output.
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

    Args:
        ntk: The combinational network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        TypeError: If ``ntk`` is a ``SequentialAig`` or not an ``Aig`` at all.
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
        AbcExecutionError: If ABC reported an error or produced no usable output.
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

    ``resyn2rs`` in level-preserving mode; the strongest of these scripts.

    The script is expanded into builtin ABC commands, so it does not depend on
    an ``abc.rc`` being present. See :data:`SCRIPTS` for the exact expansion.

    Args:
        ntk: The combinational network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        TypeError: If ``ntk`` is a ``SequentialAig`` or not an ``Aig`` at all.
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
        AbcExecutionError: If ABC reported an error or produced no usable output.
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

    Args:
        ntk: The combinational network to optimize.
        timeout: Seconds to wait for ABC to terminate, or ``None`` for no limit.
        verbose: If ``True``, print everything ABC wrote.
        binary: Overrides the resolved ABC executable for this call only.

    Returns:
        The optimized network, of the same type as ``ntk``.

    Raises:
        TypeError: If ``ntk`` is a ``SequentialAig`` or not an ``Aig`` at all.
        AbcNotFoundError: If no ABC executable could be located.
        AbcTimeoutError: If ABC did not terminate within ``timeout`` seconds.
        AbcExecutionError: If ABC reported an error or produced no usable output.
    """
    return run_script(ntk, expand_script("dc2"), timeout=timeout, verbose=verbose, binary=binary)
