#!/usr/bin/env -S uv run --script --quiet
# /// script
# dependencies = ["nox"]
# ///

"""Nox sessions."""

from __future__ import annotations

import argparse
import contextlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import nox

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

nox.needs_version = ">=2025.10.16"
nox.options.default_venv_backend = "uv"

PYTHON_ALL_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.14"]

if os.environ.get("CI", None):
    nox.options.error_on_missing_interpreters = True


@contextlib.contextmanager
def preserve_lockfile() -> Generator[None]:
    """Preserve uv.lock by moving it to a temporary location during a session."""
    lockfile = Path("uv.lock")
    if not lockfile.exists():
        yield
        return

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_lockfile = Path(temp_dir_name) / "uv.lock"
        shutil.move(str(lockfile), str(temp_lockfile))
        try:
            yield
        finally:
            if lockfile.exists():
                lockfile.unlink()
            shutil.move(str(temp_lockfile), str(lockfile))


@nox.session(reuse_venv=True, default=True)
def lint(session: nox.Session) -> None:
    """Run the linter."""
    if shutil.which("prek") is None:
        session.install("prek")

    session.run("prek", "run", "--all-files", *session.posargs, external=True)


# Wheels already built during this nox invocation, keyed by (group, wheel tag).
# Memoized per process rather than left on disk, so a stale wheel from an earlier
# invocation can never be picked up.
_BUILT_WHEELS: dict[tuple[str, str], Path] = {}


def _wheel_tag(python: str) -> str:
    """Return the wheel tag a given interpreter builds.

    `wheel.py-api = "cp312"` in pyproject.toml means 3.12 and everything above it
    produce one and the same abi3 wheel, so they share a tag and only need
    building once.

    Args:
        python: The interpreter version, as nox spells it, e.g. "3.12".

    Returns:
        The tag identifying the wheel that interpreter builds.
    """
    major, minor = (int(part) for part in python.split("."))
    if (major, minor) >= (3, 12):
        return "cp312-abi3"
    return f"cp{major}{minor}"


def _venv_python(session: nox.Session) -> Path:
    """Return the path to the session virtualenv's interpreter.

    `uv build --no-build-isolation` builds with whatever `--python` names, so it
    has to be pointed at the environment holding the `build` group rather than at
    a bare version number, which would resolve to a system interpreter.

    Args:
        session: The nox session whose virtualenv to locate.

    Returns:
        Path to the interpreter inside the session's virtualenv.
    """
    venv = Path(session.virtualenv.location)
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _build_or_reuse_wheel(
    session: nox.Session,
    group: str,
    env: dict[str, str],
    install_args: Sequence[str],
) -> Path:
    """Build the project wheel for this session's tag, or reuse one already built.

    Every session used to rebuild the extension from scratch, which for a matrix
    of six interpreters meant six compilations of the same 26 translation units
    per nox invocation, twice over across `tests` and `minimums`. Three of those
    tags are identical, so this collapses them: 3.12 through 3.15 share one abi3
    wheel and it is built once. It is also closer to what users get, since the
    newer interpreters then exercise the very artefact PyPI ships.

    `tests` and `minimums` cannot share a wheel: `minimums` resolves the build
    dependencies down to their floors, so its wheel is built by a different
    nanobind and scikit-build-core.

    Args:
        session: The nox session requesting the wheel.
        group: Which family of sessions this belongs to, `tests` or `minimums`.
        env: Environment to run `uv` with.
        install_args: Extra `uv` arguments, used to pin resolution.

    Returns:
        Path to the built wheel.
    """
    key = (group, _wheel_tag(session.python))
    cached = _BUILT_WHEELS.get(key)
    if cached is not None and cached.is_file():
        session.log(f"reusing {cached.name}, already built for {key[1]}")
        return cached

    out_dir = Path(".nox") / "_wheels" / f"{key[0]}-{key[1]}"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    session.run(
        "uv",
        "build",
        "--wheel",
        "--no-build-isolation",  # build deps are already in the session venv
        "--python",
        str(_venv_python(session)),
        "--out-dir",
        str(out_dir),
        *install_args,
        env=env,
    )

    built = sorted(out_dir.glob("*.whl"))
    if not built:
        session.error(f"uv build produced no wheel in {out_dir}")
    _BUILT_WHEELS[key] = built[0]
    return built[0]


