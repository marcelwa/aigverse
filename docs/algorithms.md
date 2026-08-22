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

This section covers the various algorithms available in aigverse for working with And-Inverter Graphs (AIGs) and other
logic representations. These algorithms enable simulation, optimization, and verification of logic networks.

## Simulation

Simulation algorithms allow you to evaluate the outputs of a logic network for all possible input combinations,
effectively generating truth tables for the network's outputs and internal nodes.

### Functional Simulation

For simulating AIGs with truth tables, the {py:func}`~aigverse.algorithms.simulate` and
{py:func}`~aigverse.algorithms.simulate_nodes` functions allow you to obtain truth tables for outputs and internal nodes of an
AIG.

```{code-cell} ipython3
from aigverse.networks import Aig
from aigverse.algorithms import simulate, simulate_nodes

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

### Sequential Simulation

{py:func}`~aigverse.algorithms.simulate` evaluates the combinational logic exactly once and has no notion of a
register. Handed a {py:class}`~aigverse.networks.SequentialAig` it never assigns the register outputs at all, so
every value downstream of one is meaningless.

{py:func}`~aigverse.algorithms.simulate_sequential` runs the network over a number of clock cycles instead. Every
register starts at its reset value, the combinational logic is evaluated once per cycle, the primary outputs are
recorded, and the register inputs are latched into the register outputs for the next cycle.

A design with no primary inputs runs off its reset state alone. A 4-bit linear-feedback shift register seeded with
`0b0001` walks through all fifteen of its non-zero states before repeating:

```{code-cell} ipython3
from aigverse.algorithms import simulate_sequential
from aigverse.networks import AigRegister, SequentialAig

lfsr = SequentialAig()

state = [lfsr.create_ro() for _ in range(4)]
feedback = lfsr.create_xor(state[3], state[2])

# Primary outputs go in before register inputs: both are combinational outputs of
# the same network, and `po_at` / `ri_at` slice that one list by position.
lfsr.create_po(state[3])

lfsr.create_ri(feedback)
for bit in range(3):
    lfsr.create_ri(state[bit])

# Seed the register chain with 0b0001
for bit in range(4):
    register = AigRegister()
    register.init = 1 if bit == 0 else 0
    lfsr.set_register(bit, register)

result = simulate_sequential(lfsr, 15)

print("output: ", "".join(str(int(cycle[0])) for cycle in result.outputs))
print("cycles: ", result.num_cycles)
print("reset:  ", result.reset_state)
print("final:  ", result.final_state)
```

A full period brings the registers back to their seed, so `final_state` matches `reset_state`.

The result carries two traces, both indexed by clock cycle first: `outputs[cycle][index]` is the value primary
output `index` took in that cycle, and `states[cycle][index]` the value register `index` held while that cycle was
evaluated. The state trace is one entry longer than the output trace, because simulating _n_ cycles crosses _n + 1_
state boundaries:

```{code-cell} ipython3
for cycle, registers in enumerate(result.states):
    print(f"  boundary {cycle:2d}: {''.join(str(int(bit)) for bit in registers)}")
```

Designs with primary inputs are driven by a stimulus, one assignment per cycle. Cycles past the end of it repeat
the last assignment, so a single assignment holds for the whole run:

```{code-cell} ipython3
# A three-stage shift register: what goes in comes out three cycles later
shift = SequentialAig()

data = shift.create_pi()
stages = [shift.create_ro() for _ in range(3)]

shift.create_po(stages[2])

shift.create_ri(data)
shift.create_ri(stages[0])
shift.create_ri(stages[1])

for stage in range(3):
    register = AigRegister()
    register.init = 0
    shift.set_register(stage, register)

# A single pulse on the input, then silence
pulse = simulate_sequential(shift, 6, [[True], [False]])

print("output:", "".join(str(int(cycle[0])) for cycle in pulse.outputs))
```

A register may declare no reset value at all, which is what a fresh
{py:class}`~aigverse.networks.AigRegister` carries and what an AIGER latch with a nondeterministic reset reads back
as. Simulation needs a concrete value, so `undefined_reset_value` says which one it should use.

## Optimization

AIG optimization aims to reduce the number of AND gates and inverters in a circuit while maintaining its logical
functionality. Different optimization techniques target various aspects of the AIG structure.

### Basic Optimization Workflow

The typical optimization workflow involves:

1. Creating or loading an AIG
2. Applying one or more optimization algorithms
3. Verifying correctness through equivalence checking

```{code-cell} ipython3
from aigverse.io import read_aiger_into_aig

# Load the i10 benchmark circuit - a real-world example
aig = read_aiger_into_aig("examples/i10.aig")

# Print statistics about the loaded circuit
print(f"i10 benchmark:")
print(f"  I/O: {aig.num_pis}/{aig.num_pos}")
print(f"  AND gates: {aig.num_gates}")
```

### Resubstitution

Resubstitution identifies portions of logic that can be expressed using existing signals in the network. This technique
is particularly effective at identifying and eliminating redundant logic.

```{code-cell} ipython3
from aigverse.algorithms import aig_resubstitution

# Clone the AIG for comparison
aig_resub = aig.clone()

