from __future__ import annotations

import subprocess
import sys
import sysconfig

import pytest


@pytest.mark.skipif(not sysconfig.get_config_var("Py_GIL_DISABLED"), reason="Requires a free-threaded interpreter")
def test_extension_imports_keep_gil_disabled() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-E",
            "-c",
            (
                "import importlib, sys; "
                "assert not sys._is_gil_enabled(); "
                "[importlib.import_module('aigverse.' + name) "
                "for name in ('networks', 'algorithms', 'io', 'generators', 'utils')]; "
                "assert not sys._is_gil_enabled()"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_root_has_no_top_level_aig_export() -> None:
    import aigverse

    assert not hasattr(aigverse, "Aig")


def test_modular_imports_are_available() -> None:
    import aigverse
    from aigverse.networks import Aig

    aig = Aig()
    assert isinstance(aig, Aig)

    assert hasattr(aigverse, "algorithms")
    assert hasattr(aigverse, "generators")
    assert hasattr(aigverse, "io")
    assert hasattr(aigverse, "networks")
    assert hasattr(aigverse, "utils")


def test_lazy_submodule_loading() -> None:
    # Verify the lazy-loading contract: accessing a submodule that is not in
    # the package __dict__ triggers __getattr__, which calls import_module and
    # caches the result in the package globals.
    #
    # We only remove from aigverse.__dict__ (not sys.modules) so that
    # import_module returns the already-loaded C extension without
    # re-initializing it (which would cause nanobind "already registered"
    # warnings).
    import aigverse

    name = "utils"
    fqn = f"aigverse.{name}"

    # Remove from package globals to force the __getattr__ path.
    had_saved = name in aigverse.__dict__
    saved = aigverse.__dict__.pop(name, None)

    try:
        assert name not in aigverse.__dict__

        # Trigger lazy loading via attribute access (__getattr__).
        mod = aigverse.utils

        # Postconditions: the module is cached in globals and functional.
        assert name in aigverse.__dict__
        assert aigverse.__dict__[name] is mod
        assert fqn in sys.modules
        assert hasattr(mod, "TruthTable")
    finally:
        # Restore exact pre-test state.
        if had_saved:
            aigverse.__dict__[name] = saved
        else:
            aigverse.__dict__.pop(name, None)