def _run_tests(
    session: nox.Session,
    *,
    group: str,
    install_args: Sequence[str] = (),
    extra_command: Sequence[str] = (),
    pytest_run_args: Sequence[str] = (),
) -> None:
    """Install the project into the session and run pytest against it.

    Args:
        session: The nox session to install into and run in.
        group: Which family of sessions this belongs to, `tests` or `minimums`.
            Wheels are shared between sessions of the same group and tag.
        install_args: Extra arguments forwarded to every `uv` invocation, used to
            pin resolution for the minimums session.
        extra_command: A command to run after installing and before testing.
        pytest_run_args: Extra arguments forwarded to pytest. Note that a `-m`
            passed here replaces the one in `addopts` rather than adding to it,
            and that a `-m` in the session's posargs replaces it in turn.
    """
    # `add_help=False` keeps `-h`/`--help` in the leftovers so they reach pytest,
    # which is what someone typing `nox -s tests -- --help` is asking for.
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--full",
        action="store_true",
        help="Install every optional dependency group and run every test, network-marked ones included.",
    )
    args, posargs = parser.parse_known_args(session.posargs)

    env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}

    if shutil.which("cmake") is None and shutil.which("cmake3") is None:
        session.install("cmake")
    if shutil.which("ninja") is None:
        session.install("ninja")

    # install build and test dependencies on top of the existing environment
    python_flag = f"--python={session.python}"
    only_group_args: list[str] = ["--only-group", "build", "--only-group", "test"]
    if args.full:
        # `--full` means everything: the heavy optional dependency groups --
        # torch alone today, several hundred MB of wheel before CUDA -- plus
        # every marker that `addopts` deselects, `network` included. An empty
        # `-m` clears the ini filter rather than narrowing it.
        #
        # It is off by default so a plain `nox -s tests` stays cheap and offline,
        # and so every caller states what it wants instead of being detected. The
        # test matrix narrows it back with `--full -m "not network"`: those tests
        # download circuits, and a hiccup at GitHub must not redden the whole
        # matrix, so they keep their own workflow.
        only_group_args += ["--only-group", "torch"]
        pytest_run_args = [*pytest_run_args, "-m", ""]
    session.run(
        "uv",
        "sync",
        "--inexact",
        *only_group_args,
        python_flag,
        *install_args,
        env=env,
    )
    wheel = _build_or_reuse_wheel(session, group, env, install_args)
    session.run(
        "uv",
        "pip",
        "install",
        "--python",
        str(_venv_python(session)),
        # the version is derived from the commit, so an uncommitted source change
        # rebuilds to the same version and would otherwise be skipped as present
        "--reinstall-package",
        "aigverse",
        str(wheel),
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
        *posargs,
        env=env,
    )


def _is_abc(candidate: str) -> bool:
    """Check that a candidate executable really is ABC by asking for its version.

    Args:
        candidate: Path to the executable to probe.

    Returns:
        True if the candidate answered with an ABC version banner.
    """
    # ABC drops an `abc.history` file wherever it runs, so keep it out of the repo.
    try:
        with tempfile.TemporaryDirectory(prefix="aigverse-abc-") as scratch:
            completed = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
                [candidate, "-s", "-q", "version"],
                cwd=scratch,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
    except (OSError, subprocess.SubprocessError):
        return False

    # The exit code alone would accept anything that succeeds, `/bin/true` included.
    return completed.returncode == 0 and "abc" in completed.stdout.lower()


