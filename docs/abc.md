# ABC Integration

Beyond the built-in optimization algorithms, `aigverse` can hand a network to the
[ABC](https://github.com/berkeley-abc/abc) logic synthesis system and read the result
back. ABC runs as a separate process and is not bundled: any ABC build works, whether
from [berkeley-abc/abc](https://github.com/berkeley-abc/abc), a distribution package, or
one shipped with [Yosys](https://github.com/YosysHQ/yosys) or oss-cad-suite. See
[Installation](installation.md#abc-integration) for how to provide it.

:::{note}
The snippets in this section are not executed when the documentation is built, because
they require a local ABC installation.
:::

```python
from aigverse import abc
from aigverse.generators import ripple_carry_multiplier
from aigverse.algorithms import equivalence_checking

aig = ripple_carry_multiplier(8)

if abc.is_available():
    optimized = abc.resyn2(aig)
    print(f"{aig.num_gates} -> {optimized.num_gates} AND gates")
    assert equivalence_checking(aig, optimized)
```

## Named scripts

The canonical ABC scripts are available as functions: `resyn`, `resyn2`, `resyn3`,
`compress`, `compress2`, `resyn2rs`, `compress2rs`, and `dc2`.

These are ordinarily _aliases_ defined in ABC's `abc.rc` resource file rather than
builtin commands, so they fail on an installation where no `abc.rc` can be found, and
they silently change meaning if a user customizes that file. `aigverse` therefore ships
the expansions itself and runs ABC with `-s`, so results do not depend on the local
installation. The exact expansion of each script is available in
{py:data}`~aigverse.abc.SCRIPTS`.

## Arbitrary commands

Any ABC command string can be run directly. Commands must be ABC builtins, and the
`read_aiger`/`write_aiger` steps are added automatically:

```python
result = abc.run_script(aig, "balance; rewrite -z; refactor", timeout=60)
```

Set `use_init_file=True` to let ABC load your own `abc.rc`, which makes your personal
aliases available at the cost of reproducibility.

## Type preservation and limitations

The returned network has the same type as the input: an
{py:class}`~aigverse.networks.Aig` yields an `Aig`, and a
{py:class}`~aigverse.networks.NamedAig` yields a `NamedAig` with its input and output
names carried through ABC.

:::{warning}
{py:class}`~aigverse.networks.SequentialAig` is rejected with a `TypeError` rather than
being silently flattened into extra primary inputs and outputs. Sequential support
requires writing registers to AIGER and reading ABC's sequential output back, neither of
which is available yet.
:::

Each call starts an ABC process and transfers the network through temporary AIGER files,
which costs roughly 20 ms of overhead per call — negligible for batch work, but worth
keeping in mind in a tight optimization loop.

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

Set `AIGVERSE_ABC_RC` to configure the same thing from the environment, or pass `None` to
clear it.
