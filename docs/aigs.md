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

## Exploring AIG Structure

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

## Building Complex Functions

AIGs support a variety of logic functions beyond just AND gates.

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

## Depth and Level Computation

The depth of an AIG network represents the longest path from any input to any output, which corresponds to the critical path delay in a circuit. You can compute the depth and level of each node using the {py:class}`~aigverse.DepthAig` class.

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

## AIGs with Fanout Information

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

## Sequential AIGs

Sequential AIGs extend standard AIGs to include registers, which allow modeling sequential circuits with memory elements.

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
from aigverse import write_aiger, read_aiger_into_aig, read_pla_into_aig

# Create a sample AIG
aig = Aig()
a = aig.create_pi()
b = aig.create_pi()
f = aig.create_and(a, b)
aig.create_po(f)

# Write to AIGER format
write_aiger(aig, "example.aig")

# Read from AIGER format
read_aig = read_aiger_into_aig("example.aig")

# Read from PLA format
read_pla_aig = read_pla_into_aig("examples/case.pla")

print(f"Original AIG size: {aig.size()}")
print(f"Read AIG size: {read_aig.size()}")
print(f"Read AIG size: {read_pla_aig.size()}")
```

## Graph Representation

AIGs can be exported as edge lists for integration with graph analysis libraries like NetworkX.

```{code-cell} ipython3
from aigverse import to_edge_list
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import pygraphviz
import matplotlib.pyplot as plt

# Create a sample AIG
aig = Aig()
a = aig.create_pi()
b = aig.create_pi()
c = aig.create_pi()
f1 = aig.create_and(a, b)
f2 = aig.create_or(f1, c)
aig.create_po(f2)

# Get the edge list
edges = to_edge_list(aig)
edge_tuples = [(e.source, e.target, e.weight) for e in edges]

# Create a NetworkX graph
G = nx.DiGraph()
for src, tgt, weight in edge_tuples:
    G.add_edge(src, tgt, weight=weight)

# Plot the graph
plt.figure(figsize=(10, 6))
pos = graphviz_layout(G, prog='dot')
nx.draw(G, pos, with_labels=True, node_color='lightblue',
        node_size=500, arrowsize=20, font_size=12)
labels = {(u, v): data['weight'] for u, v, data in G.edges(data=True)}
nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
plt.title("AIG as a Hierarchical Graph")
plt.show()
```

## Symbolic Simulation

For simulating the truth tables of AIGs, see the [Truth Tables](truth_tables.md) documentation. The {py:func}`~aigverse.simulate` and {py:func}`~aigverse.simulate_nodes` functions allow you to obtain truth tables for outputs and internal nodes of an AIG.
