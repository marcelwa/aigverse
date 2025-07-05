# `aigverse` - A Python Library for Logic Networks, Synthesis, and Optimization

```{raw} latex
\begin{abstract}
```

`aigverse` is an open-source C++17 and Python library for working with logic networks, synthesis, and optimization. It is developed by Marcel Walter at the [Technical University of Munich](https://www.tum.de/).

`aigverse` builds directly upon the [EPFL Logic Synthesis Libraries](https://arxiv.org/abs/1805.05121), particularly [mockturtle](https://github.com/lsils/mockturtle), providing a high-level Python interface to these powerful C++ libraries. This foundation gives `aigverse` access to state-of-the-art algorithms for And-Inverter Graph (AIG) manipulation and logic synthesis, while bridging the gap between logic synthesis and AI/ML applications. With `aigverse`, you can represent and manipulate logic circuits efficiently and integrate logic synthesis tasks into machine learning pipelines.

Key features include:

- Efficient logic representation using And-Inverter Graphs (AIGs)
- Support for various file formats (AIGER, Verilog, Bench, PLA)
- High-performance C++ backend with a Pythonic interface
- Integration capabilities with machine learning and data science workflows
- Comprehensive tools for logic synthesis and optimization

This documentation provides a comprehensive guide to the `aigverse` library, including {doc}`installation instructions <installation>`, a {doc}`quickstart guide <aigs>`, and detailed {doc}`API documentation <api/aigverse/index>`.
The source code of `aigverse` is publicly available on GitHub at [marcelwa/aigverse](https://github.com/marcelwa/aigverse), while pre-built binaries are available via [PyPI](https://pypi.org/project/aigverse/) for all major operating systems and all modern Python versions.

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
machine_learning
```

````{only} not latex
```{toctree}
:maxdepth: 2
:titlesonly:
:caption: Developers
:glob:

contributing
support
consulting
DevelopmentGuide
```
````

```{toctree}
:hidden:
:caption: Python API Reference

api/aigverse/index
```
