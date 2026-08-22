"""scikit-build ``dynamic-metadata`` provider for the nanobind backend dependency.

The backend is only needed by extensions built in nanobind's *split mode*, and
which mode a wheel uses depends on the interpreter it is built for. Declaring
``nanobind-backend`` statically would make the free-threaded wheels
uninstallable, because no ``nanobind-backend`` wheel is published for
``cp313t``/``cp314t`` and the project has no sdist to fall back on.

Wired up in ``pyproject.toml`` as::

    [[tool.dynamic-metadata]]
    provider = { path = "tools", module = "aigverse_dynamic_deps" }

Keep the mode check below in step with the one in
``cmake/AddAigversePythonBinding.cmake`` -- they decide the same thing about the
same interpreter, one for the metadata and one for the build.
"""

from __future__ import annotations

import sys
import sysconfig
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ["dynamic_metadata", "dynamic_wheel"]

#: No upper bound and never pinned: newer backends serve older extensions, and
#: two projects pinning different versions could not be installed together.
BACKEND_REQUIREMENT = "nanobind-backend>=1.0"


def __dir__() -> list[str]:
    return __all__


def _uses_split_mode() -> bool:
    """Report whether this interpreter's extensions are built in split mode.

    Split mode targets a stable ABI, which free-threaded interpreters only have
    from Python 3.15 on (the ``abi3t`` of PEP 803). Below that they are built in
    linked mode, which carries its own copy of the nanobind library and needs no
    backend at runtime.

    Returns:
        True if the extensions resolve a backend at import time.
    """
    free_threaded = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
    return not (free_threaded and sys.version_info < (3, 15))


def dynamic_metadata(
    settings: Mapping[str, Any],
    project: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the ``dependencies`` field for a dynamic-metadata consumer.

    Args:
        settings: Extra keys from the ``[[tool.dynamic-metadata]]`` table.
        project: The static ``[project]`` table read from ``pyproject.toml``.

    Returns:
        A mapping holding the resolved ``dependencies`` list.
    """
    del settings
    dependencies = list(project.get("dependencies", []))
    if _uses_split_mode():
        dependencies.append(BACKEND_REQUIREMENT)
    return {"dependencies": dependencies}


def dynamic_wheel(settings: Mapping[str, Any]) -> dict[str, bool]:
    """Mark ``dependencies`` as varying between the sdist and a built wheel.

    Args:
        settings: Extra keys from the ``[[tool.dynamic-metadata]]`` table.

    Returns:
        A mapping marking ``dependencies`` as wheel-dependent.
    """
    del settings
    return {"dependencies": True}
