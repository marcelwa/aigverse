#!/usr/bin/env -S uv run --script --quiet
# /// script
# dependencies = ["nox"]
# ///

"""Nox sessions."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import nox

if TYPE_CHECKING:
    from collections.abc import Sequence

nox.needs_version = ">=2025.10.16"
nox.options.default_venv_backend = "uv"

nox.options.sessions = ["lint", "tests", "minimums"]

PYTHON_ALL_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.14"]

if os.environ.get("CI", None):
    nox.options.error_on_missing_interpreters = True


@nox.session(reuse_venv=True)
def lint(session: nox.Session) -> None:
    """Run the linter."""
    if shutil.which("pre-commit") is None:
        session.install("pre-commit")

    session.run("pre-commit", "run", "--all-files", *session.posargs, external=True)


def _run_tests(
    session: nox.Session,
    *,
    install_args: Sequence[str] = (),
    extra_command: Sequence[str] = (),
    pytest_run_args: Sequence[str] = (),
) -> None:
    env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    if os.environ.get("CI", None) and sys.platform == "win32":
        env["SKBUILD_CMAKE_ARGS"] = "-T ClangCL"

    if shutil.which("cmake") is None and shutil.which("cmake3") is None:
        session.install("cmake")
    if shutil.which("ninja") is None:
        session.install("ninja")

    # install build and test dependencies on top of the existing environment
    python_flag = f"--python={session.python}"
    session.run(
        "uv",
        "sync",
        "--inexact",
        "--only-group",
        "build",
        "--only-group",
        "test",
        python_flag,
        *install_args,
        env=env,
    )
    session.run(
        "uv",
        "sync",
        "--inexact",
        "--no-dev",  # do not auto-install dev dependencies
        "--no-build-isolation-package",
        "aigverse",  # build the project without isolation
        python_flag,
        *install_args,
        env=env,
    )
    if extra_command:
        session.run(*extra_command, env=env)
    session.run(
        "uv",
        "run",
        "--no-sync",  # do not sync as everything is already installed
        python_flag,
        *install_args,
        "pytest",
        *pytest_run_args,
        *session.posargs,
        env=env,
    )


@nox.session(reuse_venv=True, python=PYTHON_ALL_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the test suite."""
    _run_tests(session)


@nox.session(reuse_venv=True, venv_backend="uv", python=PYTHON_ALL_VERSIONS)
def minimums(session: nox.Session) -> None:
    """Test the minimum versions of dependencies."""
    _run_tests(
        session,
        install_args=["--resolution=lowest-direct"],
        pytest_run_args=["-Wdefault"],
    )
    env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    session.run("uv", "tree", "--frozen", env=env)
    session.run("uv", "lock", "--refresh", env=env)


@nox.session(reuse_venv=True, python=PYTHON_ALL_VERSIONS)
def import_debug(session: nox.Session) -> None:
    """Run import-time crash diagnostics for extension modules."""
    env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    cmake_args: list[str] = ["-DAIGVERSE_ENABLE_IMPORT_DIAGNOSTICS=ON"]

    if os.environ.get("CI", None) and sys.platform == "win32":
        cmake_args.append("-T ClangCL")

    env["SKBUILD_CMAKE_ARGS"] = " ".join(cmake_args)

    if shutil.which("cmake") is None and shutil.which("cmake3") is None:
        session.install("cmake")
    if shutil.which("ninja") is None:
        session.install("ninja")

    python_flag = f"--python={session.python}"
    session.run(
        "uv",
        "sync",
        "--inexact",
        "--only-group",
        "build",
        python_flag,
        env=env,
    )
    session.run(
        "uv",
        "sync",
        "--inexact",
        "--no-dev",
        "--no-build-isolation-package",
        "aigverse",
        python_flag,
        env=env,
    )

    diagnostics_args = list(session.posargs)
    python_tag = str(session.python).replace(".", "-")
    workspace_root = Path(os.environ.get("GITHUB_WORKSPACE", Path.cwd()))
    diagnostics_dir = workspace_root / "import-debug-artifacts"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    diagnostics_log = diagnostics_dir / f"import-debug-py{python_tag}.log"
    diagnostics_args.extend(["--output-file", str(diagnostics_log)])

    if sys.platform.startswith("linux") and "--ld-debug" not in diagnostics_args:
        diagnostics_args.append("--ld-debug")
    if sys.platform.startswith("linux") and "--gdb-on-fail" not in diagnostics_args:
        diagnostics_args.append("--gdb-on-fail")

    session.run(
        "uv",
        "run",
        "--no-sync",
        python_flag,
        "python",
        "tools/import_crash_diagnostics.py",
        *diagnostics_args,
        env=env,
    )


