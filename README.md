# aigverse: A Python Library for Logic Networks, Synthesis, and Optimization

[![Python Bindings](https://img.shields.io/github/actions/workflow/status/marcelwa/aigverse/aigverse-pypi-deployment.yml?label=Bindings&logo=python&style=flat-square)](https://github.com/marcelwa/aigverse/actions/workflows/aigverse-pypi-deployment.yml)
[![License](https://img.shields.io/github/license/marcelwa/aigverse?label=License&style=flat-square)](https://github.com/marcelwa/aigverse/blob/main/LICENSE)
[![PyPI](https://img.shields.io/static/v1?label=PyPI&message=aigverse&logo=pypi&color=informational&style=flat-square)](https://pypi.org/project/aigverse/)
[![Release](https://img.shields.io/github/v/release/marcelwa/aigverse?label=aigverse&style=flat-square)](https://github.com/marcelwa/aigverse/releases)

> [!Important]
> This project is still in the early stages of development. The API is subject to change, and some features may not be
> fully implemented. I appreciate your patience and understanding as work to improve the library continues.

`aigverse` is a Python framework designed to bridge the gap between logic synthesis and AI/ML applications. It allows
you to represent and manipulate logic circuits efficiently, making it easier to integrate logic synthesis tasks into
machine learning pipelines. By leveraging the
powerful [EPFL Logic Synthesis Libraries](https://arxiv.org/abs/1805.05121),
particularly [mockturtle](https://github.com/lsils/mockturtle), `aigverse` provides a high-level Python interface to
state-of-the-art algorithms for And-Inverter Graph (AIG) manipulation and logic synthesis, widely used in formal
verification, hardware design, and optimization tasks.

## Features

- **Efficient Logic Representation**: Use And-Inverter Graphs (AIGs) to model and manipulate logic circuits in Python.
- **File Format Support**: Read and write AIGER, Verilog, Bench, PLA, ... files for interoperability with other logic
  synthesis tools.
- **C++ Backend**: Leverage the performance of the EPFL Logic Synthesis Libraries for fast logic synthesis and
  optimization.
- **High-Level API**: Simplify logic synthesis tasks with a Pythonic interface for AIG manipulation and optimization.
- **Integration with Machine Learning**: Convenient integration with popular data science libraries.

## Motivation

As AI and machine learning (ML) increasingly impact hardware design automation, there's a growing need for tools that
integrate logic synthesis with ML workflows. `aigverse` provides a Python-friendly interface for logic synthesis, making
it easier to develop applications that blend both AI/ML and traditional circuit synthesis techniques. With `aigverse`,
you can parse, manipulate, and optimize logic circuits directly from Python. Eventually, we aim to provide seamless
integration with popular ML libraries, enabling the development of novel AI-driven synthesis and optimization tools.

## Installation

`aigverse` requires Python 3.8+ and is built using the EPFL Logic Synthesis Libraries
with [pybind11](https://github.com/pybind/pybind11). To install `aigverse`:

```bash
pip install aigverse
```

## Usage

### Basic Example: Creating an AIG

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

### Iterating over AIG Nodes

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

### Depth and Level Computation

You can compute the depth of the AIG network and the level of each node. Depth information is useful for estimating the
critical path delay of a respective circuit.

```python
from aigverse import DepthAig

depth_aig = DepthAig(aig)
print(f"Depth: {depth_aig.num_levels()}")
for node in aig.nodes():
    print(f"Level of {node}: {depth_aig.level(node)}")
```

### Logic Optimization

You can optimize AIGs using various algorithms. For example, you can perform resubstitution to simplify logic using
shared divisors. Similarly, refactoring collapses maximmal fanout-free cones (MFFCs) into truth tables and resynthesizes
them into new structures. Cut rewriting optimizes the AIG by replacing cuts with improved ones from a pre-computed NPN
database.

```python
from aigverse import aig_resubstitution, sop_refactoring, aig_cut_rewriting

# Clone the AIG network for size comparison
aig_clone = aig.clone()

# Optimize the AIG with several optimization algorithms
for optimization in [aig_resubstitution, sop_refactoring, aig_cut_rewriting]:
    optimization(aig)

# Print the size of the unoptimized and optimized AIGs
print(f"Original AIG Size:  {aig_clone.size()}")
print(f"Optimized AIG Size: {aig.size()}")
```

### Equivalence Checking

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

### AIGER Files

You can read and write (ASCII) [AIGER](https://fmv.jku.at/aiger/) files.

#### Parsing

```python
from aigverse import read_aiger_into_aig, read_ascii_aiger_into_aig

# Read AIGER files into AIG networks
aig1 = read_aiger_into_aig("example.aig")
aig2 = read_ascii_aiger_into_aig("example.aag")

# Print the size of the AIGs
print(f"AIG Size: {aig1.size()}")
print(f"AIG Size: {aig2.size()}")
```

#### Writing

```python
from aigverse import write_aiger

# Write an AIG network to an AIGER file
write_aiger(aig, "example.aig")
```

### Exporting Edge Lists

You can export the AIG as an edge list, which is useful for integration with graph libraries like NetworkX.

```python
from aigverse import to_edge_list

# Export the AIG as an edge list
edges = to_edge_list(aig)
print(edges)

# Convert to list of tuples
edges = [(e.source, e.target, e.weight) for e in edges]
```

### Truth Tables

Small Boolean functions can be efficiently represented using truth tables. `aigverse` enables the creation and
manipulation of truth tables by wrapping a portion of the [kitty](https://github.com/msoeken/kitty) library.

#### Creation

```python
from aigverse import TruthTable

# Initialize a truth table with 3 variables
tt = TruthTable(3)
# Create a truth table from a hex string representing the MAJ function
tt.create_from_hex_string("e8")
```

#### Manipulation

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

#### Symbolic Simulation of AIGs

```python
from aigverse import simulate

# Obtain the truth table of each AIG output
tts = simulate(aig)

# Print the truth tables
for i, tt in enumerate(tts):
    print(f"PO{i}: {tt.to_binary()}")
```

## Contributing

Contributions are welcome! If you'd like to contribute to `aigverse`, please submit a pull request or open an issue. If
appreciate feedback and suggestions for improving the library.

## License

`aigverse` is available under the MIT License.
