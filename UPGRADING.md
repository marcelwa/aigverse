# Upgrade Guide

This document describes breaking changes and how to upgrade.

## 0.1.0

The `aigverse` library has been refactored into multiple extension modules to improve organization and scalability. If
you are upgrading from an older version, you will need to update your imports.

This version also includes an API rework for AIG optimization workflows.

### Key Changes

- **Networks**: `Aig`, `SequentialAig`, `NamedAig`, etc., `AigEdge`, `AigEdgeList`, `AigIndexList` and helper
  types are now in `aigverse.networks`.
- **Algorithms**: `balancing`, `equivalence_checking`, `simulate`, etc. are now in `aigverse.algorithms`.
- **IO**: Reading/Writing functions are now in `aigverse.io`.
- **Utils**: `TruthTable` and its free operation functions are now in `aigverse.utils`.

### Optimization and cleanup behavior

- `aig_resubstitution`, `sop_refactoring`, `aig_cut_rewriting`, and `balancing` now return a **new cleaned** `Aig` by
  default.
- `aig_resubstitution` and `sop_refactoring` support the `inplace` keyword argument (default `False`). With
  `inplace=True`, the input network is mutated, and the return value is `None`.
- `cleanup_dangling` moved from `Aig` member API to `aigverse.algorithms.cleanup_dangling`.

#### Before

```python
from aigverse.algorithms import aig_resubstitution

aig_resubstitution(aig)
```

#### After

```python
from aigverse.algorithms import aig_resubstitution, cleanup_dangling

# Return-new default
aig = aig_resubstitution(aig)

# Optional in-place mode for performance-oriented pipelines
aig_resubstitution(aig, inplace=True)
aig = cleanup_dangling(aig)
```

#### Performance note

If you intentionally chain `inplace=True` optimization calls for speed, you are responsible for calling
`cleanup_dangling` at appropriate checkpoints.

### Conversion API changes

- Removed free functions:
  - `to_edge_list(ntk)`
  - `to_index_list(ntk)`
  - `to_aig(il)`
- Added member methods:
  - `Aig.to_edge_list(...)`
  - `Aig.to_index_list()`
  - `AigIndexList.to_aig()`

#### Before

```python
from aigverse.networks import to_edge_list, to_index_list, to_aig

el = to_edge_list(aig)
il = to_index_list(aig)
aig2 = to_aig(il)
```

#### After

```python
el = aig.to_edge_list()
il = aig.to_index_list()
aig2 = il.to_aig()
```

### File I/O

#### Before

```python
from aigverse import Aig, read_aiger_into_aig

aig = read_aiger_into_aig("design.aig")
```

#### After

```python
from aigverse.networks import Aig
from aigverse.io import read_aiger_into_aig

aig = read_aiger_into_aig("design.aig")
```

### Pythonic properties

Network query methods are now **read-only properties** instead of callable methods.

| Before (method)           | After (property)        | Affected (base) types                  |
| ------------------------- | ----------------------- | -------------------------------------- |
| `aig.size()`              | `aig.size`              | `Aig`, `SequentialAig`, `AigIndexList` |
| `aig.num_pis()`           | `aig.num_pis`           | `Aig`, `SequentialAig`, `AigIndexList` |
| `aig.num_pos()`           | `aig.num_pos`           | `Aig`, `SequentialAig`, `AigIndexList` |
| `aig.num_gates()`         | `aig.num_gates`         | `Aig`, `SequentialAig`, `AigIndexList` |
| `aig.is_combinational()`  | `aig.is_combinational`  | `Aig`, `SequentialAig`                 |
| `depth_aig.num_levels()`  | `depth_aig.num_levels`  | `DepthAig`                             |
| `seq_aig.num_cis()`       | `seq_aig.num_cis`       | `SequentialAig`                        |
| `seq_aig.num_cos()`       | `seq_aig.num_cos`       | `SequentialAig`                        |
| `seq_aig.num_registers()` | `seq_aig.num_registers` | `SequentialAig`                        |

#### Before

```python
print(f"AIG has {aig.num_pis()} inputs and {aig.num_gates()} gates")
```

#### After

```python
print(f"AIG has {aig.num_pis} inputs and {aig.num_gates} gates")
```

### API policy

The package root intentionally does **not** re-export network classes or algorithm functions to lazily import extension
modules.
Use explicit modular imports (e.g. `aigverse.networks`, `aigverse.algorithms`, `aigverse.io`, `aigverse.utils`).
