from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace


def test_coverage_session_isolates_build_and_resets_counters(monkeypatch, tmp_path):
    nox = ModuleType("nox")
    nox.__dict__.update(options=SimpleNamespace(), session=lambda **_kwargs: lambda function: function)
    monkeypatch.setitem(sys.modules, "nox", nox)
    spec = importlib.util.spec_from_file_location("coverage_noxfile", Path(__file__).parents[1] / "noxfile.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "__file__", str(tmp_path / "noxfile.py"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module.shutil, "which", lambda _name: "/usr/bin/tool")
    monkeypatch.setattr(sys, "platform", "linux")

    build_dir = tmp_path / "build" / "coverage"
    build_dir.mkdir(parents=True)
    counter = build_dir / "bindings.gcda"
    notes = build_dir / "bindings.gcno"
    ordinary_counter = tmp_path / "build" / "ordinary.gcda"
    notes.touch()
    ordinary_counter.touch()
    commands = []

    class Session:
        python = "3.12"
        virtualenv = SimpleNamespace(location=str(tmp_path / "venv"))

        def __init__(self):
            self.posargs = ["--full", "-m", "not network"]
            self.env = {}

        def install(self, *args):
            commands.append((args, dict(self.env)))

        def run(self, *args, **kwargs):
            commands.append((args, {**self.env, **kwargs.get("env", {})}))
            if args[:2] == ("uv", "build"):
                wheel_dir = Path(args[args.index("--out-dir") + 1])
                (wheel_dir / "aigverse.whl").touch()
            if "pytest" in args:
                assert not counter.exists()

        def log(self, _message):
            pass

    module.tests(Session())
    commands.clear()
    session = Session()
    for _ in range(2):
        counter.touch()
        module.coverage(session)

    assert notes.exists()
    assert ordinary_counter.exists()
    builds = [(args, env) for args, env in commands if args[:2] == ("uv", "build")]
    assert len(builds) == 1
    build_args, build_env = builds[0]
    assert build_args[build_args.index("--out-dir") + 1] == str(Path(".nox/_wheels/coverage-cp310-abi3"))
    assert build_env["SKBUILD_BUILD_DIR"] == str(build_dir)
    assert build_env["SKBUILD_CMAKE_BUILD_TYPE"] == "Debug"
    assert build_env["SKBUILD_CMAKE_DEFINE"] == "AIGVERSE_ENABLE_COVERAGE=ON"
    assert any(args == ("--group", "coverage") for args, _ in commands)
    assert any(args[:2] == ("uv", "sync") and "--inexact" in args for args, _ in commands)
    pytest_args = next(args for args, _ in commands if "pytest" in args)
    assert "-n0" in pytest_args
    assert "--cov" in pytest_args
    assert "--cov-config=pyproject.toml" in pytest_args
    assert f"--cov-report=xml:{build_dir / 'python.xml'}" in pytest_args
    assert pytest_args[-2:] == ("-m", "not network")
    gcovr_args = next(args for args, _ in commands if "gcovr" in args)
    assert "--include-internal-functions" in gcovr_args
    assert f"--xml={build_dir / 'cpp.xml'}" in gcovr_args
