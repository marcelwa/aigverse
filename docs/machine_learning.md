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

### NetworkX

The [NetworkX](https://networkx.org/) adapter allows you to convert an AIG into a {py:class}`~networkx.DiGraph` object.
This enables you to leverage the rich ecosystem of graph-based machine learning and data science tools that operate on
NetworkX graphs. Once converted, you can easily extract node and edge features, visualize the structure (e.g., with
[Matplotlib](https://matplotlib.org/)), or use it as input to graph ML models.

```{code-cell} ipython3
import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import numpy as np

from aigverse import Aig
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

## Truth Tables

Truth tables can be easily converted to Python lists or [NumPy](https://numpy.org/) arrays, making them compatible with
standard ML libraries such as [scikit-learn](https://scikit-learn.org/), [PyTorch](https://pytorch.org/), or
[TensorFlow](https://www.tensorflow.org/). Since `TruthTable` objects are iterable, this conversion is direct and
intuitive. You can use these arrays as labels or features in supervised learning tasks, or as part of a dataset for
training and evaluating models.

```{code-cell} ipython3
from aigverse import TruthTable
import numpy as np

# Create a simple truth table, e.g., a 3-input majority function
tt = TruthTable(3)
tt.create_from_hex_string("e8")

# Export to a list
tt_list = list(tt)
print(f"As list: {tt_list}")

# Export to NumPy arrays of different types
tt_np_bool = np.array(tt)
print(f"As NumPy bool array:  {tt_np_bool}")
tt_np_int = np.array(tt, dtype=np.int32)
print(f"As NumPy int array:   {tt_np_int}")
tt_np_float = np.array(tt, dtype=np.float64)
print(f"As NumPy float array: {tt_np_float}")


# These arrays can now be used as labels for an ML model.
# For example, let's generate the corresponding feature matrix:
def generate_inputs(num_vars):
    inputs = []
    for i in range(2**num_vars):
        # Convert i to binary and pad with zeros
        binary = bin(i)[2:].zfill(num_vars)
        inputs.append([int(bit) for bit in binary])
    return np.array(inputs)


feature_matrix = generate_inputs(tt.num_vars())
labels = tt_np_int  # Using the integer array as labels

print("\nFeature matrix (X) and labels (y) for ML:")
print("X:\n", feature_matrix)
print("y:\n", labels)
```
