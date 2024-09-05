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
for fanin in aig.fanins(f_and):
    print(f"Fanin of {f_and}: {fanin}")
```

### Parse AIGER Files

You can read and write AIGER files using `aigverse`. Here's an example of parsing an AIGER file as an AIG network.

```python
from aigverse import read_aiger_into_aig

# Read an AIGER file into an AIG network
aig = read_aiger_into_aig("example.aig")

# Print the size of the AIG network
print(f"AIG Size: {aig.size()}")
```

## Contributing

Contributions are welcome! If you’d like to contribute to `aigverse`, please submit a pull request or open an issue. If
appreciate feedback and suggestions for improving the library.

## License

`aigverse` is available under the MIT License.

