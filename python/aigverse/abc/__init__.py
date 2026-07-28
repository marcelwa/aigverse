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

from ._binary import (
    ABC_ENV_VAR,
    abc_binary,
    abc_version,
    find_abc_binary,
    is_available,
    set_abc_binary,
)
from ._errors import AbcError, AbcExecutionError, AbcNotFoundError, AbcTimeoutError
from ._runner import run_commands, run_script
from ._scripts import SCRIPTS, expand_script
from ._wrappers import (
    compress,
    compress2,
    compress2rs,
    dc2,
    resyn,
    resyn2,
    resyn2rs,
    resyn3,
)

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
