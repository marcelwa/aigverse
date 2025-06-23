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

# And-Inverter Graphs (AIGs)

The central data structure for working with And-Inverter Graphs (AIGs) in aigverse is the {py:class}`~aigverse.Aig` class.
It enables efficient representation and manipulation of logic circuits in a form that's well-suited for optimization and verification tasks.

The following will demonstrate how to work with the {py:class}`~aigverse.Aig` class in Python.

:::{note}
AIGs (And-Inverter Graphs) are a compact representation of Boolean functions using only AND gates and inverters (NOT gates). They are widely used in formal verification, hardware design, and optimization tasks.
:::

## Quickstart

The following code snippet demonstrates how to create a simple AIG representing basic logic operations.

```{code-cell} ipython3
from aigverse import Aig

# Create a new AIG network
aig = Aig()

# Create primary inputs
x1 = aig.create_pi()
x2 = aig.create_pi()

# Create logic gates
f_and = aig.create_and(x1, x2)  # AND gate
f_or = aig.create_or(x1, x2)    # OR gate

# Create primary outputs
aig.create_po(f_and)
aig.create_po(f_or)

# Print the size of the AIG network
print(f"AIG Size: {aig.size()}")
```

:::{note}
All primary inputs (PIs) must be created before any logic gates.
:::

## Basic AIG Concepts

An AIG consists of nodes and signals:

- **Nodes** represent either primary inputs, constants, or logic gates
- **Signals** reference nodes, possibly with complementation (inversion)

```{code-cell} ipython3
# Create a new AIG
aig = Aig()

# Create a constant (false)
const0 = aig.get_constant(False)
print(f"Constant 0: {const0}")

# Create primary inputs
a = aig.create_pi()
b = aig.create_pi()
print(f"Input a: {a}")
print(f"Input b: {b}")

# Create an AND gate and its complement (NAND)
and_gate = aig.create_and(a, b)
nand_gate = aig.create_not(and_gate)
print(f"AND gate: {and_gate}")
print(f"NAND gate: {nand_gate}")

# Get the node from a signal
node = aig.get_node(and_gate)
print(f"Node of AND gate: {node}")

# Check if a signal is complemented
is_complemented = aig.is_complemented(nand_gate)
print(f"Is NAND complemented? {is_complemented}")
```

### Exploring AIG Structure

You can iterate over all nodes in the AIG, or specific subsets like primary inputs or logic gates.

```{code-cell} ipython3
# Create a sample AIG
aig = Aig()
a = aig.create_pi()
b = aig.create_pi()
c = aig.create_pi()
f1 = aig.create_and(a, b)
f2 = aig.create_or(f1, c)
aig.create_po(f2)

# Iterate over all nodes in the AIG
print("All nodes:")
for node in aig.nodes():
    print(f"  Node: {node}")

# Iterate only over primary inputs
print("\nPrimary inputs:")
for pi in aig.pis():
    print(f"  PI: {pi}")

# Iterate only over logic gates
print("\nLogic gates:")
for gate in aig.gates():
    print(f"  Gate: {gate}")

# Iterate over the fanins of a node
print("\nFanins of the OR gate:")
or_node = aig.get_node(f2)
for fanin in aig.fanins(or_node):
    print(f"  Fanin: {fanin}")
```

### Building Complex Functions

AIGs support a variety of logic functions beyond just AND gates. Internally, those are decomposed into multiple nodes.

```{code-cell} ipython3
aig = Aig()
a = aig.create_pi()
b = aig.create_pi()
c = aig.create_pi()

# Create various logic functions
and_gate = aig.create_and(a, b)
or_gate = aig.create_or(a, b)
xor_gate = aig.create_xor(a, b)
maj_gate = aig.create_maj(a, b, c)  # Majority function (a&b | a&c | b&c)
ite_gate = aig.create_ite(a, b, c)  # If-then-else: a ? b : c

# Add outputs
aig.create_po(and_gate)
aig.create_po(or_gate)
aig.create_po(xor_gate)
aig.create_po(maj_gate)
aig.create_po(ite_gate)

# Print statistics
print(f"AIG Size: {aig.size()}")
print(f"Number of gates: {aig.num_gates()}")
print(f"Number of primary inputs: {aig.num_pis()}")
print(f"Number of primary outputs: {aig.num_pos()}")
```

