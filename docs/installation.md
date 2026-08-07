# Installation

`aigverse` wraps mature C/C++ synthesis backends from the [EPFL Logic Synthesis Libraries](https://arxiv.org/abs/1805.05121) with an idiomatic Python interface for Python-first workflows.
Optional adapters extend this core with graph and array interoperability for downstream ML and data science pipelines. The resulting Python package is available on [PyPI](https://pypi.org/project/aigverse/) and can be installed on all major operating systems and all active Python versions.

:::::{tip}
We highly recommend using [`uv`](https://docs.astral.sh/uv/) for working with Python projects.
It is an extremely fast Python package and project manager, written in Rust and developed by [Astral](https://astral.sh/) (the same team behind [`ruff`](https://docs.astral.sh/ruff/)).
It can act as a drop-in replacement for `pip` and `virtualenv`, and provides a more modern and faster alternative to the traditional Python package management tools.
It automatically handles the creation of virtual environments and the installation of packages, and is much faster than `pip`.
Additionally, it can even set up Python for you if it is not installed yet.

If you do not have `uv` installed yet, you can install it via:

::::{tab-set}
:::{tab-item} macOS and Linux

```console
$ curl -LsSf https://astral.sh/uv/install.sh | sh
```

:::
:::{tab-item} Windows

```console
$ powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

::::

Check out their excellent [documentation](https://docs.astral.sh/uv/) for more information.

:::::

## Core Library

To install the core `aigverse` library, you can use `uv` or `pip`.

::::{tab-set}
:sync-group: installer

:::{tab-item} uv _(recommended)_
:sync: uv

```console
$ uv pip install aigverse
```

:::

:::{tab-item} pip
:sync: pip

```console
(.venv) $ python -m pip install aigverse
```

:::
::::

In most practical cases (under 64-bit Linux, macOS incl. Apple Silicon, and Windows), this requires no compilation and merely downloads and installs a platform-specific pre-built wheel.

Once installed, you can check if the installation was successful by running:

```console
(.venv) $ python -c "import aigverse; print(aigverse.__version__)"
```

which should print the installed version of the library.

---

If you want to use the `aigverse` Python package in your own project, you can simply add it as a dependency to your
`pyproject.toml` or `setup.py` file. This will automatically install the `aigverse` package and its dependencies when
your project is installed.

::::{tab-set}

:::{tab-item} uv _(recommended)_

```console
$ uv add aigverse
```

:::

:::{tab-item} pyproject.toml

```toml
[project]
# ...
dependencies = ["aigverse"]
# ...
```

:::

:::{tab-item} setup.py

```python
from setuptools import setup

setup(
    # ...
    install_requires=["aigverse"],
    # ...
)
```

:::
::::

## Machine Learning Adapters

The base installation intentionally excludes ML and data science adapters so that core synthesis workflows remain
lightweight and free of heavy optional dependencies. Install the `aigverse[adapters]` extra when you need graph or
numeric interoperability in Python ML/data science pipelines:

::::{tab-set}
:sync-group: installer

:::{tab-item} uv _(recommended)_
:sync: uv

```console
$ uv pip install "aigverse[adapters]"
```

:::

:::{tab-item} pip
:sync: pip

```console
(.venv) $ python -m pip install "aigverse[adapters]"
```

:::
::::

The same syntax applies to adding the `aigverse` package with adapters as a dependency to your own project.

## ABC Integration

`aigverse` does not ship [ABC](https://github.com/berkeley-abc/abc). The
{py:mod}`aigverse.abc` bridge drives an ABC executable that is already installed on your
machine, so the base installation stays lightweight and no ABC code is redistributed.

Obtain ABC in whichever way suits your platform:

- **From source** — clone [berkeley-abc/abc](https://github.com/berkeley-abc/abc) and run
  `make`, which produces an `abc` binary in the repository root.
- **Distribution package** — Debian and Ubuntu ship it as `berkeley-abc`
  (`sudo apt install berkeley-abc`); it is also in conda-forge and Homebrew.
- **Bundled toolchains** — [Yosys](https://github.com/YosysHQ/yosys) ships an ABC build,
  as does the [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build), which is
  the quickest route to a working binary if you want no build step at all: download a
  release archive and use the `abc` in its `bin/` directory. Note that both carry
  YosysHQ's ABC fork rather than `berkeley-abc/abc`, so a script may occasionally behave
  differently.

`aigverse` locates the executable in this order:

1. an explicit path set via {py:func}`~aigverse.abc.set_abc_binary`,
2. the `AIGVERSE_ABC` environment variable,
3. `abc` or `berkeley-abc` on `PATH` (Debian and Ubuntu use the latter name).

```console
export AIGVERSE_ABC=/path/to/abc
```

```python
from aigverse import abc

abc.set_abc_binary("/path/to/abc")
print(abc.is_available())
print(abc.abc_version())
```

:::{note}
Importing {py:mod}`aigverse.abc` always succeeds, whether or not ABC is installed. Use
{py:func}`~aigverse.abc.is_available` to check, and expect
{py:exc}`~aigverse.abc.AbcNotFoundError` from any call that needs the executable.
:::
