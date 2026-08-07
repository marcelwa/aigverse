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

{py:func}`~aigverse.abc.orchestrate` is a fifth: instead of running rewriting,
refactoring and resubstitution one after another, it interleaves them and picks per node
which to apply — a whole schedule in a single command.

:::{note}
ABC's `-l` switch _toggles_ a default of "preserve the number of levels", so passing it
turns level preservation off. These wrappers therefore take `preserve_levels`, which
says what it means. The `compress` scripts are the `-l` variants of the `resyn` ones,
and hence the ones that trade depth for size.

Watch out for `orchestrate`, where ABC flips the convention: it enables zero-cost
replacements by _default_, unlike the standalone `rewrite` and `refactor`. The wrappers
paper over that with `zero_cost_rewrite` / `zero_cost_refactor`, which mean what they say
in both places.
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

### The `gia` namespace

The `&` commands have wrappers of their own in the `gia` namespace, which set `gia=True`
for you. The namespace mirrors ABC's own prefix, so the two spaces stay visibly distinct
at the call site:

```{code-cell} ipython3
print(f"abc.dc2:     {abc.dc2(aig).num_gates} gates")       # ABC's `dc2`
print(f"abc.gia.dc2: {abc.gia.dc2(aig).num_gates} gates")   # ABC's `&dc2`
```

It holds {py:func}`~aigverse.abc.gia.balance` (`&b`), {py:func}`~aigverse.abc.gia.resub`,
{py:func}`~aigverse.abc.gia.dc2`, {py:func}`~aigverse.abc.gia.syn2`,
{py:func}`~aigverse.abc.gia.syn3`, {py:func}`~aigverse.abc.gia.syn4` and
{py:func}`~aigverse.abc.gia.fraig`, plus the high-effort searches below,
{py:func}`~aigverse.abc.gia.cec`, {py:func}`~aigverse.abc.gia.stats`, and
{py:func}`~aigverse.abc.gia.run_script` for anything not wrapped.

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
    report("gia.syn4", abc.gia.syn4(design))
```

On the multiplier, `gia.syn4` buys depth that `resyn2` cannot reach, and pays for it in
area. On the adder it does neither — it adds gates and leaves the depth alone, while
`resyn2` wins outright. Neither family dominates, so measure on your own designs instead
of assuming.

{py:func}`~aigverse.abc.gia.fraig` is the odd one out and worth knowing about: it is
combinational SAT sweeping, which merges nodes that are functionally equivalent but
structurally different. No amount of rewriting finds those, which makes it a useful pass
_between_ two structural scripts that each introduced their own duplicates.

### High-effort search

Three more `&` commands are searches rather than passes, and are priced accordingly:

- {py:func}`~aigverse.abc.gia.deepsyn` repeatedly restructures with randomized parameters
  and keeps the smallest result. Different `seed` values can give different results, so it
  is worth running more than once.
- {py:func}`~aigverse.abc.gia.transduction` reasons about permissible functions per node
  and finds redundancy structural rewriting cannot. It is BDD-based, so its cost climbs
  steeply with size.
- {py:func}`~aigverse.abc.gia.transtoch` is stochastic transduction — transduction run
  repeatedly with randomized parameters. It is the most expensive thing here by a wide
  margin.

```{code-cell} ipython3
optimized = abc.gia.deepsyn(aig, timeout=2)
print(f"{aig.num_gates} -> {optimized.num_gates} AND gates")
```

There is one `timeout` throughout, and it always means "seconds you are willing to wait".
Where ABC accepts a budget of its own — as `&deepsyn` does — it is handed over, so ABC
stops on its own terms and returns the best result it found rather than being killed with
nothing to show. Where it does not, the process is stopped and an
{py:exc}`~aigverse.abc.AbcTimeoutError` is raised.

:::{warning}
The last two are realistically limited to small designs, and neither takes a budget of its
own, so a `timeout` there discards the work rather than harvesting it. Bound them by size
first and by `timeout` second.
:::

### Equivalence checking

{py:func}`~aigverse.abc.gia.cec` returns a verdict rather than a network, wrapping ABC's
`&cec`. It is a genuinely independent second opinion on
{py:func}`~aigverse.algorithms.equivalence_checking`: two different implementations, so a
disagreement means one of them has a bug worth finding.

```{code-cell} ipython3
optimized = abc.compress2rs(aig)
print(f"ABC says:      {abc.gia.cec(aig, optimized)}")
print(f"aigverse says: {equivalence_checking(aig, optimized)}")
```

ABC matches inputs by position rather than by name, so the two networks must have the
same interface.

`&cec` is incomplete under a resource limit, so there are four outcomes and not two, and
the result is a {py:class}`~aigverse.abc.CecStatus` rather than a `bool`:

|                  |                                                |
| ---------------- | ---------------------------------------------- |
| `EQUIVALENT`     | ABC proved the networks equal                  |
| `NOT_EQUIVALENT` | ABC found a counterexample                     |
| `UNDECIDED`      | ABC ran out of its own budget without deciding |
| `TIMEOUT`        | ABC did not finish within `timeout`            |

The enum deliberately refuses to be truth-tested, because `if abc.gia.cec(a, b):` would
read as "equivalent" while quietly also firing for `UNDECIDED` — and "not proven equal" is
not "proven different". Compare against a member instead:

```{code-cell} ipython3
if abc.gia.cec(aig, optimized) is abc.CecStatus.EQUIVALENT:
    print("proven equivalent")
