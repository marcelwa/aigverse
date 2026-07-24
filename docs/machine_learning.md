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

# Machine Learning Integration

Many ML and data science workflows are Python-first, while mature logic synthesis data structures and algorithms are
predominantly implemented in C/C++ toolchains. Without reusable infrastructure, projects often reimplement synthesis
functionality in Python or rely on brittle wrappers and file-conversion scripts around external tools. `aigverse`
addresses this gap by exposing native AIG construction, manipulation, optimization, and analysis through an idiomatic
Python API, and by providing optional adapters for graph and numeric representations. This enables reproducible dataset
generation, feature extraction, and downstream model experimentation from within standard Python workflows.

## Adapters

Adapters are the interoperability layer for ML and data science workflows. To keep the base library lightweight, they
are optional and installed via the `adapters` extra only when needed. See the
[Installation](installation.md#machine-learning-adapters) documentation for more details.

## Dataset Generation

The generators module offers a reproducible way to create synthetic AIG datasets before converting them into ML-ready
formats.

```{code-cell} ipython3
import random

from aigverse.generators import random_aig

rng = random.Random(1234)

# Generate a reproducible, size-diverse AIG dataset
dataset = [
    random_aig(
        num_pis=rng.randint(4, 6),
        num_gates=rng.randint(20, 40),
        seed=5000 + i,
    )
    for i in range(16)
]

print(len(dataset), dataset[0].num_pis, dataset[0].num_gates)
```

## NetworkX

The [NetworkX](https://networkx.org/) adapter allows you to convert an AIG into a {py:class}`~networkx.DiGraph` object.
This enables use of graph-analysis and graph-learning tooling that operates on NetworkX graphs. Once converted, you can
extract node and edge features, visualize the structure (e.g., with [Matplotlib](https://matplotlib.org/)), or feed
the graph into downstream model pipelines.

```{code-cell} ipython3
import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import numpy as np

from aigverse.networks import Aig
import aigverse.adapters

# Create a sample AIG
aig = Aig()
a = aig.create_pi()
b = aig.create_pi()
c = aig.create_pi()
f1 = aig.create_and(a, b)
f2 = aig.create_or(f1, c)
aig.create_po(f2)

# Convert the AIG to a NetworkX graph
G = aig.to_networkx(levels=True, fanouts=True, node_tts=True, dtype=np.int32)

# Generate the initial layout using Graphviz's 'dot' program
pos = graphviz_layout(G, prog="dot")

# Invert the y-axis to flip the layout upside down
# This places the primary inputs (level 0) at the bottom
for node, position in pos.items():
    pos[node] = (position[0], -position[1])

# Prepare the labels for nodes and edges from graph attributes
node_labels = {
    node: f"Level: {data['level']}\nFanouts: {data['fanouts']}\nType: {data['type']}\nFunction: {data['function']}"
    for node, data in G.nodes(data=True)
}
edge_labels = {(u, v): data["type"] for u, v, data in G.edges(data=True)}

# Plot the graph
plt.figure(figsize=(12, 8))
plt.title("AIG with Attribute Labels")

# Draw the graph structure (just the edges and arrows)
nx.draw_networkx_nodes(G, pos, node_size=0)

# Draw the node labels with a bounding box
nx.draw_networkx_labels(
    G,
    pos,
    labels=node_labels,
    font_size=10,
    bbox={"facecolor": "lightblue", "edgecolor": "black", "boxstyle": "round,pad=0.5"},
)

# Draw the network edges
nx.draw_networkx_edges(
    G,
    pos,
    node_size=5000,
    arrows=True,
    arrowstyle="->",
    arrowsize=20,
)

# Draw the edge labels to show edge attributes
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="red", font_size=8)

# Pad and show the plot
plt.margins(x=0.2)
plt.show()
```

## DLPack Tensors

For high-throughput ML pipelines, `aigverse` can export AIG objects directly as graph tensors (node
attributes, edge indices, and edge attributes) utilizing the [DLPack](https://dmlc.github.io/dlpack/latest/) protocol via the {py:meth}`~aigverse.networks.Aig.to_graph_tensors` method. This allows
zero-copy hand-off to modern tensor frameworks, such
as [PyTorch](https://docs.pytorch.org/docs/stable/dlpack.html),
[JAX](https://docs.jax.dev/en/latest/_autosummary/jax.dlpack.from_dlpack.html#jax.dlpack.from_dlpack),
[TensorFlow](https://www.tensorflow.org/api_docs/python/tf/experimental/dlpack/from_dlpack), etc., through
`from_dlpack`.

Encoding and `dtype` mapping:

- Edge encoding (`edge_attr`):
  - `EdgeTensorEncoding.BINARY`: regular `0.0`, inverted `1.0`
  - `EdgeTensorEncoding.SIGNED`: regular `+1.0`, inverted `-1.0`
  - `EdgeTensorEncoding.ONE_HOT`: regular `[1.0, 0.0]`, inverted `[0.0, 1.0]`
- Node encoding (`node_attr`):
  - `NodeTensorEncoding.INTEGER`: `constant=0`, `pi=1`, `gate=2`, `po=3`
  - `NodeTensorEncoding.ONE_HOT`: `[constant, pi, gate, po]`
- Tensor `dtype`s:
  - `edge_index`: `int64`
  - `edge_attr`: `float32`
  - `node_attr`: `float32`

Tensor shapes follow the convention:

$$
\mathbf{edge\_index} \in \mathbb{Z}^{2 \times E}, \quad
\mathbf{edge\_attr} \in \mathbb{R}^{E \times D_{\text{edge}}}, \quad
\mathbf{node\_attr} \in \mathbb{R}^{N \times D_{\text{node}}}
$$

where $E$ is the number of edges and $N$ is the number of nodes. For edge features,
$D_{\text{edge}} = 1$ for `BINARY` and `SIGNED`, and $D_{\text{edge}} = 2$ for `ONE_HOT`.
The node feature width $D_{\text{node}}$ depends on the chosen node encoding and enabled optional features.

:::{note}
Current limitations of `to_graph_tensors`:

- The export targets **combinational** networks. Sequential networks are not supported.
- Exported tensors are backed by **CPU host memory** (NumPy-backed DLPack producer).
- `torch.from_dlpack(...)` is zero-copy on CPU, but moving tensors to CUDA still allocates GPU memory and performs a host-to-device copy.
- When `node_tts=True`, the export is restricted to at most 16 primary inputs due to the exponential growth of truth table size. This is a practical limit for ML applications, but it is not a fundamental limitation of the API.
  :::

```{code-cell} ipython3
import torch

from aigverse.networks import Aig, EdgeTensorEncoding, NodeTensorEncoding

aig = Aig()
a = aig.create_pi()
b = aig.create_pi()
g = aig.create_and(a, b)
aig.create_po(g)

dlpack_data = aig.to_graph_tensors(
    node_encoding=NodeTensorEncoding.INTEGER,
    edge_encoding=EdgeTensorEncoding.BINARY,
    levels=True,
    fanouts=True,
    node_tts=False,
)

edge_index = torch.from_dlpack(dlpack_data["edge_index"])
edge_attr = torch.from_dlpack(dlpack_data["edge_attr"])
node_attr = torch.from_dlpack(dlpack_data["node_attr"])

print(edge_index.shape, edge_attr.shape, node_attr.shape)
```

You can immediately construct sparse tensors in Python:

```{code-cell} ipython3
num_nodes = node_attr.shape[0]

sparse_adj = torch.sparse_coo_tensor(
    indices=edge_index,
    values=edge_attr,
    size=(num_nodes, num_nodes, edge_attr.shape[1]),
    is_coalesced=True,
    check_invariants=False,
)

print(sparse_adj.shape)
```

The same export also works
with [NumPy's DLPack consumer API](https://numpy.org/doc/stable/release/1.22.0-notes.html#add-nep-47-compatible-dlpack-support):

```{code-cell} ipython3
import numpy as np

edge_index_np = np.from_dlpack(aig.to_graph_tensors()["edge_index"])
print(edge_index_np.shape)
```

## Truth Tables

Truth tables are iterable, but for ML pipelines it is best to keep data in contiguous array/tensor form from the
start. A practical pattern is:

1. Materialize labels once as a NumPy array.
2. Build the input matrix with vectorized NumPy operations.
3. Convert to framework tensors (for example, [PyTorch](https://docs.pytorch.org/docs/stable/index.html)) without
   copying.

This keeps preprocessing fast and avoids Python-level loops in hot paths.

```{code-cell} ipython3
import numpy as np
import torch

from aigverse.utils import TruthTable

# Create a simple truth table (3-input majority function)
tt = TruthTable(3)
tt.create_from_hex_string("e8")

# Vectorized label extraction (shape: [2**num_vars])
y_np = np.fromiter(tt, dtype=np.uint8)

# Vectorized feature matrix generation (shape: [2**num_vars, num_vars])
n = tt.num_vars()
indices = np.array(range(2**n), dtype=np.uint32)[:, None]
bit_positions = np.array(range(n - 1, -1, -1), dtype=np.uint32)
X_np = ((indices >> bit_positions) & 1).astype(np.uint8)

# Zero-copy bridge NumPy -> PyTorch
X_torch = torch.from_numpy(X_np)
y_torch = torch.from_numpy(y_np)

print("NumPy shapes:", X_np.shape, y_np.shape)
print("Torch shapes:", X_torch.shape, y_torch.shape)
```
