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

The `networkx` adapter allows you to convert an AIG into a `networkx.DiGraph` object. This is a powerful feature, as it
enables you to leverage the rich ecosystem of graph-based machine learning tools and libraries that operate on
[NetworkX](https://networkx.org/) graphs. Once converted, you can easily extract node and edge features, visualize the
structure (e.g., with [Matplotlib](https://matplotlib.org/)), or use the graph as input to graph neural networks and
other ML models.

```{code-cell} ipython3
import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout

from aigverse import Aig, adapters

# Create a sample AIG
aig = Aig()
a = aig.create_pi()
b = aig.create_pi()
c = aig.create_pi()
f1 = aig.create_and(a, b)
f2 = aig.create_or(f1, c)
aig.create_po(f2)

# Convert the AIG to a NetworkX graph
G = aig.to_networkx(levels=True, fanouts=True, node_tts=True)

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
nx.draw(G, pos, with_labels=False, node_size=0, arrowsize=20)

# Draw the node labels with a bounding box
nx.draw_networkx_labels(
    G,
    pos,
    labels=node_labels,
    font_size=10,
    bbox={"facecolor": "lightblue", "edgecolor": "black", "boxstyle": "round,pad=0.5"},
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
[TensorFlow](https://www.tensorflow.org/). You can use these arrays as labels or features in supervised learning tasks,
or as part of a dataset for training and evaluating models.

```{code-cell} ipython3
from aigverse import TruthTable
import numpy as np

# Create a simple truth table
tt = TruthTable(3)
tt.create_from_hex_string("e8")  # Majority function

# Convert to Python list
tt_list = [int(tt.get_bit(i)) for i in range(tt.num_bits())]
print(f"As list: {tt_list}")

# Convert to NumPy array
tt_array = np.array(tt_list)
print(f"As NumPy array: {tt_array}")

# Generate input combinations (for ML feature matrix)
def generate_inputs(num_vars):
    inputs = []
    for i in range(2**num_vars):
        # Convert i to binary and pad with zeros
        binary = bin(i)[2:].zfill(num_vars)
        inputs.append([int(bit) for bit in binary])
    return inputs

inputs = generate_inputs(tt.num_vars())
outputs = tt_list

print("\nInput-output pairs for ML:")
for i, (x, f) in enumerate(zip(inputs, outputs)):
    print(f"  Input: {x}, Output: {f}")
```