def _find_abc() -> str | None:
    """Locate a usable ABC executable the same way the `aigverse.abc` bridge does.

    Kept in sync with `python/aigverse/abc/_binary.py` by hand, since the noxfile
    runs before `aigverse` is installed and cannot import the bridge. Unlike the
    bridge, this does probe the candidate: discovery there must stay side-effect
    free, whereas here the whole point is to fail before a three-minute docs build
    rather than inside the first executed example.

    Returns:
        Path to an executable ABC, or None if none was found.
    """
    configured = os.environ.get("AIGVERSE_ABC")
    if configured:
        # Accepting the variable unvalidated would let the docs build start and
        # then fail much later, when an example actually invokes ABC.
        path = Path(configured).expanduser()
        if not (path.is_file() and os.access(path, os.X_OK)):
            return None
        return str(path) if _is_abc(str(path)) else None

    found = shutil.which("abc") or shutil.which("berkeley-abc")
    return found if found is not None and _is_abc(found) else None


@nox.session(reuse_venv=True, python=PYTHON_ALL_VERSIONS, default=True)
def tests(session: nox.Session) -> None:
    """Run the test suite."""
    _run_tests(session, group="tests")


@nox.session(reuse_venv=True, venv_backend="uv", python=PYTHON_ALL_VERSIONS, default=True)
def minimums(session: nox.Session) -> None:
    """Test the minimum versions of dependencies."""
    with preserve_lockfile():
        _run_tests(
            session,
            group="minimums",
            install_args=["--resolution=lowest-direct"],
            pytest_run_args=["-Wdefault"],
        )
        env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
        session.run("uv", "tree", "--frozen", env=env)
        session.run("uv", "lock", "--refresh", env=env)


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

    # The ABC documentation page executes its examples, so it needs a real ABC.
    if _find_abc() is None:
        session.error(
            "ABC is required for building the documentation, because the examples on the "
            "ABC page are executed. Install it and put it on PATH, or point AIGVERSE_ABC at "
            "it. For example:\n"
            "  - from source: `git clone https://github.com/berkeley-abc/abc && make -C abc`\n"
            "  - Ubuntu 22.04: `sudo apt install berkeley-abc`\n"
            "  - bundled: any `abc` from Yosys or oss-cad-suite\n"
        )

    # `add_help=False` for the same reason as in `_run_tests`: `-h`/`--help` belong
    # to sphinx-build, not to this parser, which only needs to peek at `-b`.
    parser = argparse.ArgumentParser(add_help=False)
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


@nox.session(reuse_venv=True, venv_backend="uv")
def stubs(session: nox.Session) -> None:
    """Generate type stubs for Python bindings using nanobind."""
    env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    session.run(
        "uv",
        "sync",
        "--no-dev",
        "--group",
        "build",
        env=env,
    )

    package_root = Path(__file__).parent / "python" / "aigverse"
    pattern_file = package_root / "stubgen.pattern"

    session.run(
        "python",
        "-m",
        "nanobind.stubgen",
        "--recursive",
        "--include-private",
        "--pattern-file",
        str(pattern_file),
        "--output-dir",
        str(package_root),
        "--module",
        "aigverse.networks",
        "--module",
        "aigverse.algorithms",
        "--module",
        "aigverse.io",
        "--module",
        "aigverse.generators",
        "--module",
        "aigverse.utils",
    )

    # nanobind mirrors the compiled extension's filename, which carries a `.abi3` tag
    # when built against the stable ABI (see `wheel.py-api` in pyproject.toml). Normalize
    # back to the plain module name so stubs are independent of the build's ABI tag.
    for abi3_stub in package_root.glob("*.abi3.pyi"):
        abi3_stub.replace(package_root / abi3_stub.name.replace(".abi3.pyi", ".pyi"))

    pyi_files = list(package_root.glob("**/*.pyi"))

    if not pyi_files:
        session.warn("No .pyi files found")
        return

    if shutil.which("prek") is None:
        session.install("prek")

    # Allow both 0 (no issues) and 1 as success codes for fixing up stubs
    success_codes = [0, 1]
    session.run("prek", "run", "ruff-format", "--files", *pyi_files, external=True, success_codes=success_codes)
    session.run("prek", "run", "ruff-check", "--files", *pyi_files, external=True, success_codes=success_codes)
    session.run("prek", "run", "ruff-format", "--files", *pyi_files, external=True, success_codes=success_codes)

    # Run ruff-check again to ensure everything is clean
    session.run("prek", "run", "ruff-check", "--files", *pyi_files, external=True)


if __name__ == "__main__":
    nox.main()