## Symbolic Simulation

For simulating the truth tables of AIGs, see the [Truth Tables](truth_tables.md) documentation.
The {py:func}`~aigverse.simulate` and {py:func}`~aigverse.simulate_nodes` functions allow you to obtain truth tables for
outputs and internal nodes of an AIG, respectively.

## AIG Views

AIG views provide alternative representations of AIGs for specific tasks, such as depth computation or fanout analysis.
These views can be layered on top of the original AIG, allowing you to work with the same underlying structure while
adding additional functionality.

### Depth and Level Computation

The depth of an AIG network represents the longest path from any input to any output, which corresponds to the critical
path delay in a circuit. You can compute the depth and level of each node using the {py:class}`~aigverse.DepthAig`
class.

```{code-cell} ipython3
from aigverse import DepthAig

# Create a sample AIG
aig = Aig()
a = aig.create_pi()
b = aig.create_pi()
c = aig.create_pi()
f1 = aig.create_and(a, b)
f2 = aig.create_and(f1, c)
aig.create_po(f2)

# Create a depth view of the AIG
depth_aig = DepthAig(aig)

# Get the depth of the AIG
print(f"Depth of AIG: {depth_aig.num_levels()}")

# Print the level of each node
print("\nLevel of each node:")
for node in aig.nodes():
    print(f"  Node {node}: Level {depth_aig.level(node)}")

# Check which nodes are on the critical path
print("\nNodes on critical path:")
for node in aig.nodes():
    if depth_aig.is_on_critical_path(node):
        print(f"  Node {node}")
```

### AIGs with Fanout Information

Fanouts of AIG nodes can be collected using {py:class}`~aigverse.FanoutAig`.

```{code-cell} ipython3
from aigverse import FanoutAig

# Create a sample AIG
aig = Aig()
x1 = aig.create_pi()
x2 = aig.create_pi()
x3 = aig.create_pi()

# Create AND gates
n4 = aig.create_and(x1, x2)
n5 = aig.create_and(n4, x3)
n6 = aig.create_and(n4, n5)
# Create primary outputs
aig.create_po(n6)

fanout_aig = FanoutAig(aig)
print("\nFanout nodes of n4:")
for node in fanout_aig.fanouts(aig.get_node(n4)):
    print(f"  Node {node}")
```

### Sequential AIGs

{py:class}`~aigverse.SequentialAig`s extend standard AIGs to include registers, which allow modeling sequential circuits
with memory elements.

```{code-cell} ipython3
from aigverse import SequentialAig

# Create a sequential AIG
seq_aig = SequentialAig()

# Create a primary input and a register output
x = seq_aig.create_pi()       # Regular PI
r = seq_aig.create_ro()       # Register output (sequential PI)

# Create logic
f_and = seq_aig.create_and(x, r)   # AND gate

# Create a primary output and a register input
seq_aig.create_po(f_and)      # Regular PO
seq_aig.create_ri(f_and)      # Register input (sequential PO)

# Print information about the sequential AIG
print(f"Number of PIs: {seq_aig.num_pis()}")
print(f"Number of POs: {seq_aig.num_pos()}")
print(f"Number of registers: {seq_aig.num_registers()}")

# Get the register associations (RI-RO pairs)
print("\nRegister associations:")
registers = seq_aig.registers()
for reg in registers:
    ri, ro = reg
    print(f"  RI: {ri} -> RO: {ro}")
```

:::{note}
When creating sequential AIGs, follow these rules:

1. All register outputs (ROs) must be created after all primary inputs (PIs).
2. All register inputs (RIs) must be created after all primary outputs (POs).
3. As with regular AIGs, all PIs and ROs must be created before any logic gates.
   :::

## File I/O

AIGs can be read from and written to various file formats.

