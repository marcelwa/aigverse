# `aigverse` - A Python Library for Logic Networks, Synthesis, and Optimization

```{raw} latex
\begin{abstract}
```

`aigverse` is an open-source C++17 and Python infrastructure library for working with logic networks, synthesis, and
optimization in Python-first workflows.

It builds directly upon the [EPFL Logic Synthesis Libraries](https://arxiv.org/abs/1805.05121),
particularly [mockturtle](https://github.com/lsils/mockturtle), [kitty](https://github.com/lsils/kitty),
and [lorina](https://github.com/hriener/lorina), and exposes these mature C++ capabilities through an idiomatic Python
interface. This allows users to run synthesis workflows from Python without reimplementing core algorithms there. The
result is reusable support for And-Inverter Graph (AIG) construction and manipulation, optimization and equivalence
checking, dataset generation, and export into graph and numeric representations for downstream data science and ML
pipelines.

Key features include:

- Efficient logic representation using And-Inverter Graphs (AIGs)
- Support for various file formats (AIGER, Verilog, Bench, PLA)
- High-performance C++ backend with a Pythonic interface
- Optional adapters for graph and numeric interoperability in machine learning and data science workflows
- Comprehensive tools for logic synthesis and optimization

`aigverse` is designed as reusable bridge infrastructure rather than as a full end-to-end EDA toolchain.

This documentation provides a comprehensive guide to the `aigverse` library, including {doc}
`installation instructions <installation>`, a {doc}`quickstart guide <aigs>`, and detailed {doc}
`API documentation <api/aigverse/index>`.
The source code of `aigverse` is publicly available on GitHub
at [marcelwa/aigverse](https://github.com/marcelwa/aigverse), while pre-built binaries are available
via [PyPI](https://pypi.org/project/aigverse/) for all major operating systems and all modern Python versions.

```{seealso}
For a deeper dive into the vision and technical details behind `aigverse`, see the presentation **"aigverse: Toward machine learning-driven logic synthesis"** from the [Free Silicon Conference (FSiC) 2025](https://wiki.f-si.org/index.php?title=FSiC2025). The [slides are available on the FSiC wiki](https://wiki.f-si.org/index.php?title=Aigverse:_Toward_machine_learning-driven_logic_synthesis) and cover the motivation, architecture, and future directions of the `aigverse` project.
```

````{only} latex
```{note}
A live version of this document is available at [aigverse.readthedocs.io](https://aigverse.readthedocs.io).
```
````

```{raw} latex
\end{abstract}

\sphinxtableofcontents
```

```{toctree}
:hidden:

self
```

```{toctree}
:maxdepth: 2
:caption: User Guide

installation
aigs
truth_tables
algorithms
generators
machine_learning
mcp
```

````{only} not latex
```{toctree}
:maxdepth: 2
:titlesonly:
:caption: Developers
:glob:

contributing
support
DevelopmentGuide
```
````

```{toctree}
:hidden:
:caption: Python API Reference

api/aigverse/index
```
