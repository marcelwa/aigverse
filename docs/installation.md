# Installation

`aigverse` offers Python bindings on top of the [EPFL Logic Synthesis Libraries](https://arxiv.org/abs/1805.05121) together with custom adapters that enable convenient integration into machine learning pipelines.
The resulting Python package is available on [PyPI](https://pypi.org/project/aigverse/) and can be installed on all major operating systems using all modern Python versions.

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

To keep the library as light-weight as possible for default logic synthesis tasks, machine learning integration adapters
for `aigverse` are not installed by default as those require many additional dependencies. Instead, you can opt in to
the adapters by installing the `aigverse[adapters]` extra:

::::{tab-set}
:sync-group: installer

:::{tab-item} uv _(recommended)_
:sync: uv

```console
$ uv pip install aigverse[adapters]
```

:::

:::{tab-item} pip
:sync: pip

```console
(.venv) $ python -m pip install aigverse[adapters]
```

:::
::::

The same syntax applies to adding the `aigverse` package with adapters as a dependency to your own project.
