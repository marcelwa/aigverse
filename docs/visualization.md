---
file_format: mystnb
kernelspec:
  name: python3
mystnb:
  number_source_lines: true
---

```{code-cell} ipython3
:tags: [remove-cell]
%config InlineBackend.figure_formats = ['svg']
```

# Visualization

Logic synthesis is inherently structural, and visualizing an AIG is one of the fastest ways to debug a network,
understand what an optimization pass actually changed, or explain a circuit to someone else. `aigverse` does not
ship its own plotting library, but it exposes the network structure through standard formats and adapters so that
mature Python visualization tooling can be used directly. The examples below use structured benchmark networks
(see {doc}`generators`) rather than arbitrary toy circuits, so the resulting structures are non-trivial and
reproducible: the Graphviz, NetworkX, and highlighting examples share a single ripple-carry adder, while the
optimization comparison at the end uses a separate carry-lookahead adder.

## Graphviz (DOT) Export

The {py:func}`~aigverse.io.write_dot` function writes a network to a
[Graphviz](https://graphviz.org/) DOT file. Once written, the file can be rendered directly inside a script or
notebook using the [`graphviz`](https://graphviz.readthedocs.io/) Python package.

```{code-cell} ipython3
import graphviz

from aigverse.generators import ripple_carry_adder
from aigverse.io import write_dot

# A 4-bit ripple-carry adder, reused throughout this page
aig = ripple_carry_adder(bitwidth=4)

# Write to DOT format
write_dot(aig, "example.dot")

# Render the DOT file inline
graphviz.Source.from_file("example.dot")
```

:::{note}
Rendering DOT files requires a local Graphviz installation (the `dot` executable) in addition to the `graphviz`
Python package.
:::

## NetworkX and Matplotlib

The {py:meth}`~aigverse.networks.Aig.to_networkx` adapter converts an AIG into a {py:class}`~networkx.DiGraph`,
which can be laid out and drawn with [NetworkX](https://networkx.org/) and [Matplotlib](https://matplotlib.org/).
A full worked example that labels nodes with their level, fanout, type, and function is available in the
[NetworkX section](machine_learning.md#networkx) of the Machine Learning Integration guide. A minimal version of
the same workflow, using `networkx.multipartite_layout` to place every node on the row that matches its logic
level (so all primary inputs line up on a single row) and coloring nodes by type:

```{code-cell} ipython3
import matplotlib.pyplot as plt
import networkx as nx

import aigverse.adapters

# Node type one-hot order is [constant, pi, gate, po]
type_colors = ["black", "#4C72B0", "#DDDDDD", "#55A868"]


def draw_layered(graph, node_colors, node_sizes, *, title):
    """Draws a NetworkX AIG graph with nodes arranged into rows by logic level."""
    pos = nx.multipartite_layout(graph, subset_key="level", align="horizontal")
    plt.figure(figsize=(8, 5))
    nx.draw(
        graph, pos, node_color=node_colors, node_size=node_sizes, edgecolors="black", linewidths=0.8,
        arrows=True, arrowsize=10, width=0.8,
    )
    plt.title(title)
    plt.show()


# Convert the AIG to a NetworkX graph, including each node's logic level
G = aig.to_networkx(levels=True)

node_colors = [type_colors[data["type"].argmax()] for _, data in G.nodes(data=True)]
draw_layered(G, node_colors, node_sizes=180, title="Ripple-carry adder structure")
```

## Highlighting Critical Paths and Fanout

Wrapping an AIG in {py:class}`~aigverse.networks.DepthAig` or {py:class}`~aigverse.networks.FanoutAig` exposes
per-node critical-path and fanout information, which can be used to color-code a plot, making bottlenecks and
high-congestion nodes immediately visible.

```{code-cell} ipython3
from aigverse.networks import DepthAig, FanoutAig

depth_aig = DepthAig(aig)
fanout_aig = FanoutAig(aig)

# Synthetic PO nodes (index >= aig.size) represent outputs, not real AIG nodes, so they are excluded here.
node_colors = ["#C44E52" if node < aig.size and depth_aig.is_on_critical_path(node) else "#DDDDDD" for node in G.nodes()]
node_sizes = [100 + 300 * fanout_aig.fanout_size(node) if node < aig.size else 100 for node in G.nodes()]

draw_layered(G, node_colors, node_sizes, title="Critical path (red) and fanout-scaled node size")
```

## Interactive Exploration

For larger AIGs, a static plot quickly becomes hard to read. Interactive graph-drawing libraries such as
[pyvis](https://pyvis.readthedocs.io/) or [ipycytoscape](https://ipycytoscape.readthedocs.io/) can render the same
{py:class}`~networkx.DiGraph` produced by {py:meth}`~aigverse.networks.Aig.to_networkx` as a zoomable, draggable
graph with hover tooltips for node attributes. These are not dependencies of `aigverse` and must be installed
separately.

## Before vs. After: Visualizing Optimization

Comparing the DOT rendering of a network before and after an optimization pipeline visually confirms the effect
of the transformation on structure, depth, and gate count. A 4-bit carry-lookahead adder makes for a good
demonstration here, since (unlike the ripple-carry adder above) its structure still leaves room for the
resubstitution, refactoring, and rewriting passes from the [Algorithms](algorithms.md#optimization) guide to find
and remove redundant logic.

```{code-cell} ipython3
from aigverse.algorithms import aig_cut_rewriting, aig_resubstitution, balancing, cleanup_dangling, sop_refactoring
from aigverse.generators import carry_lookahead_adder
from aigverse.networks import DepthAig

# Generators can leave behind a handful of dead gates; clean those up first for a fair baseline
aig_cla = cleanup_dangling(carry_lookahead_adder(bitwidth=4))

aig_optimized = aig_cla.clone()
aig_optimized = aig_resubstitution(aig_optimized)
aig_optimized = sop_refactoring(aig_optimized)
aig_optimized = aig_cut_rewriting(aig_optimized)
aig_optimized = balancing(aig_optimized, rebalance_function="sop")

write_dot(aig_cla, "before.dot")
write_dot(aig_optimized, "after.dot")

print(f"Before: {aig_cla.num_gates} gates, {DepthAig(aig_cla).num_levels} levels")
print(f"After:  {aig_optimized.num_gates} gates, {DepthAig(aig_optimized).num_levels} levels")
```

```{code-cell} ipython3
graphviz.Source.from_file("before.dot")
```

```{code-cell} ipython3
graphviz.Source.from_file("after.dot")
```
