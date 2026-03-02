"""Collect runtime crash diagnostics for aigverse extension modules.

This script executes focused runtime probes in isolated subprocesses to capture
segfaults and heap corruption that only show up when calling into extension code
(not merely importing modules).
"""

from __future__ import annotations

import argparse
import logging
import os
import platform
import shutil
import signal
import subprocess
import sys
from pathlib import Path

LOGGER = logging.getLogger("aigverse.runtime_debug")


PROBES: dict[str, str] = {
    "io_read_aiger_missing": """
from pathlib import Path
from aigverse.io import read_aiger_into_aig

missing = Path.cwd() / "__aigverse_missing_binary_file__.aig"

try:
    read_aiger_into_aig(str(missing))
except RuntimeError:
    print("EXPECTED_RUNTIME_ERROR")
    raise SystemExit(0)
except Exception as exc:
    print(f"UNEXPECTED_EXCEPTION:{type(exc).__name__}:{exc}")
    raise SystemExit(2)
else:
    print("NO_EXCEPTION")
    raise SystemExit(3)
""".strip(),
    "io_read_ascii_aiger_missing": """
from pathlib import Path
from aigverse.io import read_ascii_aiger_into_aig

missing = Path.cwd() / "__aigverse_missing_ascii_file__.aag"

try:
    read_ascii_aiger_into_aig(str(missing))
except RuntimeError:
    print("EXPECTED_RUNTIME_ERROR")
    raise SystemExit(0)
except Exception as exc:
    print(f"UNEXPECTED_EXCEPTION:{type(exc).__name__}:{exc}")
    raise SystemExit(2)
else:
    print("NO_EXCEPTION")
    raise SystemExit(3)
""".strip(),
    "io_read_seq_aiger_missing": """
from pathlib import Path
from aigverse.io import read_aiger_into_sequential_aig

missing = Path.cwd() / "__aigverse_missing_seq_file__.aig"

try:
    read_aiger_into_sequential_aig(str(missing))
except RuntimeError:
    print("EXPECTED_RUNTIME_ERROR")
    raise SystemExit(0)
except Exception as exc:
    print(f"UNEXPECTED_EXCEPTION:{type(exc).__name__}:{exc}")
    raise SystemExit(2)
else:
    print("NO_EXCEPTION")
    raise SystemExit(3)
""".strip(),
    "alg_equivalence_mismatch": """
from aigverse.algorithms import equivalence_checking
from aigverse.networks import Aig

spec = Aig()
impl = Aig()

a1 = spec.create_pi()
b1 = spec.create_pi()
spec.create_po(spec.create_and(a1, b1))

x2 = impl.create_pi()
y2 = impl.create_pi()
impl.create_po(impl.create_and(x2, y2))

# Intentionally invalid: signal belongs to a different network.
impl.create_po(a1)

try:
    equivalence_checking(spec, impl)
except RuntimeError:
    print("EXPECTED_RUNTIME_ERROR")
    raise SystemExit(0)
except Exception as exc:
    print(f"UNEXPECTED_EXCEPTION:{type(exc).__name__}:{exc}")
    raise SystemExit(2)
else:
    print("NO_EXCEPTION")
    raise SystemExit(3)
""".strip(),
    "alg_equivalence_smoke": """
from aigverse.algorithms import equivalence_checking
from aigverse.networks import Aig

spec = Aig()
impl = Aig()

a1 = spec.create_pi()
b1 = spec.create_pi()
spec.create_po(spec.create_and(a1, b1))

x2 = impl.create_pi()
y2 = impl.create_pi()
impl.create_po(impl.create_and(x2, y2))

result = equivalence_checking(spec, impl)
print(f"RESULT:{result}")
if result is True:
    raise SystemExit(0)
raise SystemExit(4)
""".strip(),
    "io_read_aiger_smoke": """
from pathlib import Path
from aigverse.io import read_aiger_into_aig

fixture = Path.cwd() / "test" / "resources" / "mux21.aig"
if not fixture.exists():
    print(f"FIXTURE_MISSING:{fixture}")
    raise SystemExit(5)

ntk = read_aiger_into_aig(str(fixture))
print(f"SIZE:{ntk.size()}")
raise SystemExit(0)
""".strip(),
}