@nox.session(reuse_venv=True, python=PYTHON_ALL_VERSIONS)
def runtime_debug(session: nox.Session) -> None:
    """Run runtime crash diagnostics for extension module call paths."""
    env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    cmake_args: list[str] = ["-DAIGVERSE_ENABLE_IMPORT_DIAGNOSTICS=ON"]

    if os.environ.get("CI", None) and sys.platform == "win32":
        cmake_args.append("-T ClangCL")

    env["SKBUILD_CMAKE_ARGS"] = " ".join(cmake_args)

    if shutil.which("cmake") is None and shutil.which("cmake3") is None:
        session.install("cmake")
    if shutil.which("ninja") is None:
        session.install("ninja")

    python_flag = f"--python={session.python}"
    session.run(
        "uv",
        "sync",
        "--inexact",
        "--only-group",
        "build",
        python_flag,
        env=env,
    )
    session.run(
        "uv",
        "sync",
        "--inexact",
        "--no-dev",
        "--no-build-isolation-package",
        "aigverse",
        python_flag,
        env=env,
    )

    diagnostics_args = list(session.posargs)
    python_tag = str(session.python).replace(".", "-")
    workspace_root = Path(os.environ.get("GITHUB_WORKSPACE", Path.cwd()))
    diagnostics_dir = workspace_root / "runtime-debug-artifacts"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    diagnostics_log = diagnostics_dir / f"runtime-debug-py{python_tag}.log"
    diagnostics_args.extend(["--output-file", str(diagnostics_log)])

    if sys.platform.startswith("linux") and "--gdb-on-fail" not in diagnostics_args:
        diagnostics_args.append("--gdb-on-fail")

    session.run(
        "uv",
        "run",
        "--no-sync",
        python_flag,
        "python",
        "tools/runtime_crash_diagnostics.py",
        *diagnostics_args,
        env=env,
    )


@nox.session(reuse_venv=True, python=["3.12"])
def runtime_stress(session: nox.Session) -> None:
    """Run stress-oriented runtime crash diagnostics (sequential then parallel)."""
    env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    cmake_args: list[str] = ["-DAIGVERSE_ENABLE_IMPORT_DIAGNOSTICS=ON"]

    if os.environ.get("CI", None) and sys.platform == "win32":
        cmake_args.append("-T ClangCL")

    env["SKBUILD_CMAKE_ARGS"] = " ".join(cmake_args)

    if shutil.which("cmake") is None and shutil.which("cmake3") is None:
        session.install("cmake")
    if shutil.which("ninja") is None:
        session.install("ninja")

    python_flag = f"--python={session.python}"
    session.run(
        "uv",
        "sync",
        "--inexact",
        "--only-group",
        "build",
        python_flag,
        env=env,
    )
    session.run(
        "uv",
        "sync",
        "--inexact",
        "--no-dev",
        "--no-build-isolation-package",
        "aigverse",
        python_flag,
        env=env,
    )

    diagnostics_args = [
        "--repeat",
        "300",
        "--workers",
        "4",
        "--probes",
        "io_read_aiger_malformed",
        "io_read_ascii_aiger_malformed",
        "io_read_seq_aiger_malformed",
        "io_read_ascii_seq_aiger_malformed",
        "alg_equivalence_mismatch",
    ]
    diagnostics_args.extend(session.posargs)

    python_tag = str(session.python).replace(".", "-")
    workspace_root = Path(os.environ.get("GITHUB_WORKSPACE", Path.cwd()))
    diagnostics_dir = workspace_root / "runtime-debug-artifacts"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    sequential_log = diagnostics_dir / f"runtime-stress-sequential-py{python_tag}.log"
    parallel_log = diagnostics_dir / f"runtime-stress-parallel-py{python_tag}.log"

    if sys.platform.startswith("linux") and "--gdb-on-fail" not in diagnostics_args:
        diagnostics_args.append("--gdb-on-fail")

    def _without_flag(args: list[str], flag: str) -> list[str]:
        cleaned: list[str] = []
        index = 0
        while index < len(args):
            if args[index] == flag:
                index += 2
                continue
            cleaned.append(args[index])
            index += 1
        return cleaned

    base_args = _without_flag(diagnostics_args, "--workers")

    sequential_args = [*base_args, "--workers", "1", "--output-file", str(sequential_log)]
    parallel_args = [*base_args, "--workers", "4", "--output-file", str(parallel_log)]

    session.log("Running runtime stress diagnostics sequentially (workers=1)")
    session.run(
        "uv",
        "run",
        "--no-sync",
        python_flag,
        "python",
        "tools/runtime_crash_diagnostics.py",
        *sequential_args,
        env=env,
    )

    session.log("Running runtime stress diagnostics in parallel (workers=4)")

    session.run(
        "uv",
        "run",
        "--no-sync",
        python_flag,
        "python",
        "tools/runtime_crash_diagnostics.py",
        *parallel_args,
        env=env,
    )


@nox.session(reuse_venv=True)
def docs(session: nox.Session) -> None:
    """Build the docs. Use "--non-interactive" to avoid serving. Pass "-b linkcheck" to check links."""
    # Check for graphviz installation
    if shutil.which("dot") is None:
        session.error(
            "Graphviz is required for building the documentation. "
            "Please install it using your package manager. For example:\n"
            "  - macOS: `brew install graphviz`\n"
            "  - Ubuntu: `sudo apt install graphviz`\n"
            "  - Windows: `winget install graphviz` or `choco install graphviz`\n"
        )

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", dest="builder", default="html", help="Build target (default: html)")
    args, posargs = parser.parse_known_args(session.posargs)

    serve = args.builder == "html" and session.interactive
    if serve:
        session.install("sphinx-autobuild")

    env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    # install build and docs dependencies on top of the existing environment
    session.run(
        "uv",
        "sync",
        "--inexact",
        "--only-group",
        "build",
        "--only-group",
        "docs",
        env=env,
    )

    shared_args = [
        "-n",  # nitpicky mode
        "-T",  # full tracebacks
        f"-b={args.builder}",
        "docs",
        f"docs/_build/{args.builder}",
        *posargs,
    ]

    session.run(
        "uv",
        "run",
        "--no-dev",  # do not auto-install dev dependencies
        "--no-build-isolation-package",
        "aigverse",  # build the project without isolation
        "sphinx-autobuild" if serve else "sphinx-build",
        *shared_args,
        env=env,
    )
