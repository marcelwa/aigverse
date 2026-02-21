# Upgrade Guide

This document describes breaking changes and how to upgrade.

## 0.1.0

The `aigverse` library has been refactored into multiple extension modules to improve organization and scalability. If
you are upgrading from an older version, you will need to update your imports.

### Key Changes

- **Networks**: `Aig`, `SequentialAig`, `NamedAig`, etc. are now in `aigverse.networks`.
- **Algorithms**: `balancing`, `equivalence_checking`, `simulate`, etc. are now in `aigverse.algorithms`.
- **IO**: Reading/Writing functions are now in `aigverse.io`.
- **Utils**: `TruthTable`, `AigEdge`, `AigEdgeList`, `AigIndexList` and helper functions like `to_edge_list`,
  `to_index_list`, `to_aig` are now in `aigverse.utils`.
- **Cleanup**: `cleanup_dangling` is exposed as the method `aigverse.networks.Aig.cleanup_dangling`.

### Code Examples

#### Before

```python
from aigverse import Aig, read_aiger_into_aig, balancing, TruthTable

aig = read_aiger_into_aig("design.aig")
balancing(aig)
tt = TruthTable(3)
```

#### After

```python
from aigverse.networks import Aig
from aigverse.io import read_aiger_into_aig
from aigverse.algorithms import balancing
from aigverse.utils import TruthTable

aig = read_aiger_into_aig("design.aig")
balancing(aig)
tt = TruthTable(3)
```

### API policy

The package root intentionally does **not** re-export network classes or algorithm functions.
Use explicit modular imports (e.g. `aigverse.networks`, `aigverse.algorithms`, `aigverse.io`, `aigverse.utils`).
