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

# Generators

The {py::mod}`~aigverse.generators` module provides generation helpers for reproducible random dataset creation and
structured arithmetic/control benchmarks.

## Random AIG Generation

Use {py:func}`~aigverse.generators.random_aig` for reproducible one-shot generation.

```{code-cell} ipython3
from aigverse.generators import random_aig

# One-shot random AIG with fixed size
single = random_aig(num_pis=4, num_gates=12, seed=42)
print(single.num_pis, single.num_gates)
```

## Python-Side Batching

Batching is intentionally kept on the Python side for flexibility. For fixed-size datasets, call
{py:func}`~aigverse.generators.random_aig` repeatedly with fixed `num_pis` and `num_gates`.

:::{note}
{py:func}`~aigverse.generators.random_aig` does not guarantee a fixed `num_pos` across seeds:
mockturtle's random topology can leave a different number of dangling nodes depending on the sampled structure.
As a result, repeated calls with identical `num_pis`/`num_gates` may still produce different output counts.
For ML training loops, use one of these mitigation strategies when you need a uniform label shape, you can filter
generated examples by `num_pos` or resample seeds until `num_pos` matches your target.
:::

```{code-cell} ipython3
from aigverse.generators import random_aig

batch_fixed = [random_aig(num_pis=4, num_gates=12, seed=1000 + i) for i in range(8)]
print(len(batch_fixed), batch_fixed[0].num_pis, batch_fixed[0].num_gates)
```

For size-diverse datasets, sample sizes in Python and pass them to
{py:func}`~aigverse.generators.random_aig`.

```{code-cell} ipython3
import random

from aigverse.generators import random_aig

rng = random.Random(7)

dataset = [
  random_aig(
    num_pis=rng.randint(3, 5),
    num_gates=rng.randint(10, 16),
    seed=2000 + i,
  )
  for i in range(8)
]

print([(aig.num_pis, aig.num_gates) for aig in dataset])
```

## Structured Benchmark Builders

Complete benchmark networks of arithmetic and control circuits of arbitrary bitwidth can be created via respective
high-level generator functions.

```{code-cell} ipython3
from aigverse.generators import ripple_carry_adder, carry_lookahead_adder

rca4 = ripple_carry_adder(bitwidth=4)
print(f"RCA: I/O: {rca4.num_pis}/{rca4.num_pos}, gates: {rca4.num_gates}")
cla4 = carry_lookahead_adder(bitwidth=4)
print(f"CLA: I/O: {cla4.num_pis}/{cla4.num_pos}, gates: {cla4.num_gates}")
```

## Control Generators

Control builders follow the same high-level model.

```{code-cell} ipython3
from aigverse.generators import binary_decoder, multiplexer

mux = multiplexer(bitwidth=4)
print(f"MUX: I/O: {mux.num_pis}/{mux.num_pos}, gates: {mux.num_gates}")

decoder = binary_decoder(num_select_bits=4)
print(f"Decoder: I/O: {decoder.num_pis}/{decoder.num_pos}, gates: {decoder.num_gates}")
```

Available structured builders include
{py:func}`~aigverse.generators.ripple_carry_adder`,
{py:func}`~aigverse.generators.carry_lookahead_adder`,
{py:func}`~aigverse.generators.sideways_sum_adder`,
{py:func}`~aigverse.generators.ripple_carry_multiplier`,
{py:func}`~aigverse.generators.multiplexer`, and
{py:func}`~aigverse.generators.binary_decoder`.