```

## What ABC thinks of a network

{py:func}`~aigverse.abc.stats` and {py:func}`~aigverse.abc.gia.stats` run ABC's
`print_stats` and `&ps` and return an {py:class}`~aigverse.abc.AbcStats` instead of a line
of text:

```{code-cell} ipython3
print(abc.stats(aig))
print(abc.gia.stats(aig))
```

The two stores report slightly different things — `&ps` adds an average level and a memory
figure, and spells the register count `ff` where `print_stats` spells it `lat` — and both
keep the original line in `raw`.

:::{warning}
These are ABC's counts, not `aigverse`'s, and **they can differ for the very same
network**. ABC structurally hashes as it reads, so any structural redundancy the network
carried is gone before `print_stats` ever sees it:

```{code-cell} ipython3
print(f"aigverse says: {aig.num_gates} gates")
print(f"ABC says:      {abc.stats(aig).num_gates} gates")
```

Nothing was optimized in between — the gap is the strashing. Use `aig.num_gates` to
describe the network you hold and `stats()` to describe what ABC worked on, and do not
mix the two in one benchmark table.
:::

## Type preservation and limitations

The returned network has the same type as the input: an
{py:class}`~aigverse.networks.Aig` yields an `Aig`, a
{py:class}`~aigverse.networks.NamedAig` yields a `NamedAig` with its input and output
names carried through ABC, and a {py:class}`~aigverse.networks.SequentialAig` yields a
`SequentialAig` with its registers intact.

:::{warning}
The bridge transfers AIGs and nothing else, so technology mapping and $k$-LUT mapping are
out of reach. A command such as `map` or `if -K 6` runs happily inside ABC, but the mapped
netlist it leaves behind cannot be written as AIGER, and the call raises rather than
quietly handing back something unmapped. Mapping support needs cell and $k$-LUT network
types in `aigverse` first.
:::

:::{note}
{py:class}`~aigverse.networks.SequentialAig` round-trips as well, with its registers and
their reset values intact. The registers travel as AIGER latches; ABC switches to the
extended AIGER 1.9 encoding whenever one has a non-zero reset value, which is handled
transparently.

The type is checked before the base class, deliberately: it is registered as an `Aig`
subclass on the C++ side, so reading ABC's result back as a combinational network would
flatten the registers into extra primary input and output pairs.
:::

Each call starts an ABC process and transfers the network through temporary AIGER files,
which costs roughly 20 ms of overhead per call — negligible for batch work, but worth
keeping in mind in a tight optimization loop.

## When things go wrong

ABC exits with status 0 even for an unknown command or an unreadable file, and writes
everything to standard output — its standard error stays empty. Failure detection
therefore scans the output for known error markers and checks that a usable network came
back, rather than trusting the exit status:

```{code-cell} ipython3
try:
    abc.run_script(aig, "no_such_command")
except abc.AbcExecutionError as error:
    print(error)
```

Everything needed to reproduce the call is attached to the exception as `binary`,
`command`, and `output`, so a failure can be replayed by hand.

The hierarchy is small: {py:exc}`~aigverse.abc.AbcNotFoundError` when no usable executable
could be located, {py:exc}`~aigverse.abc.AbcTimeoutError` when ABC outlived its `timeout`,
and {py:exc}`~aigverse.abc.AbcExecutionError` for everything else ABC did wrong. All three
derive from {py:exc}`~aigverse.abc.AbcError`.

Options are validated in Python before ABC is started, so a value ABC would reject comes
back as a `ValueError` naming the keyword you wrote rather than as an ABC message:

```{code-cell} ipython3
for call in (
    lambda: abc.refactor(aig, max_support=16),
    lambda: abc.gia.deepsyn(aig, seed=101),
):
    try:
        call()
    except ValueError as error:
        print(error)
```

:::{note}
ABC is the authority on those ranges and `aigverse` pins no ABC version. The ranges ABC
prints in its own `-h` output are checked against the installed binary by the test suite,
so an upstream change is caught rather than guessed at. A few bounds ABC enforces without
documenting — `refactor` refuses a support above 15 while printing no range at all — are
recorded with the evidence for them.
:::

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
