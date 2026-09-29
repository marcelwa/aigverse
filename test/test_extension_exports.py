from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from fnmatch import fnmatchcase

import pytest


@pytest.mark.skipif(sys.platform != "linux", reason="Inspect ELF exports with GNU nm")
@pytest.mark.parametrize("module_name", ["networks", "algorithms", "io", "generators", "utils"])
def test_extension_exports(module_name: str) -> None:
    nm = shutil.which("nm")
    assert nm is not None, "nm is required to check Linux extension exports"
    module = importlib.import_module(f"aigverse.{module_name}")
    assert module.__file__ is not None
    result = subprocess.run(
        [nm, "-D", "--defined-only", "--format=just-symbols", "--demangle", module.__file__],
        check=True,
        capture_output=True,
        text=True,
    )
    exports = result.stdout.splitlines()
    entry_point = f"PyInit_{module_name}"
    assert entry_point in exports

    # Split mode shares these exception types with nanobind-backend.
    exceptions = ("python_error", "builtin_exception")
    unexpected = [
        symbol
        for symbol in exports
        if symbol != entry_point
        and not any(fnmatchcase(symbol, f"*nanobind::abi*::{exception}*") for exception in exceptions)
    ]
    assert not unexpected, f"Unexpected exports from {module_name}: {unexpected}"
    assert any(fnmatchcase(symbol, "typeinfo for nanobind::abi*::python_error") for symbol in exports)
    if module_name in {"networks", "utils"}:
        assert any(fnmatchcase(symbol, "typeinfo for nanobind::abi*::builtin_exception") for symbol in exports)
