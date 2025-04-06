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

# Algorithms

This section covers the various algorithms available in aigverse for working with And-Inverter Graphs (AIGs) and other logic representations. These algorithms enable simulation, optimization, and verification of logic networks.

## Simulation

Simulation algorithms allow you to evaluate the outputs of a logic network for all possible input combinations, effectively generating truth tables for the network's outputs and internal nodes.

### Functional Simulation

For simulating AIGs with truth tables, the {py:func}`~aigverse.simulate` and {py:func}`~aigverse.simulate_nodes` functions allow you to obtain truth tables for outputs and internal nodes of an AIG.

```{code-cell} ipython3
from aigverse import Aig, simulate, simulate_nodes

# Create a sample AIG
aig = Aig()
a = aig.create_pi()
b = aig.create_pi()
f_and = aig.create_and(a, b)
f_or = aig.create_or(a, b)
aig.create_po(f_and)
aig.create_po(f_or)

# Simulate the outputs
output_tts = simulate(aig)

# Print the truth tables
print("Truth tables of outputs:")
for i, tt in enumerate(output_tts):
    print(f"  Output {i}: {tt.to_binary()}")

# Simulate all nodes
node_tts = simulate_nodes(aig)

# Print the truth table of each node
print("\nTruth tables of nodes:")
for node, tt in node_tts.items():
    print(f"  Node {node}: {tt.to_binary()}")
```

## Optimization

AIG optimization aims to reduce the number of AND gates and inverters in a circuit while maintaining its logical functionality. Different optimization techniques target various aspects of the AIG structure.

### Basic Optimization Workflow

The typical optimization workflow involves:

1. Creating or loading an AIG
2. Applying one or more optimization algorithms
3. Verifying correctness through equivalence checking

```{code-cell} ipython3
from aigverse import Aig

# Create a sample AIG with redundancy
aig = Aig()
a = aig.create_pi()
b = aig.create_pi()
c = aig.create_pi()
d = aig.create_pi()

# Create a redundant circuit
t1 = aig.create_and(a, b)
t2 = aig.create_and(c, d)
t3 = aig.create_and(a, b)  # Identical to t1
t4 = aig.create_or(t1, t2)
t5 = aig.create_or(t3, t2)  # Redundant with t4
aig.create_po(t4)
aig.create_po(t5)

print(f"Original AIG size: {aig.size()}")
```

### Resubstitution

Resubstitution identifies portions of logic that can be expressed using existing signals in the network. This technique is particularly effective at identifying and eliminating redundant logic.

```{code-cell} ipython3
from aigverse import aig_resubstitution

# Clone the AIG for comparison
aig_resub = aig.clone()

# Apply resubstitution
aig_resubstitution(aig_resub)

print(f"Original size: {aig.size()}")
print(f"After resubstitution: {aig_resub.size()}")
```

### Sum-of-Products Refactoring

SOP (Sum of Products) refactoring collapses parts of the AIG into truth tables, then re-synthesizes those portions using Sum-of-Products representations. This can find more efficient implementations for complex logic functions.

```{code-cell} ipython3
from aigverse import sop_refactoring

# Clone the AIG for comparison
aig_refactor = aig.clone()

# Apply SOP refactoring
sop_refactoring(aig_refactor)

print(f"Original size: {aig.size()}")
print(f"After refactoring: {aig_refactor.size()}")
```

### Cut Rewriting

Cut rewriting identifies small subgraphs (cuts) in the AIG and replaces them with pre-computed optimal implementations from a library. This technique leverages NPN-equivalence classes to find the best possible implementation for each cut.

```{code-cell} ipython3
from aigverse import aig_cut_rewriting

# Clone the AIG for comparison
aig_rewrite = aig.clone()

# Apply cut rewriting
aig_cut_rewriting(aig_rewrite)

print(f"Original size: {aig.size()}")
print(f"After cut rewriting: {aig_rewrite.size()}")
```

### Combining Optimization Techniques

For best results, optimization techniques are typically applied in combination, often in multiple passes. The order of application can significantly impact the final result.

```{code-cell} ipython3
# Apply all optimization techniques in sequence
aig_opt = aig.clone()

# First pass
aig_resubstitution(aig_opt)
sop_refactoring(aig_opt)
aig_cut_rewriting(aig_opt)

# Second pass
aig_resubstitution(aig_opt)
sop_refactoring(aig_opt)

print(f"Original size: {aig.size()}")
print(f"After combined optimization: {aig_opt.size()}")
```

## Equivalence Checking

Equivalence checking algorithms verify that two logic networks implement the same function, which is especially important after performing optimizations.

```{code-cell} ipython3
from aigverse import equivalence_checking

# Create a sample AIG implementing a & b
aig1 = Aig()
a = aig1.create_pi()
b = aig1.create_pi()
f1 = aig1.create_and(a, b)
aig1.create_po(f1)

# Create another AIG implementing the same function using De Morgan's law
# !((!a) | (!b)) = a & b
aig2 = Aig()
a = aig2.create_pi()
b = aig2.create_pi()
not_a = aig2.create_not(a)
not_b = aig2.create_not(b)
or_gate = aig2.create_or(not_a, not_b)
f2 = aig2.create_not(or_gate)
aig2.create_po(f2)

# Check if the circuits are equivalent
are_equivalent = equivalence_checking(aig1, aig2)
print(f"AIGs are equivalent: {are_equivalent}")
```

This is particularly useful for verifying that optimized circuits maintain the same functionality as the original:

```{code-cell} ipython3
# Create a sample AIG
aig = Aig()
a = aig.create_pi()
b = aig.create_pi()
c = aig.create_pi()

t1 = aig.create_and(a, b)
t2 = aig.create_and(t1, c)
aig.create_po(t2)

# Clone and optimize
aig_opt = aig.clone()
aig_resubstitution(aig_opt)

# Check equivalence
are_equivalent = equivalence_checking(aig, aig_opt)
print(f"Original and optimized AIGs are equivalent: {are_equivalent}")
```

## Machine Learning Integration

For machine learning applications, it's often useful to convert truth tables to more common data formats:

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
for i, (x, y) in enumerate(zip(inputs, outputs)):
    print(f"  Input: {x}, Output: {y}")
```
