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

The field of logic synthesis is turning to data science and machine learning to tackle its most complex optimization
challenges. Traditional heuristic methods are being augmented, and in some cases replaced, by ML models that can predict
circuit properties, guide optimization steps, or uncover novel logic structures. This emerging paradigm hinges on the
ability to seamlessly integrate with the rich ecosystems of data science. By converting AIGs into formats such as graphs
and numerical arrays, you can unlock the powerful analytical and predictive capabilities of modern machine learning
workflows.

## Adapters

Adapters provide integration with machine learning workflows. To keep the base library lightweight, these adapters are
not included by default in the `aigverse` package but can be installed separately via the `adapters` extra. See
the [Installation](installation.md#machine-learning-adapters) documentation for more details.

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
This enables you to leverage the rich ecosystem of graph-based machine learning and data science tools that operate on
NetworkX graphs. Once converted, you can easily extract node and edge features, visualize the structure (e.g., with
[Matplotlib](https://matplotlib.org/)), or use it as input to graph ML models.

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

For high-throughput ML pipelines, `aigverse` can export AIG objects directly as graph tensors (node attributes, edge
indices, and edge attributes) utilizing the [DLPack](https://dmlc.github.io/dlpack/latest/) protocol. This allows zero-copy hand-off to modern
tensor frameworks, such
as [PyTorch](https://docs.pytorch.org/docs/stable/dlpack.html),
[JAX](https://docs.jax.dev/en/latest/_autosummary/jax.dlpack.from_dlpack.html#jax.dlpack.from_dlpack),
[TensorFlow](https://www.tensorflow.org/api_docs/python/tf/experimental/dlpack/from_dlpack), etc., through
`from_dlpack`.

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
    include_level=True,
    include_fanout=True,
    include_truth_table=False,
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

Encoding and dtype mapping:

- Edge encoding (`edge_attr`):
  - `EdgeTensorEncoding.BINARY`: regular `0.0`, inverted `1.0`
  - `EdgeTensorEncoding.SIGNED`: regular `+1.0`, inverted `-1.0`
  - `EdgeTensorEncoding.ONE_HOT`: regular `[1.0, 0.0]`, inverted `[0.0, 1.0]`
- Node encoding (`node_attr`):
  - `NodeTensorEncoding.INTEGER`: `constant=0`, `pi=1`, `gate=2`, `po=3`
  - `NodeTensorEncoding.ONE_HOT`: `[constant, pi, gate, po]`
- Tensor dtypes:
  - `edge_index`: `int64`
  - `edge_attr`: `float32`
  - `node_attr`: `float32`

The exported tensor shapes are:

- `edge_index`: `(2, E)`
- `edge_attr`: `(E, D_edge)`
- `node_attr`: `(N, D_node)`

where `D_edge` is `1` for `BINARY` and `SIGNED`, and `2` for `ONE_HOT`.

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
