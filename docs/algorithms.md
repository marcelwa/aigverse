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
from aigverse import read_aiger_into_aig

# Load the i10 benchmark circuit - a real-world example
aig = read_aiger_into_aig("examples/i10.aig")

# Print statistics about the loaded circuit
print(f"i10 benchmark:")
print(f"  I/O: {aig.num_pis()}/{aig.num_pos()}")
print(f"  AND gates: {aig.num_gates()}")
```

### Resubstitution

Resubstitution identifies portions of logic that can be expressed using existing signals in the network. This technique is particularly effective at identifying and eliminating redundant logic.

```{code-cell} ipython3
from aigverse import aig_resubstitution

# Clone the AIG for comparison
aig_resub = aig.clone()

# Apply resubstitution
aig_resubstitution(aig_resub, window_size=12)

print(f"Original AND gates: {aig.num_gates()}")
print(f"After resubstitution: {aig_resub.num_gates()} AND gates")
print(f"Reduction: {aig.num_gates() - aig_resub.num_gates()} gates ({(aig.num_gates() - aig_resub.num_gates()) / aig.num_gates() * 100:.2f}%)")
```

### Sum-of-Products Refactoring

SOP (Sum of Products) refactoring collapses parts of the AIG into truth tables, then re-synthesizes those portions using Sum-of-Products representations. This can find more efficient implementations for complex logic functions.

```{code-cell} ipython3
from aigverse import sop_refactoring

# Clone the AIG for comparison
aig_refactor = aig.clone()

# Apply SOP refactoring
sop_refactoring(aig_refactor, use_reconvergence_cut=True)

print(f"Original AND gates: {aig.num_gates()}")
print(f"After SOP refactoring: {aig_refactor.num_gates()} AND gates")
print(f"Reduction: {aig.num_gates() - aig_refactor.num_gates()} gates ({(aig.num_gates() - aig_refactor.num_gates()) / aig.num_gates() * 100:.2f}%)")
```

### Cut Rewriting

Cut rewriting identifies small subgraphs (cuts) in the AIG and replaces them with pre-computed optimal implementations from a library. This technique leverages NPN-equivalence classes to find the best possible implementation for each cut.

```{code-cell} ipython3
from aigverse import aig_cut_rewriting

# Clone the AIG for comparison
aig_rewrite = aig.clone()

# Apply cut rewriting
aig_cut_rewriting(aig_rewrite, cut_size=4)

print(f"Original AND gates: {aig.num_gates()}")
print(f"After cut rewriting: {aig_rewrite.num_gates()} AND gates")
print(f"Reduction: {aig.num_gates() - aig_rewrite.num_gates()} gates ({(aig.num_gates() - aig_rewrite.num_gates()) / aig.num_gates() * 100:.2f}%)")
```

### Balancing

Balancing performs (E)SOP factoring to minimize the number of levels in the AIG.

```{code-cell} ipython3
from aigverse import balancing, DepthAig

# Clone the AIG for comparison
aig_balance = aig.clone()

# Apply balancing
balancing(aig_balance, rebalance_function="sop")

# Compute depth
original_depth = DepthAig(aig).num_levels()
balanced_depth = DepthAig(aig_balance).num_levels()

print(f"Original depth: {original_depth} levels")
print(f"After balancing: {balanced_depth} levels")
print(f"Reduction in depth: {original_depth - balanced_depth} levels ({(original_depth - balanced_depth) / original_depth * 100:.2f}%)")
```

### Combining Optimization Techniques

For best results, optimization techniques are typically applied in combination, often in multiple passes. The order of application can significantly impact the final result.

```{code-cell} ipython3
# Apply optimization techniques in sequence
aig_opt = aig.clone()

# First pass
aig_resubstitution(aig_opt)
sop_refactoring(aig_opt)
aig_cut_rewriting(aig_opt)

# Second pass
aig_resubstitution(aig_opt)
sop_refactoring(aig_opt)

print(f"\nTotal optimization results:")
print(f"- Original: {aig.num_gates()} AND gates")
print(f"- Optimized: {aig_opt.num_gates()} AND gates")
print(f"- Total reduction: {aig.num_gates() - aig_opt.num_gates()} gates ({(aig.num_gates() - aig_opt.num_gates()) / aig.num_gates() * 100:.2f}%)")
```

## Equivalence Checking

Equivalence checking algorithms verify that two logic networks implement the same function, which is especially important after performing optimizations.

```{code-cell} ipython3
from aigverse import equivalence_checking

# Verify that our optimized circuit from the previous section maintains functional equivalence
are_equivalent = equivalence_checking(aig, aig_opt)
print(f"\nOriginal and optimized benchmark circuits are equivalent: {are_equivalent}")
print(f"This confirms our optimization preserved the circuit's functionality while reducing")
print(f"the gate count from {aig.num_gates()} to {aig_opt.num_gates()} AND gates.")
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
for i, (x, f) in enumerate(zip(inputs, outputs)):
    print(f"  Input: {x}, Output: {f}")
```