def _configure_logging(output_file: str | None) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler(stream=sys.stdout)]
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(output_path, mode="w", encoding="utf-8"))

    logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=handlers)


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


def _run_command(command: list[str], *, timeout: int | None = None) -> tuple[int, str, str, bool]:
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode(errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode(errors="replace")
        return 124, stdout, stderr, True

    return process.returncode, process.stdout, process.stderr, False


def _run_probe(name: str, snippet: str, *, timeout: int) -> tuple[int, str, str, bool]:
    command = [sys.executable, "-X", "faulthandler", "-c", snippet]
    LOGGER.info("$ %s", " ".join([*command[:3], "<probe-snippet>"]))
    _print_kv("probe.name", name)
    return _run_command(command, timeout=timeout)


def _run_gdb_trace(name: str, snippet: str) -> tuple[int, str, str, bool]:
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
        snippet,
    ]
    LOGGER.info("$ %s", " ".join([*command[:10], "..."]))
    _print_kv("gdb.probe", name)
    return _run_command(command)


def main() -> int:
    """Collect diagnostics for runtime crashes in aigverse extension calls.

    Probes are defined as Python code snippets that are executed in isolated subprocesses.
    The script captures return codes, stdout, stderr, and signals for each probe.
    Use "--gdb-on-fail" to run gdb backtraces for failing probes on Linux when gdb is available.

    Returns:
        Process exit code. Zero indicates all probes succeeded, non-zero indicates one or more
        failed probes or invalid probe selection.
    """
    parser = argparse.ArgumentParser(
        description="Collect diagnostics for runtime crashes in aigverse extension calls.",
    )
    parser.add_argument(
        "--probes",
        nargs="+",
        default=list(PROBES.keys()),
        help="Probe names to execute.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Per-probe timeout in seconds.",
    )
    parser.add_argument(
        "--gdb-on-fail",
        action="store_true",
        help="Run gdb backtrace on Linux for failing probes when gdb is available.",
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
    _print_kv("PATH", os.environ.get("PATH", ""))

    _print_header("Probe selection")
    invalid = [name for name in args.probes if name not in PROBES]
    if invalid:
        LOGGER.info("Unknown probes:")
        for name in invalid:
            LOGGER.info("- %s", name)
        LOGGER.info("Available probes:")
        for name in PROBES:
            LOGGER.info("- %s", name)
        return 2

    failures: list[str] = []
    for probe_name in args.probes:
        _print_header(f"Probe {probe_name}")
        returncode, stdout, stderr, timed_out = _run_probe(probe_name, PROBES[probe_name], timeout=args.timeout)

        _print_kv("probe.returncode", returncode)
        if timed_out:
            _print_kv("probe.timeout", True)

        signal_name = _signal_name(returncode)
        if signal_name is not None:
            _print_kv("probe.signal", signal_name)

        LOGGER.info("--- probe stdout ---")
        LOGGER.info("%s", stdout.strip() or "<no stdout>")
        LOGGER.info("--- probe stderr ---")
        LOGGER.info("%s", stderr.strip() or "<no stderr>")

        if returncode != 0:
            failures.append(probe_name)
            if args.gdb_on_fail and platform.system() == "Linux" and shutil.which("gdb") is not None and not timed_out:
                _print_header(f"gdb backtrace for {probe_name}")
                gdb_rc, gdb_out, gdb_err, gdb_timeout = _run_gdb_trace(probe_name, PROBES[probe_name])
                _print_kv("gdb.returncode", gdb_rc)
                if gdb_timeout:
                    _print_kv("gdb.timeout", True)
                LOGGER.info("--- gdb stdout ---")
                LOGGER.info("%s", gdb_out.strip() or "<no stdout>")
                LOGGER.info("--- gdb stderr ---")
                LOGGER.info("%s", gdb_err.strip() or "<no stderr>")

    _print_header("Summary")
    if not failures:
        LOGGER.info("All runtime probes succeeded.")
        return 0

    LOGGER.info("Failing runtime probes:")
    for failure in failures:
        LOGGER.info("- %s", failure)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
