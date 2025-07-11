# aigverse: A Python Library for Logic Networks, Synthesis, and Optimization

[![CI](https://img.shields.io/github/actions/workflow/status/marcelwa/aigverse/aigverse-pypi-deployment.yml?label=CI&logo=github&style=flat-square)](https://github.com/marcelwa/aigverse/actions/workflows/aigverse-pypi-deployment.yml)
[![Documentation Status](https://img.shields.io/readthedocs/aigverse?label=Docs&logo=readthedocs&style=flat-square)](https://aigverse.readthedocs.io/)
[![PyPI](https://img.shields.io/static/v1?label=PyPI&message=aigverse&logo=pypi&color=informational&style=flat-square)](https://pypi.org/project/aigverse/)
[![License](https://img.shields.io/github/license/marcelwa/aigverse?label=License&style=flat-square)](https://github.com/marcelwa/aigverse/blob/main/LICENSE)
[![Release](https://img.shields.io/github/v/release/marcelwa/aigverse?label=aigverse&style=flat-square)](https://github.com/marcelwa/aigverse/releases)

> [!Important]
> This project is still in the early stages of development. The API is subject to change, and some features may not be
> fully implemented. I appreciate your patience and understanding as work to improve the library continues.

<p align="center">
  <a href="https://aigverse.readthedocs.io">
   <picture>
     <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/marcelwa/aigverse/refs/heads/main/docs/_static/aigverse_logo_dark_mode.svg" width="60%">
     <img src="https://raw.githubusercontent.com/marcelwa/aigverse/refs/heads/main/docs/_static/aigverse_logo_light_mode.svg" width="60%" alt="aigverse logo">
   </picture>
  </a>
</p>

`aigverse` is a Python framework designed to bridge the gap between logic synthesis and AI/ML applications. It allows
you to represent and manipulate logic circuits efficiently, making it easier to integrate logic synthesis tasks into
machine learning pipelines. `aigverse` is built directly upon the powerful [EPFL Logic Synthesis Libraries](https://arxiv.org/abs/1805.05121),
particularly [mockturtle](https://github.com/lsils/mockturtle), providing a high-level Python interface to
state-of-the-art algorithms for And-Inverter Graph (AIG) manipulation and logic synthesis, widely used in formal
verification, hardware design, and optimization tasks.

<p align="center">
  <a href="https://aigverse.readthedocs.io/">
  <img width=30% src="https://img.shields.io/badge/documentation-blue?style=for-the-badge&logo=read%20the%20docs" alt="Documentation" />
  </a>
</p>

## ✨ Features

- **Efficient Logic Representation**: Use And-Inverter Graphs (AIGs) to model and manipulate logic circuits in Python.
- **File Format Support**: Read and write AIGER, Verilog, Bench, PLA, ... files for interoperability with other logic
  synthesis tools.
- **C++ Backend**: Leverage the performance of the EPFL Logic Synthesis Libraries for fast logic synthesis and
  optimization.
- **High-Level API**: Simplify logic synthesis tasks with a Pythonic interface for AIG manipulation and optimization.
- **Integration with Machine Learning**: Convenient integration with popular data science libraries.

## 🤔 Motivation

As AI and machine learning (ML) increasingly impact hardware design automation, there's a growing need for tools that
integrate logic synthesis with ML workflows. `aigverse` provides a Python-friendly interface for logic synthesis, making
it easier to develop applications that blend both AI/ML and traditional circuit synthesis techniques. By building upon the
robust foundation of the EPFL Logic Synthesis Libraries, `aigverse` delivers powerful logic manipulation capabilities while
maintaining accessibility through its Python interface. With `aigverse`, you can parse, manipulate, and optimize logic circuits
directly from Python. Eventually, we aim to provide seamless integration with popular ML libraries, enabling the development
of novel AI-driven synthesis and optimization tools.

## 📦 Installation

`aigverse` is built using the EPFL Logic Synthesis Libraries with [pybind11](https://github.com/pybind/pybind11).
It is available via PyPI for all major operating systems and supports Python 3.9 to 3.13.

```bash
pip install aigverse
```

### 🔌 Adapters

To keep the core library lightweight, machine learning integration adapters are not installed by default. These adapters
enable seamless conversion of AIGs to graph and array formats for use with ML and data science libraries (such as
[NetworkX](https://networkx.org/), [NumPy](https://numpy.org/), etc.). To install `aigverse` with the adapters extra,
use:

```bash
pip install aigverse[adapters]
```

This will install additional dependencies required for ML workflows. See the
[documentation](https://aigverse.readthedocs.io/en/latest/installation.html#machine-learning-adapters) for more details.

## 🚀 Usage

The following gives a shallow overview on `aigverse`. Detailed documentation and examples are available at
[ReadTheDocs](https://aigverse.readthedocs.io/).

### 🏗️ Basic Example: Creating an AIG

In `aigverse`, you can create a simple And-Inverter Graph (AIG) and manipulate it using various logic operations.

```python
from aigverse import Aig

# Create a new AIG network
aig = Aig()

# Create primary inputs
x1 = aig.create_pi()
x2 = aig.create_pi()

# Create logic gates
f_and = aig.create_and(x1, x2)  # AND gate
f_or = aig.create_or(x1, x2)  # OR gate

# Create primary outputs
aig.create_po(f_and)
aig.create_po(f_or)

# Print the size of the AIG network
print(f"AIG Size: {aig.size()}")
```

Note that all primary inputs (PIs) must be created before any logic gates.

### 🔍 Iterating over AIG Nodes

You can iterate over all nodes in the AIG, or specific subsets like the primary inputs or only logic nodes (gates).

```python
# Iterate over all nodes in the AIG
for node in aig.nodes():
    print(f"Node: {node}")

# Iterate only over primary inputs
for pi in aig.pis():
    print(f"Primary Input: {pi}")

# Iterate only over logic nodes (gates)
for gate in aig.gates():
    print(f"Gate: {gate}")

# Iterate over the fanins of a node
n_and = aig.get_node(f_and)
for fanin in aig.fanins(n_and):
    print(f"Fanin of {n_and}: {fanin}")
```

### 📏 Depth and Level Computation

You can compute the depth of the AIG network and the level of each node. Depth information is useful for estimating the
critical path delay of a respective circuit.

```python
from aigverse import DepthAig

depth_aig = DepthAig(aig)
print(f"Depth: {depth_aig.num_levels()}")
for node in aig.nodes():
    print(f"Level of {node}: {depth_aig.level(node)}")
```

### 🕸️ AIGs with Fanout Information

If needed, you can retrieve the fanouts of AIG nodes as well:

```python
from aigverse import FanoutAig

fanout_aig = FanoutAig(aig)
n_and = aig.get_node(f_and)
# Iterate over the fanouts of a node
for fanout in fanout_aig.fanouts(n_and):
    print(f"Fanout of node {n_and}: {fanout}")
```

### 🔄 Sequential AIGs

`aigverse` also supports sequential AIGs, which are AIGs with registers.

```python
from aigverse import SequentialAig

seq_aig = SequentialAig()
x1 = seq_aig.create_pi()  # Regular PI
x2 = seq_aig.create_ro()  # Register output (sequential PI)

f_and = seq_aig.create_and(x1, x2)  # AND gate

seq_aig.create_ri(f_and)  # Register input (sequential PO)

print(seq_aig.registers())  # Prints the association of registers
```

It is to be noted that the construction of sequential AIGs comes with some caveats:

1. All register outputs (ROs) must be created after all primary inputs (PIs).
2. All register inputs (RIs) must be created after all primary outputs (POs).
3. As for regular AIGs, all PIs and ROs must be created before any logic gates.

### ⚡ Logic Optimization

You can optimize AIGs using various algorithms. For example, you can perform _resubstitution_ to simplify logic using
shared divisors. Similarly, _refactoring_ collapses maximal fanout-free cones (MFFCs) into truth tables and resynthesizes
them into new structures. Cut _rewriting_ optimizes the AIG by replacing cuts with improved ones from a pre-computed NPN
database. Finally, _balancing_ performs (E)SOP factoring to minimize the number of levels in the AIG.

```python
from aigverse import aig_resubstitution, sop_refactoring, aig_cut_rewriting, balancing

# Clone the AIG network for size comparison
aig_clone = aig.clone()

# Optimize the AIG with several optimization algorithms
for optimization in [aig_resubstitution, sop_refactoring, aig_cut_rewriting, balancing]:
    optimization(aig)

# Print the size of the unoptimized and optimized AIGs
print(f"Original AIG Size:  {aig_clone.size()}")
print(f"Optimized AIG Size: {aig.size()}")
```

### ✅ Equivalence Checking

Equivalence of AIGs (e.g., after optimization) can be checked using SAT-based equivalence checking.

```python
from aigverse import equivalence_checking

# Perform equivalence checking
equiv = equivalence_checking(aig1, aig2)

if equiv:
    print("AIGs are equivalent!")
else:
    print("AIGs are NOT equivalent!")
```

### 📄 File Format Support

You can read and write AIGs in various file formats, including (ASCII) [AIGER](https://fmv.jku.at/aiger/), gate-level
Verilog and PLA.

#### ✏️ Writing

```python
from aigverse import write_aiger, write_verilog, write_dot

# Write an AIG network to an AIGER file
write_aiger(aig, "example.aig")
# Write an AIG network to a Verilog file
write_verilog(aig, "example.v")
# Write an AIG network to a DOT file
write_dot(aig, "example.dot")
```

#### 👓 Parsing

```python
from aigverse import (
    read_aiger_into_aig,
    read_ascii_aiger_into_aig,
    read_verilog_into_aig,
    read_pla_into_aig,
)

# Read AIGER files into AIG networks
aig1 = read_aiger_into_aig("example.aig")
aig2 = read_ascii_aiger_into_aig("example.aag")
# Read a Verilog file into an AIG network
aig3 = read_verilog_into_aig("example.v")
# Read a PLA file into an AIG network
aig4 = read_pla_into_aig("example.pla")
```

Additionally, you can read AIGER files into sequential AIGs using `read_aiger_into_sequential_aig` and
`read_ascii_aiger_into_sequential_aig`.

### 🥒 `pickle` Support

AIGs support Python's `pickle` protocol, allowing you to serialize and deserialize AIG objects for persistent storage or
interface with data science or machine learning workflows.

```python
import pickle

with open("aig.pkl", "wb") as f:
    pickle.dump(aig, f)

with open("aig.pkl", "rb") as f:
    unpickled_aig = pickle.load(f)
```

You can also pickle multiple AIGs at once by storing them in a tuple or list.

### 🧠 Machine Learning Integration

With the `adapters` extra, you can convert an AIG to a [NetworkX](https://networkx.org/) directed graph, enabling
visualization and use with graph-based ML tools:

```python
import aigverse.adapters

G = aig.to_networkx(levels=True, fanouts=True, node_tts=True)
```

Graph, node, and edge attributes provide logic, level, fanout, and function information for downstream ML or
visualization tasks.

For more details and examples, see the
[machine learning integration documentation](https://aigverse.readthedocs.io/en/latest/machine_learning.html).

### 🔢 Truth Tables

Small Boolean functions can be efficiently represented using truth tables. `aigverse` enables the creation and
manipulation of truth tables by wrapping a portion of the [kitty](https://github.com/msoeken/kitty) library.

#### 🎉 Creation

```python
from aigverse import TruthTable

# Initialize a truth table with 3 variables
tt = TruthTable(3)
# Create a truth table from a hex string representing the MAJ function
tt.create_from_hex_string("e8")
```

#### 🔧 Manipulation

```python
# Flip each bit in the truth table
for i in range(tt.num_bits()):
    print(f"Flipping bit {int(tt.get_bit(i))}")
    tt.flip_bit(i)

# Print a binary string representation of the truth table
print(tt.to_binary())

# Clear the truth table
tt.clear()

# Check if the truth table is constant 0
print(tt.is_const0())
```

#### 🔣 Symbolic Simulation of AIGs

```python
from aigverse import simulate, simulate_nodes

# Obtain the truth table of each AIG output
tts = simulate(aig)

# Print the truth tables
for i, tt in enumerate(tts):
    print(f"PO{i}: {tt.to_binary()}")

# Obtain the truth tables of each node in the AIG
n_to_tt = simulate_nodes(aig)

# Print the truth tables of each node
for node, tt in n_to_tt.items():
    print(f"Node {node}: {tt.to_binary()}")
```

#### 📃 Exporting as Lists or NumPy Arrays

For machine learning applications, it is often useful to convert truth tables into standard data structures like Python
lists or NumPy arrays. Since `TruthTable` objects are iterable, conversion is straightforward.

```python
import numpy as np

# Export to a list
tt_list = list(tt)

# Export to NumPy arrays
tt_np_bool = np.array(tt)
tt_np_int = np.array(tt, dtype=np.int32)
tt_np_float = np.array(tt, dtype=np.float64)
```

#### 🥒 `pickle` Support

Truth tables also support Python's `pickle` protocol, allowing you to serialize and deserialize them.

```python
import pickle

with open("tt.pkl", "wb") as f:
    pickle.dump(tt, f)

with open("tt.pkl", "rb") as f:
    unpickled_tt = pickle.load(f)
```

## 🙌 Contributing

Contributions are welcome! If you'd like to contribute to `aigverse`, please see the
[contribution guide](https://aigverse.readthedocs.io/en/latest/contributing.html). I appreciate feedback and suggestions
for improving the library.

## 💼 Support and Consulting

`aigverse` is and will always be a free, open-source library. If you or your organization require dedicated support,
specific new features, or integration of `aigverse` into your projects, professional consulting services are available.
This is a great way to get the features you need while also supporting the ongoing maintenance and development of the
library.

For inquiries, please reach out to [@marcelwa](https://github.com/marcelwa/). More information can be found in the
[documentation](https://aigverse.readthedocs.io/en/latest/support.html).

## 📜 License

`aigverse` is available under the MIT License.
