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

## Graph-Based Machine Learning

For more sophisticated tasks, particularly those involving Graph Neural Networks (GNNs), a list of `networkx.DiGraph`
objects needs to be converted into a dataset of tensors suitable for ML libraries. The standard and most efficient way
to do this, especially in PyTorch Geometric, is to create a `Dataset` class. This class handles the one-time conversion
of raw graph objects into a processed format that can be quickly loaded for training.

The following examples demonstrate how to create proper dataset classes for PyTorch Geometric and TensorFlow. These
classes are designed to process a list of NetworkX graphs that have been converted from `aigverse.Aig` objects.

### PyTorch Geometric Dataset

For PyTorch Geometric, the best practice is to inherit from `torch_geometric.data.InMemoryDataset`. This base class is
perfect when your entire collection of graphs can fit into memory. The key logic goes into the `process` method, which
iterates through your list of raw NetworkX graphs, converts each one into a `torch_geometric.data.Data` object, and
saves the collection of `Data` objects for efficient, repeated access.

#### Option 1: Using Sparse Edge Index (Standard)

This is the most common and memory-efficient approach in PyG. It represents graph connectivity using a sparse
`edge_index` tensor.

```{code-cell} ipython3
import networkx as nx
import numpy as np
import torch
from torch_geometric.data import Data, InMemoryDataset


class AIGPygDataset(InMemoryDataset):
    """Creates a PyTorch Geometric dataset from a list of NetworkX graphs.

    This dataset uses the standard sparse edge_index representation.
    """

    def __init__(self, root: str, graph_list: list[nx.DiGraph]):
        self.graph_list = graph_list
        super().__init__(root)
        self.data, self.slices = torch.load(self.processed_paths[0], weights_only=False)

    @property
    def processed_file_names(self) -> list[str]:
        return ["data.pt"]

    def process(self) -> None:
        # This method is called once to convert the raw data into tensors.
        data_list = []
        for G in self.graph_list:
            # Node features (x): One-hot encoded type [const, pi, gate, po]
            node_features = [data["type"] for _, data in G.nodes(data=True)]
            x = torch.tensor(np.array(node_features), dtype=torch.float)

            # Edge connectivity (edge_index): COO format [2, num_edges]
            edge_index = torch.tensor(list(G.edges), dtype=torch.long).t().contiguous()

            # Edge features (edge_attr): One-hot encoded type [regular, inverted]
            edge_features = [data["type"] for _, _, data in G.edges(data=True)]
            edge_attr = torch.tensor(np.array(edge_features), dtype=torch.float)

            data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
            data_list.append(data)

        data, slices = self.collate(data_list)
        torch.save((data, slices), self.processed_paths[0])


# --- Example Usage ---
# The following assumes you have a list of NetworkX DiGraphs.
# For demonstration, we'll create a list with two graphs.
from aigverse import Aig
import aigverse.adapters

aig1 = Aig()
a, b = aig1.create_pi(), aig1.create_pi()
f = aig1.create_and(a, b)
aig1.create_po(f)
aig2 = Aig()
a, b, c = aig2.create_pi(), aig2.create_pi(), aig2.create_pi()
f1 = aig2.create_and(a, b)
f2 = aig2.create_and(f1, c)
aig2.create_po(f2)
graph_list = [aig1.to_networkx(), aig2.to_networkx()]
# ---

# Create the dataset (it will be processed and saved in the 'aig_pyg_dataset/' directory)
dataset = AIGPygDataset(root="aig_pyg_dataset/", graph_list=graph_list)

print(f"Dataset created with {len(dataset)} graphs.")
print("First graph in the dataset:")
print(dataset[0])
print("\nSecond graph in the dataset:")
print(dataset[1])
```

#### Option 2: Using Dense Adjacency Tensor

For some models, a dense adjacency tensor is more suitable. The following `Dataset` class creates a `Data` object for
each graph containing the node feature matrix (`x`) and a 3D adjacency tensor (`adj`).