# Apply resubstitution
aig_resub = aig_resubstitution(aig_resub, window_size=12)

print(f"Original AND gates: {aig.num_gates}")
print(f"After resubstitution: {aig_resub.num_gates} AND gates")
print(f"Reduction: {aig.num_gates - aig_resub.num_gates} gates ({(aig.num_gates - aig_resub.num_gates) / aig.num_gates * 100:.2f}%)")
```

### Sum-of-Products Refactoring

SOP (Sum of Products) refactoring collapses parts of the AIG into truth tables, then re-synthesizes those portions using
Sum-of-Products representations. This can find more efficient implementations for complex logic functions.

```{code-cell} ipython3
from aigverse.algorithms import sop_refactoring

# Clone the AIG for comparison
aig_refactor = aig.clone()

# Apply SOP refactoring
aig_refactor = sop_refactoring(aig_refactor, use_reconvergence_cut=True)

print(f"Original AND gates: {aig.num_gates}")
print(f"After SOP refactoring: {aig_refactor.num_gates} AND gates")
print(f"Reduction: {aig.num_gates - aig_refactor.num_gates} gates ({(aig.num_gates - aig_refactor.num_gates) / aig.num_gates * 100:.2f}%)")
```

### Cut Rewriting

Cut rewriting identifies small subgraphs (cuts) in the AIG and replaces them with pre-computed optimal implementations
from a library. This technique leverages NPN-equivalence classes to find the best possible implementation for each cut.

```{code-cell} ipython3
from aigverse.algorithms import aig_cut_rewriting

# Clone the AIG for comparison
aig_rewrite = aig.clone()

# Apply cut rewriting
aig_rewrite = aig_cut_rewriting(aig_rewrite, cut_size=4)

print(f"Original AND gates: {aig.num_gates}")
print(f"After cut rewriting: {aig_rewrite.num_gates} AND gates")
print(f"Reduction: {aig.num_gates - aig_rewrite.num_gates} gates ({(aig.num_gates - aig_rewrite.num_gates) / aig.num_gates * 100:.2f}%)")
```

### Balancing

Balancing performs (E)SOP factoring to minimize the number of levels in the AIG.

```{code-cell} ipython3
from aigverse.algorithms import balancing
from aigverse.networks import DepthAig

# Clone the AIG for comparison
aig_balance = aig.clone()

# Apply balancing
aig_balance = balancing(aig_balance, rebalance_function="sop")

# Compute depth
original_depth = DepthAig(aig).num_levels
balanced_depth = DepthAig(aig_balance).num_levels

print(f"Original depth: {original_depth} levels")
print(f"After balancing: {balanced_depth} levels")
print(f"Reduction in depth: {original_depth - balanced_depth} levels ({(original_depth - balanced_depth) / original_depth * 100:.2f}%)")
```

### Combining Optimization Techniques

For best results, optimization techniques are typically applied in combination, often in multiple passes. The order of
application can significantly impact the final result.

```{code-cell} ipython3
# Apply optimization techniques in sequence
aig_opt = aig.clone()

# First pass
aig_opt = aig_resubstitution(aig_opt)
aig_opt = sop_refactoring(aig_opt)
aig_opt = aig_cut_rewriting(aig_opt)

# Second pass
aig_opt = aig_resubstitution(aig_opt)
aig_opt = sop_refactoring(aig_opt)

print(f"\nTotal optimization results:")
print(f"- Original: {aig.num_gates} AND gates")
print(f"- Optimized: {aig_opt.num_gates} AND gates")
print(f"- Total reduction: {aig.num_gates - aig_opt.num_gates} gates ({(aig.num_gates - aig_opt.num_gates) / aig.num_gates * 100:.2f}%)")
```

Some algorithms offer the `inplace=True` keyword argument for performance-sensitive pipelines of chained optimization.
Calling functions such as {py:func}`~aigverse.algorithms.aig_resubstitution` and
{py:func}`~aigverse.algorithms.sop_refactoring` with `inplace=True` mutates the passed network and returns `None`:

```{code-cell} ipython3
from aigverse.algorithms import cleanup_dangling

aig_fast = aig.clone()
aig_resubstitution(aig_fast, inplace=True)
sop_refactoring(aig_fast, inplace=True)

# Explicit cleanup step after in-place chaining
aig_fast = cleanup_dangling(aig_fast)
```

:::{note}
When choosing this route, users are responsible to call {py:func}`~aigverse.algorithms.cleanup_dangling` to obtain a
structurally valid AIG.
:::

## Equivalence Checking

Equivalence checking algorithms verify that two logic networks implement the same function, which is especially
important after performing optimizations.

```{code-cell} ipython3
from aigverse.algorithms import equivalence_checking

# Verify that our optimized circuit from the previous section maintains functional equivalence
are_equivalent = equivalence_checking(aig, aig_opt)
print(f"\nOriginal and optimized benchmark circuits are equivalent: {are_equivalent}")
print(f"This confirms our optimization preserved the circuit's functionality while reducing")
print(f"the gate count from {aig.num_gates} to {aig_opt.num_gates} AND gates.")
```
