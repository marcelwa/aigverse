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
mature Python visualization tooling can be used directly.

## Graphviz (DOT) Export

The {py:func}`~aigverse.io.write_dot` function writes a network to a
[Graphviz](https://graphviz.org/) DOT file. Once written, the file can be rendered directly inside a script or
notebook using the [`graphviz`](https://graphviz.readthedocs.io/) Python package.

```{code-cell} ipython3
import graphviz

from aigverse.io import write_dot
from aigverse.networks import Aig

# Create a sample AIG
aig = Aig()
a = aig.create_pi()
b = aig.create_pi()
c = aig.create_pi()
f1 = aig.create_and(a, b)
f2 = aig.create_or(f1, c)
aig.create_po(f2)

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
the same workflow:

```{code-cell} ipython3
import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout

import aigverse.adapters

# Convert the AIG to a NetworkX graph
G = aig.to_networkx()

# Layer the graph so inputs and outputs are visually separated
pos = graphviz_layout(G, prog="dot")
for node, position in pos.items():
    pos[node] = (position[0], -position[1])

plt.figure(figsize=(6, 4))
nx.draw(G, pos, with_labels=True, node_color="lightblue", arrows=True, arrowsize=15)
plt.show()
```

## Highlighting Critical Paths and Fanout

Wrapping an AIG in {py:class}`~aigverse.networks.DepthAig` exposes per-node critical-path information, and passing
`fanouts=True` to {py:meth}`~aigverse.networks.Aig.to_networkx` attaches each node's fanout count directly as a
graph attribute. Combined, these can be used to color-code a plot, making bottlenecks and high-congestion nodes
immediately visible.

```{code-cell} ipython3
from aigverse.networks import DepthAig

depth_aig = DepthAig(aig)

# Request fanout counts as a node attribute
G = aig.to_networkx(fanouts=True)
pos = graphviz_layout(G, prog="dot")
for node, position in pos.items():
    pos[node] = (position[0], -position[1])

# Color critical-path nodes red, all others gray.
# Synthetic PO nodes (index >= aig.size) are not real AIG nodes, so they are excluded here.
node_colors = ["red" if node < aig.size and depth_aig.is_on_critical_path(node) else "lightgray" for node in G.nodes()]

# Size nodes by their fanout count
node_sizes = [300 + 200 * data["fanouts"] for _, data in G.nodes(data=True)]

plt.figure(figsize=(6, 4))
nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=node_sizes, arrows=True, arrowsize=15)
plt.title("Critical path (red) and fanout-scaled node size")
plt.show()
```

:::{note}
{py:meth}`~aigverse.networks.Aig.to_networkx` adds one synthetic node per primary output (index `>= aig.size`) to
represent the network's outputs. These synthetic nodes are not valid arguments for
{py:class}`~aigverse.networks.DepthAig` or {py:class}`~aigverse.networks.FanoutAig` methods, which only operate on
real AIG nodes.
:::

## Interactive Exploration

For larger AIGs, a static plot quickly becomes hard to read. Interactive graph-drawing libraries such as
[pyvis](https://pyvis.readthedocs.io/) or [ipycytoscape](https://ipycytoscape.readthedocs.io/) can render the same
{py:class}`~networkx.DiGraph` produced by {py:meth}`~aigverse.networks.Aig.to_networkx` as a zoomable, draggable
graph with hover tooltips for node attributes. These are not dependencies of `aigverse` and must be installed
separately.

## Before vs. After: Visualizing Optimization

Comparing the DOT (or NetworkX) rendering of a network before and after an optimization pass such as
{py:func}`~aigverse.algorithms.balancing` visually confirms the effect of the transformation on depth.

```{code-cell} ipython3
from aigverse.algorithms import balancing

aig_balanced = balancing(aig.clone(), rebalance_function="sop")

write_dot(aig, "before.dot")
write_dot(aig_balanced, "after.dot")

print(f"Depth before: {DepthAig(aig).num_levels} levels")
print(f"Depth after:  {DepthAig(aig_balanced).num_levels} levels")
```

```{code-cell} ipython3
graphviz.Source.from_file("before.dot")
```

```{code-cell} ipython3
graphviz.Source.from_file("after.dot")
```
