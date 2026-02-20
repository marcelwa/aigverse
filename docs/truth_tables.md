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

# Truth Tables

The aigverse library provides support for working with truth tables, which are a fundamental representation of Boolean functions. The {py:class}`~aigverse.TruthTable` class offers efficient manipulation and analysis of Boolean functions.

:::{note}
Truth tables provide a complete specification of a Boolean function by listing all possible input combinations and their corresponding outputs. They are particularly useful for small functions where exhaustive enumeration is feasible.
:::

## Creating Truth Tables

Truth tables can be created in several ways:

```{code-cell} ipython3
from aigverse.utils import TruthTable

# Initialize a truth table with 3 variables (2^3 = 8 entries)
tt = TruthTable(3)

# Create a truth table from a hex string (representing the Majority function)
tt.create_from_hex_string("e8")
print(f"Truth table from hex string: {tt.to_binary()}")

# Create a truth table for an AND function
tt_and = TruthTable(2)
tt_and.create_from_hex_string("8")
print(f"AND function: {tt_and.to_binary()}")

# Create a truth table for an OR function
tt_or = TruthTable(2)
tt_or.create_from_hex_string("e")
print(f"OR function: {tt_or.to_binary()}")
```

## Basic Manipulation

Truth tables provide various methods for bit manipulation:

```{code-cell} ipython3
# Create a truth table
tt = TruthTable(3)
tt.create_from_hex_string("e8")  # Majority function

# Get individual bits
print(f"Original truth table: {tt.to_binary()}")
print(f"Bit at position 0: {int(tt.get_bit(0))}")
print(f"Bit at position 7: {int(tt.get_bit(7))}")

# Flip bits
tt.flip_bit(0)
tt.flip_bit(7)
print(f"After flipping bits 0 and 7: {tt.to_binary()}")

# Clear the truth table
tt.clear()
print(f"After clearing: {tt.to_binary()}")

# Check if constant
print(f"Is constant 0? {tt.is_const0()}")
```

## Truth Table Properties

You can analyze various properties of truth tables:

```{code-cell} ipython3
# Create a truth table for XOR
tt_xor = TruthTable(2)
tt_xor.create_from_hex_string("6")  # XOR function
print(f"XOR function: {tt_xor.to_binary()}")

# Get number of variables and bits
print(f"Number of variables: {tt_xor.num_vars()}")
print(f"Number of bits: {tt_xor.num_bits()}")

# Check if the function is balanced (equal number of 0s and 1s)
num_ones = sum(int(tt_xor.get_bit(i)) for i in range(tt_xor.num_bits()))
is_balanced = num_ones == tt_xor.num_bits() // 2
print(f"Is balanced? {is_balanced}")
```

## Truth Table Simulation

The simulation of AIGs and other logic networks using truth tables is covered in the [Simulation section](algorithms.md#simulation) of the Algorithms documentation. This approach allows you to obtain the truth tables for outputs and internal nodes of a logic network.

## `pickle` Support

Truth tables support Python's `pickle` protocol, allowing you to serialize and deserialize them for persistent storage or use in data science workflows.

```{code-cell} ipython3
import pickle

# Create a truth table
tt = TruthTable(3)
tt.create_from_hex_string("d8")  # ITE function

# Pickle the truth table
with open("tt.pkl", "wb") as f:
    pickle.dump(tt, f)

# Unpickle the truth table
with open("tt.pkl", "rb") as f:
    unpickled_tt = pickle.load(f)

# Verify that the unpickled object is identical
print(f"Original:    {tt.to_binary()}")
print(f"Unpickled:   {unpickled_tt.to_binary()}")
print(f"Equivalent:  {tt == unpickled_tt}")
```

You can also pickle multiple truth tables at once by storing them in a list or tuple.
