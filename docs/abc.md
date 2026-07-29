---
file_format: mystnb
kernelspec:
  name: python3
---

# ABC Integration

Beyond the built-in optimization algorithms, `aigverse` can hand a network to
[ABC](https://github.com/berkeley-abc/abc) and read the result back.

:::{important}
ABC runs as a separate process and is **not** bundled with `aigverse`. Any ABC build
works, whether from [berkeley-abc/abc](https://github.com/berkeley-abc/abc), a
distribution package, or one shipped with [Yosys](https://github.com/YosysHQ/yosys) or
the [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build). See
[Installation → ABC Integration](installation.md#abc-integration) for how to obtain one
and how to point `aigverse` at it.
:::

```{code-cell} ipython3
from aigverse import abc
from aigverse.generators import carry_lookahead_adder
from aigverse.algorithms import equivalence_checking

aig = carry_lookahead_adder(16)
optimized = abc.resyn2(aig)

print(f"{aig.num_gates} -> {optimized.num_gates} AND gates")
print(f"Equivalent: {equivalence_checking(aig, optimized)}")
```

Every script is available the same way; they differ in how hard they try:

```{code-cell} ipython3
for script in ("resyn", "resyn2", "resyn2rs", "compress2rs", "dc2"):
    result = getattr(abc, script)(aig)
    print(f"{script:12s} {aig.num_gates} -> {result.num_gates} AND gates")
```

## Named scripts

The canonical ABC scripts are available as functions: `resyn`, `resyn2`, `resyn3`,
`compress`, `compress2`, `resyn2rs`, `compress2rs`, and `dc2`.

Ordinarily these are _aliases_ defined in ABC's `abc.rc` resource file rather than
builtin commands, which makes them unreliable to call: they are unavailable on an
installation where no `abc.rc` is found, and they silently mean something else on one
where a user has customized that file. `aigverse` sidesteps both problems by shipping the
expansions itself and running ABC with `-s`, so a script means the same thing on every
machine. The exact expansion of each script is available in
{py:data}`~aigverse.abc.SCRIPTS`.

## Individual commands

The four commands the scripts are built from are exposed as well, so a schedule can be
composed from Python — useful when the sequence itself is what is being searched over:

```{code-cell} ipython3
result = aig
for step in (abc.balance, abc.rewrite, abc.refactor, abc.resub):
    result = step(result)

print(f"{aig.num_gates} -> {result.num_gates} AND gates")
```

Their options are exposed as keyword arguments rather than as ABC switches:
`abc.rewrite(aig, zero_cost=True)` or `abc.resub(aig, max_cut_size=12)`.

:::{note}
ABC's `-l` switch _toggles_ a default of "preserve the number of levels", so passing it
turns level preservation off. These wrappers therefore take `preserve_levels`, which
says what it means. The `compress` scripts are the `-l` variants of the `resyn` ones,
and hence the ones that trade depth for size.
:::

## Arbitrary commands

Any ABC command string can be run directly. The read and write steps are added
automatically, and whatever AIG is current when the script ends is what comes back:

```{code-cell} ipython3
result = abc.run_script(aig, "balance; rewrite -z; refactor", timeout=60)
print(f"{aig.num_gates} -> {result.num_gates} AND gates")
```

Set `use_init_file=True` to let ABC load your own `abc.rc`, which makes your personal
aliases available.

### The two network stores

ABC keeps two independent network stores, and a command only ever sees its own. By
default `aigverse` loads the network with `read_aiger` into the classic store, where the
commands without a `&` prefix operate — `balance`, `rewrite`, `refactor`, `resub`, and
therefore every named script above.

The `&`-prefixed commands of ABC9 work on a separate store, the GIA, which is empty in
that mode. Pass `gia=True` to load the network there directly:

```{code-cell} ipython3
result = abc.run_script(aig, "&syn2", gia=True)
print(f"{aig.num_gates} -> {result.num_gates} AND gates")
```

The two stores can also be bridged inside a single script with `&get` and `&put`, but
those do not carry I/O names across, whereas `gia=True` does.

### `&`-space wrappers

The `&` commands have wrappers of their own, which set `gia=True` for you:
`gia_balance` (`&b`), `gia_resub`, `gia_dc2`, `gia_syn2`, `gia_syn3`, `gia_syn4`, and
`gia_fraig`.

The `&`-space is not a mirror of the classic set — there is no `&rewrite` and no
`&refactor`, with `&dc2` standing in for both. What it offers instead is a different
strategy: these commands map to LUTs internally and unmap again, restructuring far more
aggressively than the classic commands, which only rewrite locally.

Whether that pays off is strongly design-dependent, and it is worth seeing that rather
than taking it on faith:

```{code-cell} ipython3
from aigverse.generators import ripple_carry_multiplier
from aigverse.networks import DepthAig

def report(label, ntk):
    print(f"  {label:10s} {ntk.num_gates:4d} gates  {DepthAig(ntk).num_levels:3d} levels")

for name, design in [("multiplier", ripple_carry_multiplier(4)), ("adder", aig)]:
    print(name)
    report("original", design)
    report("resyn2", abc.resyn2(design))
    report("gia_syn4", abc.gia_syn4(design))
```

On the multiplier, `gia_syn4` buys depth that `resyn2` cannot reach, and pays for it in
area. On the adder it does neither — it adds gates and leaves the depth alone, while
`resyn2` wins outright. Neither family dominates, so measure on your own designs instead
of assuming.

{py:func}`~aigverse.abc.gia_fraig` is the odd one out and worth knowing about: it is
combinational SAT sweeping, which merges nodes that are functionally equivalent but
structurally different. No amount of rewriting finds those, which makes it a useful pass
_between_ two structural scripts that each introduced their own duplicates.

## Type preservation and limitations

The returned network has the same type as the input: an
{py:class}`~aigverse.networks.Aig` yields an `Aig`, and a
{py:class}`~aigverse.networks.NamedAig` yields a `NamedAig` with its input and output
names carried through ABC.

:::{warning}
The bridge transfers AIGs and nothing else, so technology mapping and $k$-LUT mapping are
out of reach. A command such as `map` or `if -K 6` runs happily inside ABC, but the mapped
netlist it leaves behind cannot be written as AIGER, and the call raises rather than
quietly handing back something unmapped. Mapping support needs cell and $k$-LUT network
types in `aigverse` first.
:::

:::{warning}
{py:class}`~aigverse.networks.SequentialAig` is rejected with a `TypeError` rather than
being silently flattened into extra primary inputs and outputs. Sequential support
requires writing registers to AIGER and reading ABC's sequential output back, neither of
which is available yet.
:::

Each call starts an ABC process and transfers the network through temporary AIGER files,
which costs roughly 20 ms of overhead per call — negligible for batch work, but worth
keeping in mind in a tight optimization loop.

## A worked study

[`examples/abc_recipe_study.py`](https://github.com/marcelwa/aigverse/blob/main/examples/abc_recipe_study.py)
puts the bridge through a real experiment on the
[EPFL benchmark suite](https://github.com/lsils/benchmarks): it runs all 24 orderings of
the four atomic commands, compares the classic and `&`-space families on the area–depth
plane, and plots the result. It is a standalone [PEP 723](https://peps.python.org/pep-0723/)
script, so `uv run examples/abc_recipe_study.py` needs no setup beyond an ABC binary.

## Keeping the scripts in sync

The shipped expansions are checked against the `abc.rc` of the ABC the test suite runs
against, so a change to an alias upstream is caught when the pinned ABC revision is
bumped rather than showing up in your results. Point `AIGVERSE_ABC_RC` at an `abc.rc` to
run that check locally.

## Using your own aliases

{py:func}`~aigverse.abc.set_abc_rc` registers an ABC resource file that is loaded before
every command, which makes your own aliases available without giving up reproducibility:
the file you name is the only one ABC reads.

```python
from aigverse import abc

abc.set_abc_rc("/path/to/abc.rc")
result = abc.run_script(aig, "resyn2")  # now resolves as an alias
```

:::{note}
That snippet is not executed here, since it needs a resource file to point at.
:::

Set `AIGVERSE_ABC_RC` to configure the same thing from the environment, or pass `None` to
clear it.