```{code-cell} ipython3
from aigverse import (
   write_aiger,
   write_verilog,
   write_dot,
   read_aiger_into_aig,
   read_verilog_into_aig,
   read_pla_into_aig
)

# Create a sample AIG
aig = Aig()
a = aig.create_pi()
b = aig.create_pi()
f = aig.create_and(a, b)
aig.create_po(f)

# Write to AIGER format
write_aiger(aig, "example.aig")

# Write to Verilog format
write_verilog(aig, "example.v")

# Write to DOT format
write_dot(aig, "example.dot")

# Read from AIGER format
read_aig = read_aiger_into_aig("example.aig")

# Read from Verilog format
read_verilog_aig = read_verilog_into_aig("example.v")

# Read from PLA format
read_pla_aig = read_pla_into_aig("example.pla")

print(f"Original AIG size: {aig.size()}")
print(f"Read AIGER AIG size: {read_aig.size()}")
print(f"Read Verilog AIG size: {read_verilog_aig.size()}")
print(f"Read PLA AIG size: {read_pla_aig.size()}")
```

:::{note}
The gate-level Verilog file support constitutes a very small subset of the Verilog standard, similar
in extent to what ABC supports. For more information, see the
[`lorina` parser](https://lorina.readthedocs.io/en/latest/verilog.html) used by this project.
:::

## Index Lists

Alternatively, index lists provide a compact, serialization-friendly representation of an AIG's structure as a flat
list of integers. This is useful for ML pipelines, dataset generation, or exporting AIGs for use in environments where
fixed-size numeric arrays are required.

```{code-cell} ipython3
from aigverse import to_index_list, to_aig, AigIndexList

# Create a sample AIG
aig = Aig()
a = aig.create_pi()
b = aig.create_pi()
c = aig.create_pi()
d = aig.create_pi()
t0 = aig.create_and(a, b)
t1 = aig.create_and(~c, ~d)
t2 = aig.create_xor(t0, t1)
aig.create_po(t2)

# Convert an AIG to an index list
indices = to_index_list(aig)

# Convert an index list back to an AIG
aig2 = to_aig(indices)

# Convert to a Python list
indices = [int(i) for i in indices]
print(indices)
```

The first three entries encode number of PIs, number of POs, and number of gates, respectively. In the example above,
those are `4`, `1`, and `5`. Successive pairs of indices refer to the fanins signals of nodes. Each fanin exists in two
polarities: negated = odd index, and non-negated = even index. In the example, `2` and `4` refer to the non-negated
signals originating from PIs `1` and `2`. These form the first AND gate. The subsequent `7` and `9` are odd, hence,
negated. If the first index is lower than the second, an AND gate is encoded. Otherwise, it is an XOR gate. The final
indices of the list refer to the PO signals. It must be ensured that they match the encoded number of POs.

For more information on the index list format, see
[`mockturtle`'s documentation](https://mockturtle.readthedocs.io/en/latest/utils/util_data_structures.html#index-list).

## `pickle` Support

AIGs support Python's [`pickle`](https://docs.python.org/3/library/pickle.html) protocol, allowing you to serialize and
deserialize AIG objects for persistent storage. This is useful for saving intermediate results, sharing AIGs between
processes, quickly restoring previously computed networks, or interface with data science or machine learning workflows.

```{code-cell} ipython3
import pickle

# Save AIG to a file using pickle
with open("aig.pkl", "wb") as f:
    pickle.dump(aig, f)

# Load the AIG from the pickle file
with open("aig.pkl", "rb") as f:
    unpickled_aig = pickle.load(f)
```

You can also pickle and unpickle multiple AIGs at once by storing them in a tuple or list.

```{code-cell} ipython3
aig1 = Aig()
a1 = aig1.create_pi()
b1 = aig1.create_pi()
f1 = aig1.create_and(a1, b1)
aig1.create_po(f1)

aig2 = Aig()
a2 = aig2.create_pi()
b2 = aig2.create_pi()
f2 = aig2.create_or(a2, b2)
aig2.create_po(f2)

# Pickle both AIGs together
with open("aigs.pkl", "wb") as f:
    pickle.dump((aig1, aig2), f)

# Unpickle them
with open("aigs.pkl", "rb") as f:
    unpickled_aig1, unpickled_aig2 = pickle.load(f)
```