```{code-cell} ipython3
import networkx as nx
import numpy as np
import torch
from torch_geometric.data import Data, InMemoryDataset


class AIGPygAdjDataset(InMemoryDataset):
    """Creates a PyTorch Geometric dataset from a list of NetworkX graphs.

    This dataset uses a dense 3D adjacency tensor for multi-relational edges.
    """

    def __init__(self, root, graph_list: list[nx.DiGraph]):
        self.graph_list = graph_list
        super().__init__(root)
        self.data, self.slices = torch.load(self.processed_paths[0], weights_only=False)

    @property
    def processed_file_names(self) -> list[str]:
        return ["data_adj.pt"]

    def process(self) -> None:
        data_list = []

        # Find the maximum number of nodes in the dataset for padding
        max_nodes = 0
        for G in self.graph_list:
            max_nodes = max(max_nodes, G.number_of_nodes())

        for G in self.graph_list:
            num_nodes = G.number_of_nodes()

            # Node features (x)
            node_features_np = np.array([data["type"] for _, data in G.nodes(data=True)], dtype=np.float32)
            # Pad node features to max_nodes
            x_padded = np.pad(node_features_np, ((0, max_nodes - num_nodes), (0, 0)), "constant")
            x = torch.from_numpy(x_padded)

            # 3D Adjacency Tensor (adj)
            adj = np.zeros((num_nodes, num_nodes, 2), dtype=np.float32)
            for u, v, data in G.edges(data=True):
                # data['type'] is a one-hot vector [1, 0] (regular) or [0, 1] (inverted)
                adj[u, v, :] = data["type"]

            # Pad adjacency tensor to max_nodes x max_nodes
            adj_padded = np.pad(adj, ((0, max_nodes - num_nodes), (0, max_nodes - num_nodes), (0, 0)), "constant")
            adj_tensor = torch.from_numpy(adj_padded)

            data = Data(x=x, adj=adj_tensor)
            data_list.append(data)

        data, slices = self.collate(data_list)
        torch.save((data, slices), self.processed_paths[0])


# --- Example Usage ---
# We use the same graph_list from the previous example.
# For demonstration, we'll create a list with two graphs.
from aigverse import Aig
import aigverse.adapters

aig1 = Aig()
a, b = aig1.create_pi(), aig1.create_pi()
f = aig1.create_and(a, b)
aig1.create_po(f)
aig2 = Aig()
a, b, c = aig2.create_pi(), aig2.create_pi(), aig2.create_pi()
f1 = aig2.create_and(a, b)
f2 = aig2.create_and(f1, c)
aig2.create_po(f2)
graph_list = [aig1.to_networkx(), aig2.to_networkx()]
# ---

# Create the dataset
adj_dataset = AIGPygAdjDataset(root="aig_pyg_adj_dataset/", graph_list=graph_list)

print(f"Adjacency Tensor Dataset created with {len(adj_dataset)} graphs.")
first_graph = adj_dataset[0]
print("First graph in the dataset:")
print(f"Node features shape: {first_graph.x.shape}")
print(f"Adjacency tensor shape: {first_graph.adj.shape}")
```

### TensorFlow Dataset

For TensorFlow, the `tf.data.Dataset` API is the standard. A common and flexible pattern is to create a Python generator
that yields your processed data (the node and adjacency tensors for each graph) and then wrap it with
`tf.data.Dataset.from_generator`. This creates an efficient, iterable input pipeline for your model.

```{code-cell} ipython3
import os

# Suppress TensorFlow GPU-related warnings by forcing CPU-only mode
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
# Suppress TensorFlow informational and warning messages
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import networkx as nx
import numpy as np
import tensorflow as tf


def aig_tf_generator(graph_list: list[nx.DiGraph]) -> tf.Tensor:
    """
    A Python generator that yields tensors for each graph in the list.
    """
    for G in graph_list:
        num_nodes = G.number_of_nodes()

        # Node feature matrix
        node_features_list = [data["type"] for _, data in G.nodes(data=True)]
        node_features = np.array(node_features_list, dtype=np.float32)

        # 3D Adjacency tensor
        adj = np.zeros((num_nodes, num_nodes, 2), dtype=np.float32)
        for u, v, data in G.edges(data=True):
            adj[u, v, :] = data["type"]

        yield node_features, adj


# --- Example Usage ---
# We use the same graph_list from the previous examples.
# For demonstration, we'll create a list with two graphs.
from aigverse import Aig
import aigverse.adapters

aig1 = Aig()
a, b = aig1.create_pi(), aig1.create_pi()
f = aig1.create_and(a, b)
aig1.create_po(f)
aig2 = Aig()
a, b, c = aig2.create_pi(), aig2.create_pi(), aig2.create_pi()
f1 = aig2.create_and(a, b)
f2 = aig2.create_and(f1, c)
aig2.create_po(f2)
graph_list = [aig1.to_networkx(), aig2.to_networkx()]
# Let's define the output tensor shapes and types for the generator.
# Note: Since graphs have variable numbers of nodes, we set node dimensions to None.
output_signature = (
    tf.TensorSpec(shape=(None, 4), dtype=tf.float32),  # 4 node types
    tf.TensorSpec(shape=(None, None, 2), dtype=tf.float32),  # 2 edge types
)

# Create the tf.data.Dataset from the generator
tf_dataset = tf.data.Dataset.from_generator(lambda: aig_tf_generator(graph_list), output_signature=output_signature)

# TensorFlow Dataset created. You can now iterate over it or use .batch(), .shuffle(), etc.
# Example of taking one element from the dataset
for node_features, adj_tensor in tf_dataset.take(1):
    print("\nFirst item in the TF dataset:")
    print(f"Node features shape: {node_features.shape}")
    print(f"Adjacency tensor shape: {adj_tensor.shape}")
```
