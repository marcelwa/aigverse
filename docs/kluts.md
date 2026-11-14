---
file_format: mystnb
kernelspec:
  name: python3
mystnb:
  number_source_lines: true
---

# k-LUT Networks

{py:class}`~aigverse.networks.Klut` represents a combinational network whose gates are lookup tables (LUTs).
Each gate stores a Boolean truth table over its ordered fanins. Signals and node handles are Python integers;
the two constant nodes are `0` and `1`. Use `create_not(signal)` for inversion: Python's `~signal` complements the
integer handle and is not a network operation.

## Constructing and inspecting LUTs

```{code-cell} ipython3
from aigverse.networks import Klut
from aigverse.utils import TruthTable

ntk = Klut()
a = ntk.create_pi()
b = ntk.create_pi()

function = TruthTable(2)
function.create_from_binary_string("0010")
gate = ntk.create_node([a, b], function)
ntk.create_po(gate)

assert ntk.fanins(gate) == [a, b]
assert ntk.node_function(gate) == function
print(ntk)
```

The first fanin is truth-table variable 0, the least significant bit of an assignment index. The example's
`0010` table is true only when `a` is true and `b` is false. A table must have exactly one variable per fanin.
Zero fanins produce a constant; a gate supports at most 32 fanins. Truth tables require space exponential in
their variable count, so this native ceiling is not a practical recommendation for LUT size.

`create_and`, `create_nand`, `create_or`, `create_xor`, `create_lt`, `create_le`, `create_maj`, `create_ite`, and
`create_xor3` provide common functions. The n-ary AND, OR, and XOR helpers build trees of binary LUTs.
`create_buf` returns its input unchanged. Identical ordered fanins and truth tables reuse the existing gate.
`node_function` returns an independent truth table, so editing it does not change the network.

Use `nodes()`, `gates()`, `pis()`, `pos()`, and `fanins(node)` to inspect the network. `fanin_size(node)` counts
input edges; `fanout_size(node)` counts references including primary outputs. Handles must belong to the
network receiving the call: integers do not carry a network identity.

## Names, depth, fanouts, and copies

{py:class}`~aigverse.networks.NamedKlut` adds signal and output names. {py:class}`~aigverse.networks.DepthKlut`
adds LUT levels, and {py:class}`~aigverse.networks.FanoutKlut` adds gate fanout lists.

```{code-cell} ipython3
import copy

from aigverse.networks import DepthKlut, FanoutKlut, NamedKlut

named = NamedKlut()
x = named.create_pi("x")
y = named.create_pi("y")
named.create_po(named.create_and(x, y), "result")

depth = DepthKlut(named)
fanout = FanoutKlut(named)
assert depth.num_levels == 1
assert fanout.fanouts(x) == [named.po_at(0)]

independent = copy.deepcopy(named)
independent.create_po(independent.create_not(x), "inverted")
assert named.num_pos == 1
```

View constructors share network storage with their argument, following the AIG view convention. After changing
outputs through another shared object, call `update_levels()` to refresh depth metadata. Critical-path queries
recompute levels. Gate fanout lists exclude primary outputs; `update_fanout()` rebuilds them explicitly.
Depth and fanout constructors rebuild independent metadata, even when constructed from another view of the same type.
Depth refreshes visit output cones; dangling nodes have level zero after a refresh.
`NamedKlut(named)` copies the existing name maps: later name changes and names attached to new nodes are local
to each view, even though the nodes themselves are shared. Use `has_name` and `has_output_name` before querying
optional names; querying a missing name raises `IndexError`.

`DepthKlut.create_po()` recomputes levels, including logic that was previously dangling. For networks with many
outputs, build them in a plain `Klut` and construct a `DepthKlut` afterward to compute depth once. Repeated
critical-path queries also recompute metadata; they are intended for individual queries rather than whole-network scans.

Native depth computation and BLIF writing use recursive traversals. Very deep chains can overflow the native
stack and terminate the process. The limit depends on the platform and thread stack; there is no portable safe depth.

`clone()`, `copy.copy()`, and `copy.deepcopy()` create independent networks and retain the view type; named
copies preserve names. `Klut(view)` makes an independent plain network, discarding extra metadata.

## BLIF import and export

For AIG mapping, truth-table simulation, SAT equivalence checking, cleanup, and conversion back to AIGs,
see [LUT mapping and conversion](algorithms.md#lut-mapping-and-conversion).

{py:func}`~aigverse.io.read_blif` reads one complete flat combinational BLIF model ending with `.end`
and returns a `NamedKlut`.
{py:func}`~aigverse.io.write_blif` writes a `Klut` or one of its views.

```{code-cell} ipython3
from pathlib import Path
from tempfile import TemporaryDirectory

from aigverse.io import read_blif, write_blif

with TemporaryDirectory() as directory:
    path = Path(directory) / "network.blif"
    write_blif(named, path)
    restored = read_blif(path)

assert restored.get_name(restored.pi_at(0)) == "x"
assert restored.get_output_name(0) == "result"
```

BLIF preserves primary-input and primary-output names and order, including repeated output drivers. Internal
nodes are unnamed on import and their names are regenerated on export; the writer uses model name `top`.
The writer omits gates that do not reach an output and may add buffer LUTs for primary outputs. Round trips
preserve interface behavior, not gate counts or node identities.
The reader accepts `.model`, `.inputs`, `.outputs`,
`.names`, and `.end`, comments, line continuations, and on-set or off-set covers. It rejects malformed covers,
missing drivers, cycles, latches, hierarchy, and library cells with `RuntimeError`.

Nonempty BLIF covers expand into dense LUT truth tables whose space grows exponentially with fanin count.
A small input file can therefore require a large amount of memory.
BLIF cover generation and output size can also grow exponentially with LUT fanin count.

The writer rejects names containing ASCII whitespace, ASCII control characters, `#`, or backslash. Generated interface
names avoid explicit names. One interface name cannot refer to different drivers. `new_n0` and `new_n1` are reserved for the native
writer's constant nodes; an output may use one only when it references the corresponding constant.
