"""Collect import-time crash diagnostics for aigverse extension modules."""

from __future__ import annotations

import argparse
import importlib.util
import logging
import os
import platform
import shutil
import signal
import subprocess
import sys
import textwrap
from pathlib import Path

LOGGER = logging.getLogger("aigverse.import_debug")


ALLOWED_TOOLS = {
    "dumpbin",
    "gdb",
    "ldd",
    "otool",
    "python",
    "readelf",
    "where",
}


def _configure_logging(output_file: str | None) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler(stream=sys.stdout)]
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(output_path, mode="w", encoding="utf-8"))

    logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=handlers)


def _run_command(command: list[str], *, env: dict[str, str] | None = None) -> tuple[int, str, str]:
    executable_name = Path(command[0]).name
    if executable_name not in ALLOWED_TOOLS and command[0] != sys.executable:
        msg = f"Command not permitted: {command[0]}"
        raise ValueError(msg)

    process = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
    return process.returncode, process.stdout, process.stderr


def _print_header(title: str) -> None:
    LOGGER.info("\n=== %s ===", title)


def _print_kv(key: str, value: object) -> None:
    LOGGER.info("%s: %s", key, value)


def _signal_name(returncode: int) -> str | None:
    if returncode >= 0:
        return None
    sig = -returncode
    try:
        return signal.Signals(sig).name
    except ValueError:
        return f"SIGNAL_{sig}"


def _module_spec(module_name: str) -> tuple[str | None, str | None]:
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        return None, "spec-not-found"
    return spec.origin, None


def _dump_binary_info(binary_path: Path) -> None:
    _print_header(f"Binary dependencies: {binary_path}")
    system = platform.system()

    if system == "Linux":
        tools = [
            ["ldd", str(binary_path)],
            ["readelf", "-d", str(binary_path)],
        ]
    elif system == "Darwin":
        tools = [["otool", "-L", str(binary_path)]]
    elif system == "Windows":
        tools = [["dumpbin", "/DEPENDENTS", str(binary_path)]] if shutil.which("dumpbin") else [["where", "dumpbin"]]
    else:
        tools = []

    if not tools:
        LOGGER.info("No dependency inspection tool configured for this platform.")
        return

    for command in tools:
        if shutil.which(command[0]) is None:
            LOGGER.info("Tool not found: %s", " ".join(command))
            continue
        LOGGER.info("\n$ %s", " ".join(command))
        returncode, stdout, stderr = _run_command(command)
        LOGGER.info("%s", stdout.strip() or "<no stdout>")
        if stderr.strip():
            LOGGER.info("--- stderr ---")
            LOGGER.info("%s", stderr.strip())
        _print_kv("returncode", returncode)


def _run_import_probe(module_name: str, *, ld_debug: bool) -> tuple[int, str, str]:
    code = textwrap.dedent(
        f"""
        import faulthandler
        faulthandler.enable()
        import {module_name}
        print('IMPORT_OK:{module_name}')
        """
    ).strip()

    env = os.environ.copy()
    if ld_debug and platform.system() == "Linux":
        env["LD_DEBUG"] = "libs,symbols"

    command = [sys.executable, "-X", "faulthandler", "-c", code]
    return _run_command(command, env=env)


def _run_gdb_trace(module_name: str) -> tuple[int, str, str]:
    code = f"import faulthandler; faulthandler.enable(); import {module_name}"
    command = [
        "gdb",
        "-batch",
        "-ex",
        "set pagination off",
        "-ex",
        "run",
        "-ex",
        "thread apply all bt full",
        "--args",
        sys.executable,
        "-X",
        "faulthandler",
        "-c",
        code,
    ]
    return _run_command(command)


def main() -> int:
    """Run extension import diagnostics.

    Returns:
        Process exit code. Zero indicates success, non-zero indicates one or more failed probes.
    """
    parser = argparse.ArgumentParser(
        description="Collect diagnostics for import-time crashes of aigverse extension modules.",
    )
    parser.add_argument(
        "--module-prefix",
        default="aigverse",
        help="Package prefix to inspect.",
    )
    parser.add_argument(
        "--modules",
        nargs="+",
        default=["networks", "algorithms", "io", "utils"],
        help="Extension module names below the module prefix.",
    )
    parser.add_argument(
        "--ld-debug",
        action="store_true",
        help="Enable LD_DEBUG=libs,symbols for Linux subprocess probes.",
    )
    parser.add_argument(
        "--gdb-on-fail",
        action="store_true",
        help="Run gdb backtrace for failing imports on Linux when gdb is available.",
    )
    parser.add_argument(
        "--output-file",
        default=None,
        help="Optional log file path. If set, diagnostics are written to stdout and this file.",
    )
    args = parser.parse_args()

    _configure_logging(args.output_file)

    _print_header("Runtime")
    _print_kv("python", sys.version.replace("\n", " "))
    _print_kv("executable", sys.executable)
    _print_kv("platform", platform.platform())
    _print_kv("machine", platform.machine())
    _print_kv("cwd", Path.cwd())
    _print_kv("PYTHONPATH", os.environ.get("PYTHONPATH", ""))
    _print_kv("PATH", os.environ.get("PATH", ""))
    _print_kv("LD_LIBRARY_PATH", os.environ.get("LD_LIBRARY_PATH", ""))
    _print_kv("DYLD_LIBRARY_PATH", os.environ.get("DYLD_LIBRARY_PATH", ""))

    if platform.system() == "Linux":
        _print_header("Compiler runtime")
        if shutil.which("ldd"):
            returncode, stdout, stderr = _run_command(["ldd", "--version"])
            LOGGER.info("%s", stdout.strip() or "<no stdout>")
            if stderr.strip():
                LOGGER.info("%s", stderr.strip())
            _print_kv("returncode", returncode)

    failures: list[str] = []

    for short_name in args.modules:
        module_name = f"{args.module_prefix}.{short_name}"
        _print_header(f"Module {module_name}")

        origin, error = _module_spec(module_name)
        _print_kv("spec.origin", origin)
        if error is not None:
            _print_kv("probe", error)
            failures.append(module_name)
            continue

        if origin is not None and origin.endswith((".so", ".pyd", ".dylib")):
            _dump_binary_info(Path(origin))

        returncode, stdout, stderr = _run_import_probe(module_name, ld_debug=args.ld_debug)
        _print_kv("import.returncode", returncode)
        signal_name = _signal_name(returncode)
        if signal_name:
            _print_kv("import.signal", signal_name)

        LOGGER.info("--- import stdout ---")
        LOGGER.info("%s", stdout.strip() or "<no stdout>")
        LOGGER.info("--- import stderr ---")
        LOGGER.info("%s", stderr.strip() or "<no stderr>")

        if returncode != 0:
            failures.append(module_name)
            if args.gdb_on_fail and platform.system() == "Linux" and shutil.which("gdb") is not None:
                _print_header(f"gdb backtrace for {module_name}")
                gdb_rc, gdb_out, gdb_err = _run_gdb_trace(module_name)
                _print_kv("gdb.returncode", gdb_rc)
                LOGGER.info("--- gdb stdout ---")
                LOGGER.info("%s", gdb_out.strip() or "<no stdout>")
                LOGGER.info("--- gdb stderr ---")
                LOGGER.info("%s", gdb_err.strip() or "<no stderr>")

    _print_header("Summary")
    if not failures:
        LOGGER.info("All module probes succeeded.")
        return 0

    LOGGER.info("Failing module probes:")
    for module_name in failures:
        LOGGER.info("- %s", module_name)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
